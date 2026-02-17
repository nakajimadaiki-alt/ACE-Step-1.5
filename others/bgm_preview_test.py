"""Tests for Phase 2 image adjustment preview renderer."""

import unittest
from pathlib import Path
import uuid

import numpy as np
from PIL import Image

from others.bgm_preview import render_image_adjustment_preview


class BgmPreviewTest(unittest.TestCase):
    """Behavior tests for preview rendering."""

    def _create_temp_image_path(self) -> Path:
        """ワークスペース配下にテスト用画像パスを作成する。"""
        root = Path(__file__).resolve().parent / ".tmp_preview_tests"
        root.mkdir(exist_ok=True)
        return root / f"sample_{uuid.uuid4().hex}.png"

    def test_returns_none_without_image_path(self):
        """Missing image path should return `None`."""
        preview = render_image_adjustment_preview(None, 1.0, 0, 0)
        self.assertIsNone(preview)

    def test_renders_canvas_with_expected_size(self):
        """Renderer should return an RGB image with default canvas size."""
        image_path = self._create_temp_image_path()
        try:
            Image.new("RGB", (100, 50), color=(255, 0, 0)).save(image_path)

            preview = render_image_adjustment_preview(str(image_path), 1.0, 0, 0)

            self.assertIsInstance(preview, np.ndarray)
            self.assertEqual((540, 960, 3), preview.shape)
            self.assertEqual(np.uint8, preview.dtype)
        finally:
            if image_path.exists():
                image_path.unlink()

    def test_offset_moves_visible_pixels(self):
        """Offset should move the drawn image area on the canvas."""
        image_path = self._create_temp_image_path()
        try:
            Image.new("RGB", (40, 40), color=(255, 255, 255)).save(image_path)

            centered = render_image_adjustment_preview(str(image_path), 1.0, 0, 0)
            shifted = render_image_adjustment_preview(str(image_path), 1.0, 120, 0)

            centered_non_black = np.argwhere(np.any(centered != 0, axis=2))
            shifted_non_black = np.argwhere(np.any(shifted != 0, axis=2))
            centered_x_mean = centered_non_black[:, 1].mean()
            shifted_x_mean = shifted_non_black[:, 1].mean()

            self.assertGreater(shifted_x_mean, centered_x_mean)
        finally:
            if image_path.exists():
                image_path.unlink()

    def test_disc_mode_preview_renders_circle_alpha_projection(self):
        """Disc mode should render a centered circular preview."""
        image_path = self._create_temp_image_path()
        try:
            Image.new("RGB", (80, 80), color=(0, 255, 0)).save(image_path)
            preview = render_image_adjustment_preview(
                image_path=str(image_path),
                image_scale=1.0,
                image_offset_x=0,
                image_offset_y=0,
                visual_mode="静止画 - 回転ディスク (Rotating Disk)",
            )
            self.assertEqual((540, 960, 3), preview.shape)
            # 左上は黒背景のまま（円盤外）。
            self.assertTrue(np.array_equal(preview[0, 0], np.array([0, 0, 0], dtype=np.uint8)))
        finally:
            if image_path.exists():
                image_path.unlink()


if __name__ == "__main__":
    unittest.main()
