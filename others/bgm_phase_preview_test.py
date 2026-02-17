"""Tests for phase preview generation helpers."""

import unittest
from unittest.mock import MagicMock, patch

from others.bgm_phase_preview import create_visual_preview
from others.bgm_phase_preview import create_combined_preview


class BgmPhasePreviewTest(unittest.TestCase):
    """Behavior tests for Phase preview generation."""

    @patch("others.bgm_phase_preview.os.path.exists", return_value=True)
    def test_video_mode_returns_selected_video_path(self, _exists_mock):
        """Video mode should return selected video directly."""
        result = create_visual_preview(
            visual_mode="動画ループ (Video Loop)",
            video_dropdown_path="lib.mp4",
            video_upload_path="upload.mp4",
            image_path=None,
            rotation_period=10,
            image_scale=1.0,
            image_offset_x=0,
            image_offset_y=0,
            preview_dir="previews",
        )
        self.assertEqual("upload.mp4", result)

    @patch("others.bgm_phase_preview.os.path.exists", return_value=True)
    @patch("others.bgm_phase_preview.os.makedirs")
    @patch("others.bgm_phase_preview.build_disc_clip")
    def test_disc_mode_builds_preview_file(self, disc_builder, _makedirs, _exists_mock):
        """Disc mode should build clip and write short preview mp4."""
        clip = MagicMock()
        disc_builder.return_value = clip

        result = create_visual_preview(
            visual_mode="静止画 - 回転ディスク (Rotating Disk)",
            video_dropdown_path=None,
            video_upload_path=None,
            image_path="image.png",
            rotation_period=5,
            image_scale=1.2,
            image_offset_x=10,
            image_offset_y=-20,
            preview_dir="previews",
        )

        disc_builder.assert_called_once()
        clip.write_videofile.assert_called_once()
        self.assertTrue(result.endswith(".mp4"))

    def test_image_mode_requires_image_path(self):
        """Image mode without image should raise ValueError."""
        with self.assertRaises(ValueError):
            create_visual_preview(
                visual_mode="静止画 - 固定表示 (Static Image)",
                video_dropdown_path=None,
                video_upload_path=None,
                image_path=None,
                rotation_period=5,
                image_scale=1.0,
                image_offset_x=0,
                image_offset_y=0,
                preview_dir="previews",
            )

    @patch("others.bgm_phase_preview.os.path.exists", return_value=True)
    @patch("others.bgm_phase_preview.os.makedirs")
    def test_combined_preview_calls_generator_with_audio(
        self,
        _makedirs,
        _exists_mock,
    ):
        """Phase 3 combined preview should call generator with audio and style."""
        generator = MagicMock()
        result = create_combined_preview(
            audio_path="audio.wav",
            visual_mode="静止画 - 回転ディスク (Rotating Disk)",
            video_path=None,
            image_path="img.png",
            rotation_period=10,
            image_scale=1.1,
            image_offset_x=40,
            image_offset_y=-10,
            preview_dir="previews",
            generate_video_fn=generator,
        )
        generator.assert_called_once()
        kwargs = generator.call_args.kwargs
        self.assertEqual("audio.wav", kwargs["audio_path"])
        self.assertEqual("disc", kwargs["style"])
        self.assertTrue(result.endswith(".mp4"))


if __name__ == "__main__":
    unittest.main()
