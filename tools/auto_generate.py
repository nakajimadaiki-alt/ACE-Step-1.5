"""
.txt設定ファイルを読み込んで音楽生成→動画合成を自動実行する。

使い方:
    python tools/auto_generate.py songs/my_song.txt
    python tools/auto_generate.py songs/*.txt          # 複数一括処理

.txtフォーマット (songs/example.txt を参照):
    caption = chill lo-fi beats, piano
    duration = 180
    visual  = disc
    image   = ./assets/cover.png
    output  = my_video

    [lyrics]
    [Verse]
    歌詞をここに書く
    [/lyrics]
"""

import argparse
import json
import os
import sys
import time
from urllib.parse import unquote, urlparse, parse_qs

import requests

# --- パス設定 ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
APP_DIR = os.path.join(PROJECT_ROOT, "app")
for _p in (PROJECT_ROOT, APP_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from generate_bgm_video import generate_bgm_video  # noqa: E402

API_URL = os.getenv("ACESTEP_API_URL", "http://127.0.0.1:8001").strip()
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "bgm_output")


# ---------------------------------------------------------------------------
# .txt パーサー
# ---------------------------------------------------------------------------

def parse_txt(path: str) -> dict:
    """key = value 形式 + [lyrics]...[/lyrics] ブロックを解析する。

    ルール:
      - 行頭 # はコメント
      - [lyrics] ～ [/lyrics] の内容は "lyrics" キーに格納
      - それ以外は key = value (= より右が値、前後の空白を除去)
    """
    config = {}
    lyrics_lines = []
    in_lyrics = False

    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\n")
            stripped = line.strip()

            if stripped.lower() == "[lyrics]":
                in_lyrics = True
                continue
            if stripped.lower() == "[/lyrics]":
                in_lyrics = False
                continue
            if in_lyrics:
                lyrics_lines.append(line)
                continue

            if not stripped or stripped.startswith("#"):
                continue

            if "=" in stripped:
                key, _, val = stripped.partition("=")
                key = key.strip().lower().replace("-", "_")
                val = val.strip()
                # インラインコメントを除去 (#以降)
                if " #" in val:
                    val = val[: val.index(" #")].strip()
                config[key] = val

    if lyrics_lines:
        # 末尾の空行を落として結合
        while lyrics_lines and not lyrics_lines[-1].strip():
            lyrics_lines.pop()
        config["lyrics"] = "\n".join(lyrics_lines)

    # lyrics_file 指定があれば外部ファイルを読み込む
    if "lyrics_file" in config and "lyrics" not in config:
        lf = os.path.join(os.path.dirname(path), config["lyrics_file"])
        if os.path.exists(lf):
            with open(lf, encoding="utf-8") as f:
                config["lyrics"] = f.read()
        else:
            print(f"  [warn] lyrics_file not found: {lf}")

    return config


# ---------------------------------------------------------------------------
# ACE-Step 音楽生成
# ---------------------------------------------------------------------------

def _post_process_audio(audio_path: str, config: dict) -> str:
    """ローパスフィルター + ノーマライズで音をまろやかにする。

    pydub を使用。generate_lofi_mix.py と同じ処理。
    入力と同じディレクトリに _processed サフィックスで保存して返す。
    """
    try:
        from pydub import AudioSegment
    except ImportError:
        print("  [warn] pydub が未インストールのため post_process をスキップします。")
        print("         pip install pydub")
        return audio_path

    cutoff = int(config.get("lpf_cutoff", 10000))
    fade_in_ms  = int(float(config.get("fade_in",  1.0)) * 1000)
    fade_out_ms = int(float(config.get("fade_out", 5.0)) * 1000)

    print(f"  [post] LPF {cutoff}Hz + normalize + fade in {fade_in_ms}ms / out {fade_out_ms}ms")

    seg = AudioSegment.from_wav(audio_path)
    seg = seg.low_pass_filter(cutoff)
    seg = seg.normalize()
    if fade_in_ms  > 0: seg = seg.fade_in(fade_in_ms)
    if fade_out_ms > 0: seg = seg.fade_out(fade_out_ms)

    base, _ = os.path.splitext(audio_path)
    out_path = base + "_processed.wav"
    seg.export(out_path, format="wav")
    print(f"  [post] -> {out_path}")
    return out_path


def _apply_fade_only(audio_path: str, config: dict) -> str:
    """フェードイン・アウトだけを適用する（LPF・normalize なし）。"""
    try:
        from pydub import AudioSegment
    except ImportError:
        print("  [warn] pydub が未インストールのためフェードをスキップします。")
        return audio_path

    fade_in_ms  = int(float(config.get("fade_in",  0.0)) * 1000)
    fade_out_ms = int(float(config.get("fade_out", 5.0)) * 1000)
    print(f"  [fade] in {fade_in_ms}ms / out {fade_out_ms}ms")

    seg = AudioSegment.from_wav(audio_path)
    if fade_in_ms  > 0: seg = seg.fade_in(fade_in_ms)
    if fade_out_ms > 0: seg = seg.fade_out(fade_out_ms)

    base, _ = os.path.splitext(audio_path)
    out_path = base + "_fade.wav"
    seg.export(out_path, format="wav")
    return out_path


def _resolve_audio_path(file_value: str) -> str:
    """APIが返すファイル値を実際のローカルパスに変換する。

    APIは "/v1/audio?path=<URL encoded absolute path>" 形式を返すことがある。
    その場合は path パラメータをデコードして実パスを取り出す。
    通常の絶対パスはそのまま返す。
    """
    if file_value.startswith("/v1/audio"):
        parsed = urlparse(file_value)
        qs = parse_qs(parsed.query)
        paths = qs.get("path", [])
        if paths:
            return unquote(paths[0])
    return file_value

def _resolve_path(value: str, base_dir: str) -> str:
    """相対パスをbase_dirからの絶対パスに解決する。"""
    if os.path.isabs(value):
        return value
    return os.path.normpath(os.path.join(base_dir, value))


def generate_music(config: dict) -> str:
    """ACE-Step API で音楽を生成してローカルファイルパスを返す。"""
    caption = config.get("caption", "lofi hip hop, chill, calm piano")
    duration = int(config.get("duration", 120))
    seed = int(config.get("seed", -1))

    # steps: 多いほど高品質・低ノイズ。25だとざらつく。60前後推奨
    # guidance_scale: 高いほどプロンプトに忠実だが7超えると歪みやすい。3.5-5.0が自然
    steps = int(config.get("steps", 60))
    guidance = float(config.get("guidance_scale", 4.5))

    payload = {
        "prompt": caption,
        "duration": duration,
        "audio_format": "wav",
        "num_inference_steps": steps,
        "guidance_scale": guidance,
        "seed": seed,
    }

    lyrics = config.get("lyrics", "").strip()
    if lyrics:
        payload["lyrics"] = lyrics

    if "bpm" in config:
        payload["bpm"] = int(config["bpm"])

    if "keyscale" in config:
        payload["keyscale"] = config["keyscale"]

    print(f"  caption  : {caption[:80]}{'...' if len(caption) > 80 else ''}")
    print(f"  duration : {duration}s  seed: {seed}  steps: {steps}  guidance: {guidance}")
    if lyrics:
        print(f"  lyrics   : {len(lyrics)} chars")

    # 1. タスク投入
    resp = requests.post(f"{API_URL}/release_task", json=payload, timeout=30)
    resp.raise_for_status()
    task_id = resp.json()["data"]["task_id"]
    print(f"  task_id  : {task_id}")

    # 2. 完了待ち (ポーリング)
    spinner = ["|", "/", "-", "\\"]
    i = 0
    while True:
        time.sleep(3)
        q = requests.post(
            f"{API_URL}/query_result",
            json={"task_id_list": [task_id]},
            timeout=10,
        )
        data = q.json()["data"][0]
        status = data["status"]

        if status == 1:
            result = json.loads(data["result"])
            file_path = result[0]["file"]
            return _resolve_audio_path(file_path)
        elif status == -1:
            raise RuntimeError(f"Music generation failed: {data.get('error', 'unknown error')}")

        print(f"  {spinner[i % 4]} waiting... (status={status})", end="\r", flush=True)
        i += 1


# ---------------------------------------------------------------------------
# メイン処理
# ---------------------------------------------------------------------------

def run(txt_path: str) -> str:
    """1つの.txtを処理して出力パスを返す。"""
    print(f"\n{'='*60}")
    print(f"  {os.path.basename(txt_path)}")
    print(f"{'='*60}")

    base_dir = os.path.dirname(os.path.abspath(txt_path))
    config = parse_txt(txt_path)

    # 出力パス
    out_name = config.get("output") or os.path.splitext(os.path.basename(txt_path))[0]
    if not out_name.endswith(".mp4"):
        out_name += ".mp4"
    output_path = os.path.join(OUTPUT_DIR, out_name)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # --- Step 1: 音楽生成 ---
    print("\n[1/2] Generating music...")
    audio_path = generate_music(config)
    print(f"\n  -> {audio_path}")

    # --- 後処理: ローパスフィルター + ノーマライズ + フェード ---
    if config.get("post_process", "").lower() in ("true", "1", "yes"):
        audio_path = _post_process_audio(audio_path, config)
    elif "fade_in" in config or "fade_out" in config:
        # post_process なしでもフェードだけ適用する
        audio_path = _apply_fade_only(audio_path, config)

    # --- Step 2: 動画レンダリング ---
    print("\n[2/2] Rendering video...")
    visual = config.get("visual", "video").lower()
    video_path = None
    image_path = None
    style = "static"

    if visual == "video":
        raw = config.get("video", "")
        if raw:
            video_path = _resolve_path(raw, base_dir)
        else:
            # video_editor/dist/ から自動検索
            dist = os.path.join(PROJECT_ROOT, "video_editor", "dist")
            mp4s = sorted(
                [os.path.join(dist, f) for f in os.listdir(dist) if f.endswith(".mp4")],
                key=os.path.getmtime,
                reverse=True,
            ) if os.path.isdir(dist) else []
            if mp4s:
                video_path = mp4s[0]
                print(f"  auto-selected video: {os.path.basename(video_path)}")
            else:
                raise ValueError(
                    "visual=video だが動画ファイルが見つかりません。"
                    " video=<path> を .txt に追加するか、video_editor/dist/ に動画を置いてください。"
                )

    elif visual in ("disc", "static"):
        raw = config.get("image", "")
        if not raw:
            raise ValueError(f"visual={visual} には image=<path> が必要です。")
        image_path = _resolve_path(raw, base_dir)
        style = visual

    else:
        raise ValueError(f"visual の値が不正です: {visual!r}  (video / disc / static のいずれかを指定)")

    rotation_speed = 1.0 / float(config.get("rotation_period", 10))
    image_scale = float(config.get("image_scale", 1.0))
    image_offset_x = int(config.get("image_offset_x", 0))
    image_offset_y = int(config.get("image_offset_y", 0))

    generate_bgm_video(
        audio_path=audio_path,
        output_path=output_path,
        video_path=video_path,
        image_path=image_path,
        style=style,
        rotation_speed=rotation_speed,
        image_scale=image_scale,
        image_offset_x=image_offset_x,
        image_offset_y=image_offset_y,
    )

    print(f"\nDone! -> {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description=".txtを読んで音楽生成→動画合成を自動実行",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="例:\n  python tools/auto_generate.py songs/my_song.txt\n  python tools/auto_generate.py songs/*.txt",
    )
    parser.add_argument("files", nargs="+", metavar="<config.txt>", help=".txt設定ファイル")
    args = parser.parse_args()

    # API疎通確認
    try:
        r = requests.get(f"{API_URL}/health", timeout=5)
        if r.status_code != 200:
            raise ConnectionError
        print(f"API OK: {API_URL}")
    except Exception:
        print(f"ERROR: ACE-Step API に接続できません ({API_URL})")
        print("起動コマンド: .venv/Scripts/acestep-api.exe --host 127.0.0.1 --port 8001")
        sys.exit(1)

    results = []
    errors = []
    for path in args.files:
        try:
            out = run(path)
            results.append((path, out))
        except Exception as e:
            print(f"\nERROR: {path}: {e}")
            errors.append((path, str(e)))

    # サマリー
    print(f"\n{'='*60}")
    print(f"完了: {len(results)}件  失敗: {len(errors)}件")
    for _, out in results:
        print(f"  [OK] {out}")
    for p, e in errors:
        print(f"  [NG] {p}: {e}")


if __name__ == "__main__":
    main()
