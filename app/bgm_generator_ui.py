"""BGM動画生成ツール — シングルページUI。

起動:
    set ACESTEP_API_URL=http://127.0.0.1:8001
    .venv\\Scripts\\python.exe others\\bgm_generator_ui.py
"""

import glob
import os
import re
import subprocess
import sys
import time
import traceback

import gradio as gr

try:
    from .bgm_cache import cleanup_previews, get_preview_stats
    from .bgm_health import health_badge_html
    from .bgm_phase_preview import create_combined_preview, create_visual_preview
    from .bgm_preview import render_image_adjustment_preview
    from .bgm_ui_flow import resolve_phase1_audio_path
except ImportError:
    from bgm_cache import cleanup_previews, get_preview_stats
    from bgm_health import health_badge_html
    from bgm_phase_preview import create_combined_preview, create_visual_preview
    from bgm_preview import render_image_adjustment_preview
    from bgm_ui_flow import resolve_phase1_audio_path

from generate_bgm_video import generate_bgm_video

# ---------------------------------------------------------------------------
# パス定数
# ---------------------------------------------------------------------------
current_dir = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(current_dir) if os.path.basename(current_dir) in ("others", "app") else current_dir

AUDIO_DIR   = os.path.join(PROJECT_ROOT, "lofi_mix_output")
VIDEO_DIR   = os.path.join(PROJECT_ROOT, "video_editor", "dist")
OUTPUT_DIR  = os.path.join(PROJECT_ROOT, "bgm_output")
PREVIEW_DIR = os.path.join(OUTPUT_DIR, "previews")
LOFI_SCRIPT = os.path.join(PROJECT_ROOT, "tools", "generate_lofi_mix.py")

for _p in (current_dir, PROJECT_ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

for _d in (OUTPUT_DIR, AUDIO_DIR, PREVIEW_DIR):
    os.makedirs(_d, exist_ok=True)


# ---------------------------------------------------------------------------
# ユーティリティ
# ---------------------------------------------------------------------------

def _list_files(directory, extensions):
    if not os.path.exists(directory):
        return []
    files = []
    for ext in extensions:
        files.extend(glob.glob(os.path.join(directory, f"*.{ext}")))
    return sorted(files, key=os.path.getmtime, reverse=True)


def get_audio_choices():
    return _list_files(AUDIO_DIR, ["wav", "mp3"])


def get_video_choices():
    return _list_files(VIDEO_DIR, ["mp4", "mov"])


def _choices_update(choices):
    return gr.update(choices=choices, value=choices[0] if choices else None)


def _fmt_size(path):
    try:
        b = os.path.getsize(path)
        return f"{b/1048576:.1f} MB" if b >= 1048576 else (f"{b/1024:.1f} KB" if b >= 1024 else f"{b} B")
    except Exception:
        return "?"


def _file_status(path, label):
    """ファイルの存在・サイズを検査してステータス行を返す。"""
    if not path:
        return f"❌ {label}: 未指定"
    if not os.path.exists(str(path)):
        return f"❌ {label}: ファイルが見つかりません → {path}"
    size = os.path.getsize(str(path))
    if size == 0:
        return f"❌ {label}: ファイルが空 (0 bytes) → {path}"
    return f"✅ {label}: {os.path.basename(str(path))} ({_fmt_size(path)})"


# ---------------------------------------------------------------------------
# 音楽生成ラッパー (ジェネレータ)
# ---------------------------------------------------------------------------

def _build_progress_md(total, completed, current_track, phase):
    if phase == "done":
        bar = "\u2588" * 20
        return f"**\u2705 完了!** {total}/{total} トラック\n\n`[{bar}]` 100%"
    if phase == "error":
        filled = int(20 * completed / max(total, 1))
        bar = "\u2588" * filled + "\u2591" * (20 - filled)
        return f"**\u274c エラー** {completed}/{total} トラック\n\n`[{bar}]`"
    if phase == "mixing":
        bar = "\u2588" * 18 + "\u2592" * 2
        return f"**\U0001F3B6 ミックス中...** {completed}/{total} トラック生成済み\n\n`[{bar}]` 90%"
    progress = min((completed + 0.5) / max(total, 1) if current_track else completed / max(total, 1), 0.89)
    pct = int(progress * 100)
    bar = "\u2588" * int(20 * progress) + "\u2592" * (20 - int(20 * progress))
    status = f"トラック {current_track}/{total} 生成中..." if current_track else "準備中..."
    return f"**\U0001F3B5 {status}**\n\n`[{bar}]` {pct}%"


def generate_lofi_wrapper(num_tracks, track_duration, custom_prompt):
    total = int(num_tracks)
    completed = 0
    current_track = 0
    try:
        before_choices = get_audio_choices()
        cmd = [
            sys.executable, "-u", LOFI_SCRIPT,
            "--num_tracks", str(total),
            "--track_duration", str(int(track_duration)),
            "--output_dir", AUDIO_DIR,
        ]
        if custom_prompt and custom_prompt.strip():
            cmd.extend(["--prompt", custom_prompt.strip()])

        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1,
        )
        log_lines = []
        phase = "generating"
        re_track    = re.compile(r"\[(\d+)/(\d+)\] Generating:")
        re_complete = re.compile(r"Generation complete:")
        re_mixing   = re.compile(r"Mixing Tracks|Mixing track")

        for line in process.stdout:
            stripped = line.rstrip()
            log_lines.append(stripped)
            m = re_track.search(stripped)
            if m:
                current_track = int(m.group(1))
                total = int(m.group(2))
            if re_complete.search(stripped):
                completed += 1
            if re_mixing.search(stripped):
                phase = "mixing"
            yield _build_progress_md(total, completed, current_track, phase), "\n".join(log_lines[-50:]), gr.update()

        process.wait()
        full_log = "\n".join(log_lines)

        if process.returncode != 0:
            yield _build_progress_md(total, completed, current_track, "error"), \
                  full_log + f"\n\n❌ スクリプト異常終了 (returncode={process.returncode})", gr.update()
            return

        choices = get_audio_choices()
        if len(choices) <= len(before_choices):
            yield _build_progress_md(total, completed, current_track, "error"), \
                  full_log + "\n\n❌ 音楽ファイルが生成されませんでした。\n" \
                             "ACE-Step API が起動しているか確認してください。\n" \
                             f"API URL: {os.getenv('ACESTEP_API_URL', 'http://127.0.0.1:8001')}", gr.update()
            return

        yield _build_progress_md(total, completed, current_track, "done"), \
              full_log + "\n\n✅ 音楽生成完了！", \
              gr.update(choices=choices, value=choices[0] if choices else None)

    except Exception as e:
        raise gr.Error(f"生成エラー: {e}\n{traceback.format_exc()}")


# ---------------------------------------------------------------------------
# 動画生成ラッパー
# ---------------------------------------------------------------------------

def generate_video(
    audio_dropdown, audio_upload,
    visual_mode,
    video_dropdown, video_upload2,
    image_upload2,
    rotation_period, image_scale, image_offset_x, image_offset_y,
    output_filename, test_mode,
):
    """入力を検証し動画を生成。出力パスとデバッグログを返す。"""
    debug = []
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    debug.append(f"=== 生成開始 {ts} ===")

    # --- パス解決 ---
    audio_path = resolve_phase1_audio_path(audio_dropdown, audio_upload)
    video_path = (video_upload2 or video_dropdown) if visual_mode == "動画ループ (Video Loop)" else None
    image_path = image_upload2 if "静止画" in visual_mode else None

    debug.append(f"[入力]")
    debug.append(f"  音楽      : {audio_path}")
    debug.append(f"  映像モード : {visual_mode}")
    debug.append(f"  動画      : {video_path}")
    debug.append(f"  画像      : {image_path}")
    debug.append(f"  スケール  : {image_scale}  オフセット: ({image_offset_x}, {image_offset_y})")
    debug.append(f"  回転周期  : {rotation_period}s  テスト: {test_mode}")

    # --- バリデーション ---
    debug.append("\n[バリデーション]")
    errors = []

    debug.append("  " + _file_status(audio_path, "音楽"))
    if not audio_path or not os.path.exists(str(audio_path or "")):
        errors.append("音楽ファイルが選択されていないか見つかりません。")
    elif os.path.getsize(str(audio_path)) == 0:
        errors.append(f"音楽ファイルが空です: {audio_path}")

    if visual_mode == "動画ループ (Video Loop)":
        debug.append("  " + _file_status(video_path, "動画"))
        if not video_path or not os.path.exists(str(video_path or "")):
            errors.append("動画ファイルが選択されていないか見つかりません。")
    elif "静止画" in visual_mode:
        debug.append("  " + _file_status(image_path, "画像"))
        if not image_path or not os.path.exists(str(image_path or "")):
            errors.append("画像ファイルがアップロードされていないか見つかりません。")

    if errors:
        debug.append("\n❌ 入力エラー:")
        for e in errors:
            debug.append(f"  • {e}")
        return None, gr.update(visible=False), "\n".join(debug)

    # --- 出力パス ---
    if not output_filename:
        output_filename = f"bgm_{int(time.time())}"
    if not output_filename.endswith(".mp4"):
        output_filename += ".mp4"
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    debug.append(f"\n[出力先] {output_path}")

    style = "disc" if "回転ディスク" in visual_mode else "static"
    rotation_speed = 1.0 / float(rotation_period) if rotation_period > 0 else 0.1
    test_duration = 20 if test_mode else None

    # --- 生成実行 ---
    debug.append("\n[実行中]")
    try:
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
            test_duration=test_duration,
        )
    except Exception as e:
        tb = traceback.format_exc()
        debug.append(f"❌ generate_bgm_video 例外: {e}")
        debug.append(f"\n--- トレースバック ---\n{tb}")
        return None, gr.update(visible=False), "\n".join(debug)

    # --- 後検証 ---
    if not os.path.exists(output_path):
        debug.append(f"❌ 出力ファイルが作成されませんでした: {output_path}")
        debug.append("  考えられる原因: MoviePy の書き込みエラー、ディスク容量不足")
        return None, gr.update(visible=False), "\n".join(debug)

    out_size = os.path.getsize(output_path)
    if out_size == 0:
        debug.append(f"❌ 出力ファイルが空です (0 bytes): {output_path}")
        return None, gr.update(visible=False), "\n".join(debug)

    debug.append(f"✅ 生成完了: {output_path} ({_fmt_size(output_path)})")
    return output_path, gr.update(visible=True), "\n".join(debug)


# ---------------------------------------------------------------------------
# プレビューラッパー
# ---------------------------------------------------------------------------

def _build_visual_preview(
    visual_mode, video_dropdown, video_upload2,
    image_upload2, rotation_period, image_scale, image_offset_x, image_offset_y,
):
    cleanup_previews(PREVIEW_DIR)
    try:
        return create_visual_preview(
            visual_mode=visual_mode,
            video_dropdown_path=video_dropdown,
            video_upload_path=video_upload2,
            image_path=image_upload2,
            rotation_period=rotation_period,
            image_scale=image_scale,
            image_offset_x=image_offset_x,
            image_offset_y=image_offset_y,
            preview_dir=PREVIEW_DIR,
        )
    except Exception as e:
        raise gr.Error(f"プレビューエラー: {e}\n{traceback.format_exc()}")


def _build_combined_preview(
    audio_dropdown, audio_upload,
    visual_mode, video_dropdown, video_upload2,
    image_upload2, rotation_period, image_scale, image_offset_x, image_offset_y,
):
    audio_path = resolve_phase1_audio_path(audio_dropdown, audio_upload)
    video_path = (video_upload2 or video_dropdown) if visual_mode == "動画ループ (Video Loop)" else None
    image_path = image_upload2 if "静止画" in visual_mode else None
    cleanup_previews(PREVIEW_DIR)
    try:
        return create_combined_preview(
            audio_path=audio_path,
            visual_mode=visual_mode,
            video_path=video_path,
            image_path=image_path,
            rotation_period=rotation_period,
            image_scale=image_scale,
            image_offset_x=image_offset_x,
            image_offset_y=image_offset_y,
            preview_dir=PREVIEW_DIR,
            preview_duration=8.0,
        )
    except Exception as e:
        raise gr.Error(f"プレビューエラー: {e}\n{traceback.format_exc()}")


def _update_image_preview(image_path, image_scale, image_offset_x, image_offset_y, visual_mode):
    return render_image_adjustment_preview(
        image_path=image_path,
        image_scale=image_scale,
        image_offset_x=image_offset_x,
        image_offset_y=image_offset_y,
        visual_mode=visual_mode,
    )


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------
css = """
.container { max-width: 1200px; margin: auto; }
.section-label { font-weight: bold; font-size: 1.05em; }
"""

# ---------------------------------------------------------------------------
# UI 構築
# ---------------------------------------------------------------------------
with gr.Blocks(title="BGM Generator") as app:
    gr.Markdown("# BGM 動画生成ツール")

    # API ヘルスバッジ
    with gr.Row():
        health_html = gr.HTML(value="<span>API確認中...</span>")
        refresh_health_btn = gr.Button("🔄 API状態更新", size="sm", scale=0)
    health_timer = gr.Timer(value=30)

    with gr.Row(elem_classes="container"):

        # ============================================================
        # 左カラム: 設定
        # ============================================================
        with gr.Column(scale=1, min_width=420):

            # --- 音楽セクション ---
            with gr.Accordion("🎵 音楽", open=True):
                with gr.Tabs():
                    with gr.Tab("ライブラリから選択"):
                        audio_choices = get_audio_choices()
                        audio_dropdown = gr.Dropdown(
                            label="作成済み音楽ファイル",
                            choices=audio_choices,
                            value=audio_choices[0] if audio_choices else None,
                            interactive=True,
                        )
                        refresh_audio_btn = gr.Button("🔄 リスト更新", size="sm")
                        audio_upload = gr.File(
                            label="または音楽ファイルをアップロード",
                            type="filepath",
                            file_types=["audio"],
                        )

                    with gr.Tab("新しく AI 生成する"):
                        gr.Markdown(
                            "設定を入力して「音楽を生成」を押してください。\n"
                            "ACE-Step APIサーバーが起動している必要があります。"
                        )
                        custom_prompt = gr.Textbox(
                            label="生成プロンプト (自由記述)",
                            placeholder="例: chill lo-fi beats, jazz piano, epic orchestral...",
                            info="空欄の場合は「Lofi Hip Hop」が自動生成されます。",
                        )
                        with gr.Row():
                            num_tracks    = gr.Slider(1, 20, value=3, step=1,  label="生成する曲数")
                            track_duration = gr.Slider(60, 300, value=120, step=10, label="1曲の長さ (秒)")
                        gen_lofi_btn     = gr.Button("✨ 音楽を生成する", variant="secondary")
                        gen_progress_md  = gr.Markdown(visible=True)
                        gen_log_output   = gr.Textbox(
                            label="生成ログ", lines=6, max_lines=12, interactive=False,
                        )

            # --- 映像セクション ---
            with gr.Accordion("📺 映像", open=True):
                visual_mode = gr.Radio(
                    choices=[
                        "動画ループ (Video Loop)",
                        "静止画 - 回転ディスク (Rotating Disk)",
                        "静止画 - 固定表示 (Static Image)",
                    ],
                    label="映像モード",
                    value="動画ループ (Video Loop)",
                )

                # 動画ループ
                with gr.Group(visible=True) as video_group:
                    video_choices = get_video_choices()
                    video_dropdown = gr.Dropdown(
                        label="動画ライブラリから選択",
                        choices=video_choices,
                        value=video_choices[0] if video_choices else None,
                    )
                    refresh_video_btn = gr.Button("🔄 リスト更新", size="sm")
                    video_upload2 = gr.File(
                        label="または動画をアップロード",
                        type="filepath",
                        file_types=["video"],
                    )

                # 静止画共通
                with gr.Group(visible=False) as image_group:
                    image_upload2 = gr.File(
                        label="画像をアップロード",
                        type="filepath",
                        file_types=["image"],
                    )
                    image_preview = gr.Image(
                        label="編集プレビュー",
                        type="numpy",
                        interactive=False,
                        height=280,
                    )
                    with gr.Group(visible=False) as disk_settings:
                        rotation_period = gr.Slider(
                            1, 60, value=10, step=1,
                            label="回転周期 (秒/回転)",
                            info="ディスクが1回転するのにかかる時間",
                        )
                    image_scale    = gr.Slider(0.1, 3.0, value=1.0, step=0.1, label="サイズ (倍率)")
                    with gr.Row():
                        image_offset_x = gr.Slider(-960, 960, value=0, step=10, label="位置 X (左右)")
                        image_offset_y = gr.Slider(-540, 540, value=0, step=10, label="位置 Y (上下)")

            # --- 出力設定 ---
            with gr.Accordion("⚙️ 出力設定", open=True):
                output_filename = gr.Textbox(
                    label="出力ファイル名",
                    value=f"bgm_video_{int(time.time())}",
                    placeholder="拡張子(.mp4)は自動付与",
                )
                test_mode = gr.Checkbox(
                    label="テストモード (冒頭20秒のみ生成)",
                    value=False,
                    info="動作確認を高速に行いたいときに使用",
                )

            generate_btn = gr.Button("🚀 動画を生成する", variant="primary", size="lg")

        # ============================================================
        # 右カラム: 出力 + デバッグ
        # ============================================================
        with gr.Column(scale=1, min_width=420):
            output_video_player = gr.Video(
                label="生成動画",
                interactive=False,
                visible=False,
            )

            with gr.Row():
                preview_visual_btn  = gr.Button("▶ 映像プレビュー (映像のみ)", variant="secondary")
                preview_combined_btn = gr.Button("▶ 統合プレビュー (音声+映像 8秒)", variant="secondary")
            preview_video = gr.Video(label="プレビュー", interactive=False)

            debug_log = gr.Textbox(
                label="デバッグログ / エラー詳細",
                lines=18,
                max_lines=40,
                interactive=False,
                placeholder="ここに生成ログとエラーの詳細が表示されます。",
            )

    # --- プレビューキャッシュ ---
    with gr.Accordion("プレビューキャッシュ", open=False):
        cache_info  = gr.Markdown("読み込み中...")
        cleanup_btn = gr.Button("🗑 キャッシュを整理する", size="sm")

    # =========================================================
    # イベントハンドラ
    # =========================================================

    # ヘルス
    app.load(health_badge_html, outputs=health_html)
    refresh_health_btn.click(health_badge_html, outputs=health_html)
    health_timer.tick(health_badge_html, outputs=health_html)

    # キャッシュ
    def _cache_info_text():
        stats = get_preview_stats(PREVIEW_DIR)
        return f"プレビューファイル: {stats['count']}個 ({stats['size_mb']} MB)"

    def _do_cleanup():
        deleted = cleanup_previews(PREVIEW_DIR, max_files=0)
        stats = get_preview_stats(PREVIEW_DIR)
        return f"{deleted}個削除。現在: {stats['count']}個 ({stats['size_mb']} MB)"

    app.load(_cache_info_text, outputs=cache_info)
    cleanup_btn.click(_do_cleanup, outputs=cache_info)

    # 音楽リスト更新
    refresh_audio_btn.click(
        lambda: _choices_update(get_audio_choices()),
        outputs=audio_dropdown,
    )

    # 音楽 AI 生成
    gen_lofi_btn.click(
        generate_lofi_wrapper,
        inputs=[num_tracks, track_duration, custom_prompt],
        outputs=[gen_progress_md, gen_log_output, audio_dropdown],
    )

    # 映像モード切替
    def _toggle_visual_mode(mode):
        is_video = (mode == "動画ループ (Video Loop)")
        is_image = not is_video
        is_disk  = (mode == "静止画 - 回転ディスク (Rotating Disk)")
        return (
            gr.update(visible=is_video),
            gr.update(visible=is_image),
            gr.update(visible=is_disk),
        )

    visual_mode.change(
        _toggle_visual_mode,
        inputs=[visual_mode],
        outputs=[video_group, image_group, disk_settings],
    )

    refresh_video_btn.click(
        lambda: _choices_update(get_video_choices()),
        outputs=video_dropdown,
    )

    # 画像プレビュー更新
    _img_preview_inputs = [image_upload2, image_scale, image_offset_x, image_offset_y, visual_mode]
    for _trigger in (image_upload2, image_scale, image_offset_x, image_offset_y, visual_mode):
        _trigger.change(_update_image_preview, inputs=_img_preview_inputs, outputs=image_preview)

    # 映像プレビュー
    preview_visual_btn.click(
        _build_visual_preview,
        inputs=[
            visual_mode, video_dropdown, video_upload2,
            image_upload2, rotation_period, image_scale, image_offset_x, image_offset_y,
        ],
        outputs=preview_video,
    )

    # 統合プレビュー (音声+映像)
    preview_combined_btn.click(
        _build_combined_preview,
        inputs=[
            audio_dropdown, audio_upload,
            visual_mode, video_dropdown, video_upload2,
            image_upload2, rotation_period, image_scale, image_offset_x, image_offset_y,
        ],
        outputs=preview_video,
    )

    # 動画生成
    generate_btn.click(
        generate_video,
        inputs=[
            audio_dropdown, audio_upload,
            visual_mode,
            video_dropdown, video_upload2,
            image_upload2,
            rotation_period, image_scale, image_offset_x, image_offset_y,
            output_filename, test_mode,
        ],
        outputs=[output_video_player, output_video_player, debug_log],
    )


if __name__ == "__main__":
    app.launch(css=css, inbrowser=True)
