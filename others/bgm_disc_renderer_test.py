"""Tests for disc/static clip rendering helpers."""

import unittest

import numpy as np

from others.bgm_disc_renderer import _object_position_from_pixel_offset, _render_disc_rgba


class BgmDiscRendererTest(unittest.TestCase):
    """Tests for disc rendering helper behavior."""

    def test_offset_to_object_position_center(self):
        """Zero offset should map to centered object position."""
        x_pct, y_pct = _object_position_from_pixel_offset(0, 0)
        self.assertEqual(50.0, x_pct)
        self.assertEqual(50.0, y_pct)

    def test_offset_to_object_position_clamped(self):
        """Large offset should be clamped to valid 0-100 range."""
        x_pct, y_pct = _object_position_from_pixel_offset(5000, -5000)
        self.assertEqual(100.0, x_pct)
        self.assertEqual(0.0, y_pct)

    def test_render_disc_returns_square_rgba(self):
        """Disc renderer should output an RGBA square image."""
        source = np.zeros((120, 80, 4), dtype=np.uint8)
        source[:, :, 0] = 255
        source[:, :, 3] = 255

        disc = _render_disc_rgba(
            image_rgba=source,
            disc_diameter=300,
            image_scale=1.0,
            object_x_pct=50.0,
            object_y_pct=50.0,
        )

        self.assertEqual((300, 300, 4), disc.shape)
        self.assertEqual(np.uint8, disc.dtype)
        # 円形マスクの角は透明であるべき。
        self.assertEqual(0, int(disc[0, 0, 3]))


if __name__ == "__main__":
    unittest.main()
