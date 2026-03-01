"""Phase 2の画像編集プレビュー生成ヘルパー。"""

from __future__ import annotations

import os

import numpy as np
from PIL import Image
try:
    from .bgm_disc_renderer import _object_position_from_pixel_offset, _render_disc_rgba
except ImportError:
    from bgm_disc_renderer import _object_position_from_pixel_offset, _render_disc_rgba


def render_image_adjustment_preview(
    image_path: str | None,
    image_scale: float,
    image_offset_x: float,
    image_offset_y: float,
    visual_mode: str | None = None,
    canvas_size: tuple[int, int] = (960, 540),
) -> np.ndarray | None:
    """画像の拡大率と位置オフセットを反映したプレビュー画像を返す。

    Args:
        image_path: 入力画像のパス。
        image_scale: 画像拡大率。
        image_offset_x: 中央からのXオフセット。
        image_offset_y: 中央からのYオフセット。
        visual_mode: 現在の映像モード文字列。
        canvas_size: 出力プレビューキャンバスサイズ `(width, height)`。

    Returns:
        `numpy.ndarray`: RGBのプレビュー画像。入力不足時は `None`。
    """
    if not image_path or not isinstance(image_path, str):
        return None
    if not os.path.exists(image_path):
        return None

    canvas_width, canvas_height = canvas_size
    canvas = np.zeros((canvas_height, canvas_width, 3), dtype=np.uint8)

    with Image.open(image_path) as source:
        rgba = source.convert("RGBA")

    if visual_mode and "回転ディスク" in visual_mode:
        disc_diameter = min(int(canvas_height * 0.85), int(canvas_width * 0.5))
        object_x_pct, object_y_pct = _object_position_from_pixel_offset(image_offset_x, image_offset_y)
        disc = _render_disc_rgba(
            image_rgba=np.array(rgba),
            disc_diameter=disc_diameter,
            image_scale=image_scale,
            object_x_pct=object_x_pct,
            object_y_pct=object_y_pct,
        )
        rgba_canvas = Image.fromarray(
            np.dstack([canvas, np.full((canvas_height, canvas_width), 255, dtype=np.uint8)]),
            "RGBA",
        )
        disc_image = Image.fromarray(disc, "RGBA")
        left = (canvas_width - disc_diameter) // 2
        top = (canvas_height - disc_diameter) // 2
        rgba_canvas.paste(disc_image, (left, top), disc_image)
        return np.array(rgba_canvas.convert("RGB"))

    scale = max(float(image_scale), 0.05)
    target_width = max(int(rgba.width * scale), 1)
    target_height = max(int(rgba.height * scale), 1)
    resized = rgba.resize((target_width, target_height), Image.Resampling.LANCZOS)

    center_x = (canvas_width - target_width) // 2 + int(image_offset_x)
    center_y = (canvas_height - target_height) // 2 + int(image_offset_y)

    rgba_canvas = Image.fromarray(np.dstack([canvas, np.full((canvas_height, canvas_width), 255, dtype=np.uint8)]), "RGBA")
    rgba_canvas.paste(resized, (center_x, center_y), resized)
    rgb_preview = np.array(rgba_canvas.convert("RGB"))
    return rgb_preview
