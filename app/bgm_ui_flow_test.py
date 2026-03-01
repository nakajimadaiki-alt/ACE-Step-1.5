"""Tests for pure UI flow helpers used by `bgm_generator_ui.py`."""

import unittest

from others.bgm_ui_flow import (
    build_phase3_selection,
    has_phase1_selection,
    resolve_phase1_audio_path,
)


class BgmUiFlowTest(unittest.TestCase):
    """Behavior tests for phase selection helpers."""

    def test_phase1_upload_takes_precedence(self):
        """Uploaded audio path should override dropdown selection."""
        resolved = resolve_phase1_audio_path("library.mp3", "upload.mp3")
        self.assertEqual("upload.mp3", resolved)

    def test_phase1_selection_presence(self):
        """Selection detector returns true only when at least one path exists."""
        self.assertTrue(has_phase1_selection("library.mp3", None))
        self.assertFalse(has_phase1_selection(None, None))

    def test_build_phase3_selection_video_mode_success(self):
        """Video mode returns video path and summary when inputs are valid."""
        mode, video_path, image_path, summary = build_phase3_selection(
            mode="動画ループ (Video Loop)",
            video_dropdown_path="base.mp4",
            video_upload_path=None,
            image_upload_path=None,
            audio_path="song.mp3",
        )
        self.assertEqual("動画ループ (Video Loop)", mode)
        self.assertEqual("base.mp4", video_path)
        self.assertIsNone(image_path)
        self.assertIn("動画ループ", summary)

    def test_build_phase3_selection_image_mode_requires_image(self):
        """Image mode should fail when image upload is missing."""
        with self.assertRaises(ValueError):
            build_phase3_selection(
                mode="静止画 - 固定表示 (Static Image)",
                video_dropdown_path=None,
                video_upload_path=None,
                image_upload_path=None,
                audio_path="song.mp3",
            )


if __name__ == "__main__":
    unittest.main()
