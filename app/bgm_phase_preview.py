"""Phase 2/3用のビジュアルプレビュー生成ロジック。"""

from __future__ import annotations

import os
import time

try:
    from .bgm_disc_renderer import build_disc_clip, build_static_image_clip
except ImportError:
    from bgm_disc_renderer import build_disc_clip, build_static_image_clip


def _resolve_visual_paths(visual_mode: str, video_dropdown_path, video_upload_path, image_path):
    """モードに応じた実入力パスを返す。"""
    selected_video = video_upload_path if video_upload_path else video_dropdown_path
    if visual_mode == "動画ループ (Video Loop)":
        if not selected_video:
            raise ValueError("動画を選択してください。")
        return selected_video, None

    if not image_path:
        raise ValueError("画像をアップロードしてください。")
    return selected_video, image_path


def create_visual_preview(
    visual_mode: str,
    video_dropdown_path,
    video_upload_path,
    image_path,
    rotation_period: float,
    image_scale: float,
    image_offset_x: float,
    image_offset_y: float,
    preview_dir: str,
    preview_duration: float = 4.0,
):
    """映像設定の短尺プレビュー動画パスを返す。

    動画モードでは入力動画をそのまま返し、静止画モードでは
    画像設定を反映した短尺MP4を生成して返す。
    """
    video_path, selected_image = _resolve_visual_paths(
        visual_mode=visual_mode,
        video_dropdown_path=video_dropdown_path,
        video_upload_path=video_upload_path,
        image_path=image_path,
    )

    if visual_mode == "動画ループ (Video Loop)":
        if not os.path.exists(video_path):
            raise ValueError(f"動画ファイルが見つかりません: {video_path}")
        return video_path

    if not os.path.exists(selected_image):
        raise ValueError(f"画像ファイルが見つかりません: {selected_image}")

    os.makedirs(preview_dir, exist_ok=True)
    preview_name = f"visual_preview_{int(time.time() * 1000)}.mp4"
    preview_path = os.path.join(preview_dir, preview_name)
    rotation_speed = 1.0 / float(rotation_period) if float(rotation_period) > 0 else 0.1

    if "回転ディスク" in visual_mode:
        preview_clip = build_disc_clip(
            image_path=selected_image,
            duration=preview_duration,
            rotation_speed=rotation_speed,
            image_scale=image_scale,
            offset_x=image_offset_x,
            offset_y=image_offset_y,
        )
    else:
        preview_clip = build_static_image_clip(
            image_path=selected_image,
            duration=preview_duration,
            image_scale=image_scale,
            offset_x=image_offset_x,
            offset_y=image_offset_y,
        )

    preview_clip.write_videofile(
        preview_path,
        codec="libx264",
        fps=24,
        audio=False,
        threads=2,
        preset="ultrafast",
    )
    if hasattr(preview_clip, "close"):
        preview_clip.close()
    return preview_path


def create_combined_preview(
    audio_path,
    visual_mode: str,
    video_path,
    image_path,
    rotation_period: float,
    image_scale: float,
    image_offset_x: float,
    image_offset_y: float,
    preview_dir: str,
    preview_duration: float = 8.0,
    generate_video_fn=None,
):
    """Phase 3用の音声+映像プレビューを生成してパスを返す。"""
    if not audio_path:
        raise ValueError("音声ファイルを選択してください。")
    if not os.path.exists(audio_path):
        raise ValueError(f"音声ファイルが見つかりません: {audio_path}")

    selected_video, selected_image = _resolve_visual_paths(
        visual_mode=visual_mode,
        video_dropdown_path=video_path,
        video_upload_path=None,
        image_path=image_path,
    )

    os.makedirs(preview_dir, exist_ok=True)
    preview_name = f"combined_preview_{int(time.time() * 1000)}.mp4"
    preview_path = os.path.join(preview_dir, preview_name)
    rotation_speed = 1.0 / float(rotation_period) if float(rotation_period) > 0 else 0.1
    style = "disc" if "回転ディスク" in visual_mode else "static"

    if generate_video_fn is None:
        try:
            from .generate_bgm_video import generate_bgm_video as generate_video_fn
        except ImportError:
            from generate_bgm_video import generate_bgm_video as generate_video_fn

    generate_video_fn(
        audio_path=audio_path,
        output_path=preview_path,
        video_path=selected_video if visual_mode == "動画ループ (Video Loop)" else None,
        image_path=selected_image if visual_mode != "動画ループ (Video Loop)" else None,
        style=style,
        rotation_speed=rotation_speed,
        image_scale=image_scale,
        image_offset_x=image_offset_x,
        image_offset_y=image_offset_y,
        test_duration=preview_duration,
    )
    return preview_path
