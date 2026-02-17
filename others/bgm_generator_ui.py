import gradio as gr
import os
import glob
from generate_bgm_video import generate_bgm_video
import time
import subprocess
import traceback
import re
try:
    from .bgm_ui_flow import build_phase3_selection, has_phase1_selection, resolve_phase1_audio_path
    from .bgm_preview import render_image_adjustment_preview
    from .bgm_phase_preview import create_combined_preview, create_visual_preview
    from .bgm_health import health_badge_html
    from .bgm_cache import cleanup_previews, get_preview_stats
except ImportError:
    from bgm_ui_flow import build_phase3_selection, has_phase1_selection, resolve_phase1_audio_path
    from bgm_preview import render_image_adjustment_preview
    from bgm_phase_preview import create_combined_preview, create_visual_preview
    from bgm_health import health_badge_html
    from bgm_cache import cleanup_previews, get_preview_stats

# --- Constants & Config ---
# Paths are relative to the project root
current_dir = os.path.dirname(os.path.abspath(__file__))
if os.path.basename(current_dir) == "others":
    PROJECT_ROOT = os.path.dirname(current_dir)
else:
    PROJECT_ROOT = current_dir

AUDIO_DIR = os.path.join(PROJECT_ROOT, "lofi_mix_output")
VIDEO_DIR = os.path.join(PROJECT_ROOT, "video_editor", "dist")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "bgm_output")
PREVIEW_DIR = os.path.join(OUTPUT_DIR, "previews")
LOFI_SCRIPT = os.path.join(PROJECT_ROOT, "tools", "generate_lofi_mix.py")

import sys
if current_dir not in sys.path:
    sys.path.append(current_dir)
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

# Ensure directories exist
for d in [OUTPUT_DIR, AUDIO_DIR, PREVIEW_DIR]:
    if not os.path.exists(d):
        os.makedirs(d)

# --- Helpers ---
def list_files(directory, extensions):
    """ディレクトリ内の指定拡張子のファイルを更新日時順（新しい順）で取得"""
    if not os.path.exists(directory):
        return []
    files = []
    for ext in extensions:
        files.extend(glob.glob(os.path.join(directory, f"*.{ext}")))
    return sorted(files, key=os.path.getmtime, reverse=True)

def get_audio_choices():
    return list_files(AUDIO_DIR, ["wav", "mp3"])

def get_video_choices():
    return list_files(VIDEO_DIR, ["mp4", "mov"])


def _choices_update(choices):
    """Dropdownの選択肢更新を、先頭要素の自動選択つきで返す。"""
    return gr.update(choices=choices, value=choices[0] if choices else None)


def _phase1_next_button_state(dropdown_val, upload_val):
    """Phase 1の入力状態に応じた「次へ」ボタン状態を返す。"""
    return gr.update(interactive=has_phase1_selection(dropdown_val, upload_val))


def _update_image_preview(image_path, image_scale, image_offset_x, image_offset_y, visual_mode):
    """Phase 2の画像編集プレビューを更新する。"""
    return render_image_adjustment_preview(
        image_path=image_path,
        image_scale=image_scale,
        image_offset_x=image_offset_x,
        image_offset_y=image_offset_y,
        visual_mode=visual_mode,
    )


def _build_visual_preview(
    visual_mode,
    video_dropdown_path,
    video_upload_path,
    image_path,
    rotation_period,
    image_scale,
    image_offset_x,
    image_offset_y,
):
    """Phase 2/3で共通利用するプレビュー生成ラッパー。"""
    cleanup_previews(PREVIEW_DIR)
    try:
        return create_visual_preview(
            visual_mode=visual_mode,
            video_dropdown_path=video_dropdown_path,
            video_upload_path=video_upload_path,
            image_path=image_path,
            rotation_period=rotation_period,
            image_scale=image_scale,
            image_offset_x=image_offset_x,
            image_offset_y=image_offset_y,
            preview_dir=PREVIEW_DIR,
        )
    except ValueError as error:
        raise gr.Error(str(error))


def _build_phase3_combined_preview(
    audio_path,
    visual_mode,
    video_path,
    image_path,
    rotation_period,
    image_scale,
    image_offset_x,
    image_offset_y,
):
    """Phase 3の音声+映像プレビューを生成する。"""
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
    except ValueError as error:
        raise gr.Error(str(error))

# --- Wrappers ---
def _build_progress_md(total_tracks, completed, current_track, phase):
    """進捗状況をMarkdown文字列で返す。

    phase: "generating" | "mixing" | "done" | "error"
    """
    if phase == "done":
        bar = "\u2588" * 20
        return f"**\u2705 完了!** {total_tracks}/{total_tracks} トラック\n\n`[{bar}]` 100%"
    if phase == "error":
        filled = int(20 * completed / max(total_tracks, 1))
        bar = "\u2588" * filled + "\u2591" * (20 - filled)
        return f"**\u274c エラー** {completed}/{total_tracks} トラック\n\n`[{bar}]`"
    if phase == "mixing":
        bar = "\u2588" * 18 + "\u2592" * 2
        return f"**\ud83c\udfb6 ミックス中...** {completed}/{total_tracks} トラック生成済み\n\n`[{bar}]` 90%"

    # generating
    # 進捗 = (完了トラック数) / 全体、生成中トラックは半分カウント
    progress = (completed + 0.5) / max(total_tracks, 1) if current_track else completed / max(total_tracks, 1)
    progress = min(progress, 0.89)  # mixing前は最大89%
    pct = int(progress * 100)
    filled = int(20 * progress)
    bar = "\u2588" * filled + "\u2592" * (20 - filled)
    status = f"トラック {current_track}/{total_tracks} 生成中..." if current_track else "準備中..."
    return f"**\ud83c\udfb5 {status}**\n\n`[{bar}]` {pct}%"


def generate_lofi_wrapper(num_tracks, track_duration, custom_prompt):
    """Lofi生成スクリプトを実行 (ジェネレータ: ログ+進捗をリアルタイム表示)"""
    total = int(num_tracks)
    completed = 0
    current_track = 0

    try:
        before_choices = get_audio_choices()
        python_exe = os.sys.executable
        cmd = [
            python_exe, "-u", LOFI_SCRIPT,
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
        re_track = re.compile(r"\[(\d+)/(\d+)\] Generating:")
        re_complete = re.compile(r"Generation complete:")
        re_mixing = re.compile(r"Mixing Tracks|Mixing track")

        for line in process.stdout:
            stripped = line.rstrip()
            log_lines.append(stripped)
            log_text = "\n".join(log_lines[-50:])

            # パース: トラック生成開始
            m = re_track.search(stripped)
            if m:
                current_track = int(m.group(1))
                total = int(m.group(2))

            # パース: トラック生成完了
            if re_complete.search(stripped):
                completed += 1

            # パース: ミックス段階
            if re_mixing.search(stripped):
                phase = "mixing"

            progress_md = _build_progress_md(total, completed, current_track, phase)
            yield progress_md, log_text, gr.update()

        process.wait()
        full_log = "\n".join(log_lines)

        if process.returncode != 0:
            progress_md = _build_progress_md(total, completed, current_track, "error")
            yield progress_md, full_log + "\n\n[ERROR] 生成スクリプトが異常終了しました。", gr.update()
            return

        choices = get_audio_choices()
        if len(choices) <= len(before_choices):
            progress_md = _build_progress_md(total, completed, current_track, "error")
            yield (
                progress_md,
                full_log + "\n\n[WARNING] 音楽ファイルが生成されませんでした。"
                "\nACE-Step APIサーバー未起動の可能性があります。",
                gr.update(),
            )
            return

        progress_md = _build_progress_md(total, completed, current_track, "done")
        yield (
            progress_md,
            full_log + "\n\n[DONE] 音楽生成完了！",
            gr.update(choices=choices, value=choices[0] if choices else None),
        )

    except Exception as e:
        raise gr.Error(f"生成エラー: {str(e)}")


def final_generation_wrapper(
    audio_path, 
    visual_mode, # "動画ループ (Video Loop)" or "静止画 (ディスク)" or "静止画 (固定)"
    video_path, 
    image_path, 
    rotation_period, 
    image_scale,
    image_offset_x,
    image_offset_y,
    output_filename, 
    test_mode
):
    """最終設定を検証し、動画生成を実行して出力パスを返す。"""
    if not audio_path:
        raise gr.Error("Phase 1 エラー: 音声ファイルが選択されていません。")
    
    final_video_path = None
    style = "static"
    
    # Visual Mode Mapping
    # "動画ループ (Video Loop)" -> Video
    # "静止画 - 回転ディスク (Rotating Disk)" -> Image, style=disc
    # "静止画 - 固定表示 (Static Image)" -> Image, style=static
    
    if visual_mode == "動画ループ (Video Loop)":
        if not video_path:
             raise gr.Error("Phase 2 エラー: 動画ファイルが選択されていません。")
        final_video_path = video_path
    elif "静止画" in visual_mode:
        if not image_path:
             raise gr.Error("Phase 2 エラー: 画像ファイルがアップロードされていません。")
        final_video_path = None
        style = "disc" if "回転ディスク" in visual_mode else "static"
    
    # Output Path
    if not output_filename:
        output_filename = f"bgm_{int(time.time())}"
    if not output_filename.endswith(".mp4"):
        output_filename += ".mp4"
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    
    test_duration = 20 if test_mode else None

    # Calculate rotation speed (rotations/sec)
    # Speed = 1 / Period
    rotation_speed = 1.0 / float(rotation_period) if rotation_period > 0 else 0.1

    print(f"DEBUG: Calling generate_bgm_video with:")
    print(f"  audio={audio_path}")
    print(f"  output={output_path}")
    print(f"  video={final_video_path}")
    print(f"  image={image_path}")
    print(f"  style={style}")
    print(f"  scale={image_scale}")
    print(f"  offset=({image_offset_x}, {image_offset_y})")

    try:
        gr.Info("動画生成中...しばらくお待ちください。")
        generate_bgm_video(
            audio_path=audio_path,
            output_path=output_path,
            video_path=final_video_path,
            image_path=image_path if "静止画" in visual_mode else None,
            style=style,
            rotation_speed=rotation_speed,
            image_scale=image_scale,
            image_offset_x=image_offset_x,
            image_offset_y=image_offset_y,
            test_duration=test_duration
        )
        if not os.path.exists(output_path):
            raise gr.Error(f"出力ファイルが見つかりません: {output_path}")
        if os.path.getsize(output_path) <= 0:
            raise gr.Error(f"出力ファイルサイズが0です: {output_path}")
        gr.Info("生成完了！")
        return output_path, gr.update(visible=True)
    except Exception as e:
        print("VIDEO GENERATION FAILED:")
        print(traceback.format_exc())
        raise gr.Error(f"動画生成エラー: {str(e)}")

# --- UI Construction ---
css = """
.container { max-width: 900px; margin: auto; }
.phase-header { font-size: 1.2em; margin-bottom: 10px; font-weight: bold; border-bottom: 2px solid #eee; padding-bottom: 5px; }
.step-nav { margin-top: 20px; border-top: 1px solid #eee; padding-top: 10px; }
"""

with gr.Blocks(title="BGM Generator Wizard") as app:
    gr.Markdown("# 🧙‍♂️ 作業用BGM動画作成ウィザード")

    # Health Badge
    with gr.Row():
        health_html = gr.HTML(value="<span style='font-size:0.9em;'>Checking...</span>")
        refresh_health_btn = gr.Button("🔄 API状態更新", size="sm", scale=0)
    health_timer = gr.Timer(value=30)

    # State
    selected_audio = gr.State()
    selected_visual_mode = gr.State(value="動画ループ (Video Loop)")
    selected_video = gr.State()
    selected_image = gr.State()

    with gr.Column(elem_classes="container"):
        
        # --- PHASE 1: AUDIO ---
        with gr.Group(visible=True) as phase1:
            gr.Markdown("## 🎵 Phase 1: 音楽の準備", elem_classes="phase-header")
            
            with gr.Tabs():
                with gr.Tab("ライブラリから選択"):
                    audio_choices = get_audio_choices()
                    audio_dropdown = gr.Dropdown(
                        label="作成済み・既存の音楽ファイル", 
                        choices=audio_choices,
                        value=audio_choices[0] if audio_choices else None, 
                        interactive=True
                    )
                    refresh_audio_btn = gr.Button("🔄 リスト更新", size="sm")
                    audio_upload = gr.File(label="ファイルをアップロード", type="filepath", file_types=["audio"])

                with gr.Tab("新しく生成する (AI)"):
                    gr.Markdown("設定を入力して「音楽を生成」を押してください。")
                    custom_prompt = gr.Textbox(
                        label="生成プロンプト (自由記述)", 
                        placeholder="例: chill beats, jazz piano, epic orchestral, cyber punk...", 
                        info="好みのジャンルや雰囲気を入力してください。空欄の場合は「Lofi Hip Hop」が自動生成されます。"
                    )
                    with gr.Row():
                        num_tracks = gr.Slider(minimum=1, maximum=20, value=3, step=1, label="生成する曲数 (トラック数)")
                        track_duration = gr.Slider(minimum=60, maximum=300, value=120, step=10, label="1曲あたりの長さ (秒)")
                    
                    gen_lofi_btn = gr.Button("✨ 音楽を生成する", variant="secondary")
                    gen_progress_md = gr.Markdown(value="", visible=True)
                    gen_log_output = gr.Textbox(
                        label="生成ログ", lines=8, max_lines=15,
                        interactive=False,
                    )

            with gr.Row(elem_classes="step-nav"):
                to_phase2_btn = gr.Button(
                    "次へ: 映像の設定 ➡",
                    variant="primary",
                    interactive=bool(audio_choices),
                )

        # --- PHASE 2: VISUAL ---
        with gr.Group(visible=False) as phase2:
            gr.Markdown("## 📺 Phase 2: 映像の選択", elem_classes="phase-header")
            
            visual_mode = gr.Radio(
                ["動画ループ (Video Loop)", "静止画 - 回転ディスク (Rotating Disk)", "静止画 - 固定表示 (Static Image)"], 
                label="映像モード", 
                value="動画ループ (Video Loop)"
            )
            
            # Mode 1: Video Loop
            with gr.Group(visible=True) as video_group:
                gr.Markdown("### 動画ループ素材")
                video_choices = get_video_choices()
                video_dropdown = gr.Dropdown(
                    label="ライブラリから選択", 
                    choices=video_choices,
                    value=video_choices[0] if video_choices else None
                )
                refresh_video_btn = gr.Button("🔄 リスト更新", size="sm")
                video_upload2 = gr.File(label="または動画をアップロード", type="filepath", file_types=["video"])

            # Mode 2 & 3: Image
            with gr.Group(visible=False) as image_group:
                gr.Markdown("### 静止画素材")
                image_upload2 = gr.File(label="画像をアップロード", type="filepath", file_types=["image"])
                image_preview = gr.Image(
                    label="編集プレビュー（サイズ・位置を反映）",
                    type="numpy",
                    interactive=False,
                    height=320,
                )
                
                with gr.Group(visible=False) as disk_settings:
                    rotation_period = gr.Slider(
                        minimum=1, maximum=60, value=10, step=1, 
                        label="回転周期 (秒/回転)", 
                        info="ディスクが1回転するのにかかる時間 (秒)"
                    )
                
                with gr.Group(visible=False) as pos_settings:
                    image_scale = gr.Slider(minimum=0.1, maximum=3.0, value=1.0, step=0.1, label="サイズ (倍率)")
                    with gr.Row():
                        image_offset_x = gr.Slider(minimum=-960, maximum=960, value=0, step=10, label="位置 X (左右)")
                        image_offset_y = gr.Slider(minimum=-540, maximum=540, value=0, step=10, label="位置 Y (上下)")

            with gr.Row(elem_classes="step-nav"):
                back_to_phase1_btn = gr.Button("⬅ 戻る: 音楽")
                to_phase3_btn = gr.Button("次へ: 生成と確認 ➡", variant="primary")
            with gr.Row():
                phase2_preview_btn = gr.Button("▶ Phase 2 プレビュー更新", variant="secondary")
            phase2_video_preview = gr.Video(label="Phase 2 動画プレビュー", interactive=False)

        # --- PHASE 3: COMBINE ---
        with gr.Group(visible=False) as phase3:
            gr.Markdown("## 🎬 Phase 3: 生成・プレビュー", elem_classes="phase-header")
            
            gr.Markdown("以下の設定で動画を生成します。")
            summary_text = gr.Markdown("...")
            
            with gr.Row():
                output_filename = gr.Textbox(
                    label="出力ファイル名", 
                    value=f"bgm_video_{int(time.time())}", 
                    placeholder="拡張子(.mp4)は自動付与"
                )
                test_mode = gr.Checkbox(
                    label="テストモード (高速・冒頭20秒のみ)", 
                    value=False,
                    info="動作確認用に短時間で生成します"
                )
            
            generate_final_btn = gr.Button("🚀 動画を生成する", variant="primary", scale=2)
            
            output_video_player = gr.Video(label="プレビュー", interactive=False)
            with gr.Row():
                phase3_preview_btn = gr.Button("▶ Phase 3 事前プレビュー更新", variant="secondary")
            phase3_video_preview = gr.Video(label="Phase 3 事前プレビュー", interactive=False)
            
            with gr.Row(elem_classes="step-nav"):
                back_to_phase2_btn = gr.Button("⬅ 戻る: 映像")

        # --- Preview Cache ---
        with gr.Accordion("Preview Cache", open=False):
            cache_info = gr.Markdown("読み込み中...")
            cleanup_btn = gr.Button("🗑 キャッシュを整理する", size="sm")

    # --- LOGIC ---

    # Health Badge
    app.load(health_badge_html, outputs=health_html)
    refresh_health_btn.click(health_badge_html, outputs=health_html)
    health_timer.tick(health_badge_html, outputs=health_html)

    # Cache Info
    def _cache_info_text():
        stats = get_preview_stats(PREVIEW_DIR)
        return f"プレビューファイル: {stats['count']}個 ({stats['size_mb']} MB)"

    def _do_cleanup():
        deleted = cleanup_previews(PREVIEW_DIR, max_files=0)
        stats = get_preview_stats(PREVIEW_DIR)
        return f"{deleted}個のファイルを削除しました。現在: {stats['count']}個 ({stats['size_mb']} MB)"

    app.load(_cache_info_text, outputs=cache_info)
    cleanup_btn.click(_do_cleanup, outputs=cache_info)

    # Phase 1 Logic
    refresh_audio_btn.click(lambda: _choices_update(get_audio_choices()), outputs=audio_dropdown)
    refresh_audio_btn.click(_phase1_next_button_state, inputs=[audio_dropdown, audio_upload], outputs=to_phase2_btn)
    
    gen_lofi_btn.click(
        generate_lofi_wrapper,
        inputs=[num_tracks, track_duration, custom_prompt],
        outputs=[gen_progress_md, gen_log_output, audio_dropdown],
    )

    def go_to_phase2(dropdown_val, upload_val):
        """Phase 1の入力を検証し、Phase 2へ遷移する。"""
        path = resolve_phase1_audio_path(dropdown_val, upload_val)
        if not path:
             raise gr.Error("音楽ファイルを選択してください。")
        return path, gr.update(visible=False), gr.update(visible=True)

    to_phase2_btn.click(
        go_to_phase2,
        inputs=[audio_dropdown, audio_upload],
        outputs=[selected_audio, phase1, phase2]
    )
    audio_dropdown.change(_phase1_next_button_state, inputs=[audio_dropdown, audio_upload], outputs=to_phase2_btn)
    audio_upload.change(_phase1_next_button_state, inputs=[audio_dropdown, audio_upload], outputs=to_phase2_btn)

    # Phase 2 Logic
    def toggle_visual_mode(mode):
        is_video = mode == "動画ループ (Video Loop)"
        is_image = not is_video
        is_disk = mode == "静止画 - 回転ディスク (Rotating Disk)"
        return {
            video_group: gr.update(visible=is_video),
            image_group: gr.update(visible=is_image),
            disk_settings: gr.update(visible=is_disk),
            pos_settings: gr.update(visible=is_image)
        }
    
    visual_mode.change(toggle_visual_mode, inputs=[visual_mode], outputs=[video_group, image_group, disk_settings, pos_settings])
    
    refresh_video_btn.click(lambda: _choices_update(get_video_choices()), outputs=video_dropdown)
    image_upload2.change(
        _update_image_preview,
        inputs=[image_upload2, image_scale, image_offset_x, image_offset_y, visual_mode],
        outputs=image_preview,
    )
    image_scale.change(
        _update_image_preview,
        inputs=[image_upload2, image_scale, image_offset_x, image_offset_y, visual_mode],
        outputs=image_preview,
    )
    image_offset_x.change(
        _update_image_preview,
        inputs=[image_upload2, image_scale, image_offset_x, image_offset_y, visual_mode],
        outputs=image_preview,
    )
    image_offset_y.change(
        _update_image_preview,
        inputs=[image_upload2, image_scale, image_offset_x, image_offset_y, visual_mode],
        outputs=image_preview,
    )
    visual_mode.change(
        _update_image_preview,
        inputs=[image_upload2, image_scale, image_offset_x, image_offset_y, visual_mode],
        outputs=image_preview,
    )
    phase2_preview_btn.click(
        _build_visual_preview,
        inputs=[visual_mode, video_dropdown, video_upload2, image_upload2, rotation_period, image_scale, image_offset_x, image_offset_y],
        outputs=phase2_video_preview,
    )

    def go_to_phase3(mode, vid_drop, vid_up, img_up, audio_path):
        """Phase 2の入力を検証し、Phase 3の表示データを作る。"""
        try:
            selected_mode, selected_video_path, selected_image_path, summary = build_phase3_selection(
                mode=mode,
                video_dropdown_path=vid_drop,
                video_upload_path=vid_up,
                image_upload_path=img_up,
                audio_path=audio_path,
            )
        except ValueError as error:
            raise gr.Error(str(error))

        return (
            selected_mode,
            selected_video_path,
            selected_image_path,
            gr.update(visible=False),
            gr.update(visible=True),
            summary,
        )

    to_phase3_btn.click(
        go_to_phase3,
        inputs=[visual_mode, video_dropdown, video_upload2, image_upload2, selected_audio],
        outputs=[selected_visual_mode, selected_video, selected_image, phase2, phase3, summary_text]
    )

    back_to_phase1_btn.click(lambda: (gr.update(visible=True), gr.update(visible=False)), outputs=[phase1, phase2])
    back_to_phase2_btn.click(lambda: (gr.update(visible=True), gr.update(visible=False)), outputs=[phase2, phase3])

    # Phase 3 Logic
    generate_final_btn.click(
        final_generation_wrapper,
        inputs=[selected_audio, selected_visual_mode, selected_video, selected_image, rotation_period, image_scale, image_offset_x, image_offset_y, output_filename, test_mode],
        outputs=[output_video_player, output_video_player]
    )
    phase3_preview_btn.click(
        _build_phase3_combined_preview,
        inputs=[selected_audio, selected_visual_mode, selected_video, selected_image, rotation_period, image_scale, image_offset_x, image_offset_y],
        outputs=phase3_video_preview,
    )

if __name__ == "__main__":
    app.launch(css=css, inbrowser=True)
