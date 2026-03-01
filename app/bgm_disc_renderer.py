"""MoviePy向けの静止画/円盤クリップ生成ユーティリティ。"""

from __future__ import annotations

import numpy as np
from moviepy import ColorClip, CompositeVideoClip, ImageClip, VideoClip
from PIL import Image, ImageDraw

CANVAS_SIZE = (1920, 1080)


def _load_rgba(image_path: str) -> np.ndarray:
    """画像をRGBA配列で読み込む。"""
    with Image.open(image_path) as image:
        return np.array(image.convert("RGBA"))


def _object_position_from_pixel_offset(offset_x: float, offset_y: float) -> tuple[float, float]:
    """UIのpxオフセットを`object-position`相当の百分率へ変換する。"""
    x_pct = 50.0 + (float(offset_x) / (CANVAS_SIZE[0] / 2.0)) * 50.0
    y_pct = 50.0 + (float(offset_y) / (CANVAS_SIZE[1] / 2.0)) * 50.0
    return max(0.0, min(100.0, x_pct)), max(0.0, min(100.0, y_pct))


def _render_disc_rgba(
    image_rgba: np.ndarray,
    disc_diameter: int,
    image_scale: float,
    object_x_pct: float,
    object_y_pct: float,
) -> np.ndarray:
    """円盤テクスチャをRGBA配列として生成する。"""
    source = Image.fromarray(image_rgba, "RGBA")
    source_w, source_h = source.size

    base_scale = max(disc_diameter / source_w, disc_diameter / source_h)
    final_scale = max(0.05, float(image_scale)) * base_scale
    scaled_w = max(1, int(source_w * final_scale))
    scaled_h = max(1, int(source_h * final_scale))
    resized = source.resize((scaled_w, scaled_h), Image.Resampling.LANCZOS)

    container = Image.new("RGBA", (disc_diameter, disc_diameter), (0, 0, 0, 0))
    paste_x = int((disc_diameter - scaled_w) * (object_x_pct / 100.0))
    paste_y = int((disc_diameter - scaled_h) * (object_y_pct / 100.0))
    container.paste(resized, (paste_x, paste_y), resized)

    mask = Image.new("L", (disc_diameter, disc_diameter), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((0, 0, disc_diameter - 1, disc_diameter - 1), fill=255)
    container.putalpha(mask)

    # 円盤感を強める非対称ハイライトを追加し、回転が視認できるようにする。
    draw = ImageDraw.Draw(container, "RGBA")
    draw.ellipse(
        (0, 0, disc_diameter - 1, disc_diameter - 1),
        outline=(120, 120, 120, 160),
        width=max(2, disc_diameter // 320),
    )
    spindle_radius = max(6, disc_diameter // 55)
    cx = cy = disc_diameter // 2
    draw.ellipse(
        (cx - spindle_radius, cy - spindle_radius, cx + spindle_radius, cy + spindle_radius),
        fill=(34, 34, 34, 255),
        outline=(88, 88, 88, 255),
        width=max(2, disc_diameter // 500),
    )

    return np.array(container)


def _compose_on_black(image_clip, duration: float, position: tuple[int, int]):
    """前景を黒背景へ合成したクリップを返す。"""
    if hasattr(image_clip, "with_background_color"):
        return image_clip.with_background_color(
            size=CANVAS_SIZE,
            color=(0, 0, 0),
            pos=position,
        ).with_duration(duration)
    background = ColorClip(size=CANVAS_SIZE, color=(0, 0, 0), duration=duration)
    return CompositeVideoClip([background, image_clip.with_position(position)])


def build_static_image_clip(
    image_path: str,
    duration: float,
    image_scale: float,
    offset_x: float,
    offset_y: float,
):
    """固定画像モードのクリップを生成する。"""
    image_rgba = _load_rgba(image_path)
    image_clip = ImageClip(image_rgba).with_duration(duration)
    if image_scale != 1.0:
        image_clip = image_clip.resized(image_scale)
    image_w, image_h = image_clip.size
    pos_x = (CANVAS_SIZE[0] - image_w) // 2 + int(offset_x)
    pos_y = (CANVAS_SIZE[1] - image_h) // 2 + int(offset_y)
    return _compose_on_black(image_clip, duration, (pos_x, pos_y))


def build_disc_clip(
    image_path: str,
    duration: float,
    rotation_speed: float,
    image_scale: float,
    offset_x: float,
    offset_y: float,
):
    """円盤モードのクリップを生成する。

    MoviePy の Rotate エフェクトは RGBA クリップで回転中心がずれる場合があるため、
    PIL で直接回転させて VideoClip を構築する。
    """
    image_rgba = _load_rgba(image_path)
    disc_diameter = min(int(CANVAS_SIZE[1] * 0.85), int(CANVAS_SIZE[0] * 0.5))
    object_x_pct, object_y_pct = _object_position_from_pixel_offset(offset_x, offset_y)
    disc_rgba = _render_disc_rgba(
        image_rgba=image_rgba,
        disc_diameter=disc_diameter,
        image_scale=image_scale,
        object_x_pct=object_x_pct,
        object_y_pct=object_y_pct,
    )

    disc_pil = Image.fromarray(disc_rgba, "RGBA")
    pos_x = (CANVAS_SIZE[0] - disc_diameter) // 2
    pos_y = (CANVAS_SIZE[1] - disc_diameter) // 2
    canvas_size_wh = CANVAS_SIZE  # (width, height)

    def make_frame(t):
        # PIL.Image.rotate は center を基準に回転 (expand=False で元サイズ維持)
        # 正の角度 = 反時計回りなので負にして時計回りにする
        angle = -(float(rotation_speed) * 360.0 * t) % 360
        rotated = disc_pil.rotate(angle, resample=Image.Resampling.BILINEAR, expand=False)
        canvas = Image.new("RGB", canvas_size_wh, (0, 0, 0))
        canvas.paste(rotated, (pos_x, pos_y), rotated)
        return np.array(canvas)

    return VideoClip(make_frame, duration=duration)
