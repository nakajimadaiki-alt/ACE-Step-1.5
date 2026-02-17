"""Tests for `generate_bgm_video` orchestration paths."""

import unittest
from unittest.mock import MagicMock, patch

from others.generate_bgm_video import generate_bgm_video


class GenerateBgmVideoTest(unittest.TestCase):
    """Unit tests for `generate_bgm_video` behavior."""

    @patch("others.generate_bgm_video.os.path.exists", return_value=True)
    @patch("others.generate_bgm_video.AudioFileClip")
    @patch("others.generate_bgm_video.build_static_image_clip")
    def test_static_image_mode_uses_static_builder(
        self,
        static_builder,
        audio_clip_cls,
        _exists_mock,
    ):
        """Static image mode should call static clip builder and write output."""
        audio_clip = MagicMock()
        audio_clip.duration = 5.0
        audio_clip_cls.return_value = audio_clip

        image_clip = MagicMock()
        image_clip.duration = 5.0
        final_with_audio = MagicMock()
        image_clip.with_audio.return_value = final_with_audio
        static_builder.return_value = image_clip

        generate_bgm_video(
            audio_path="audio.mp3",
            output_path="out.mp4",
            image_path="image.png",
            style="static",
            image_scale=1.2,
            image_offset_x=12,
            image_offset_y=-34,
        )

        static_builder.assert_called_once()
        final_with_audio.write_videofile.assert_called_once()

    @patch("others.generate_bgm_video.os.path.exists", return_value=True)
    @patch("others.generate_bgm_video.AudioFileClip")
    @patch("others.generate_bgm_video.build_disc_clip")
    def test_disc_mode_uses_disc_builder(
        self,
        disc_builder,
        audio_clip_cls,
        _exists_mock,
    ):
        """Disc mode should call disc clip builder and write output."""
        audio_clip = MagicMock()
        audio_clip.duration = 6.0
        audio_clip_cls.return_value = audio_clip

        disc_clip = MagicMock()
        disc_clip.duration = 6.0
        final_with_audio = MagicMock()
        disc_clip.with_audio.return_value = final_with_audio
        disc_builder.return_value = disc_clip

        generate_bgm_video(
            audio_path="audio.mp3",
            output_path="out.mp4",
            image_path="image.png",
            style="disc",
            rotation_speed=0.25,
            image_scale=1.5,
            image_offset_x=80,
            image_offset_y=-50,
        )

        disc_builder.assert_called_once()
        final_with_audio.write_videofile.assert_called_once()

    @patch("others.generate_bgm_video.os.path.exists", return_value=True)
    @patch("others.generate_bgm_video.AudioFileClip")
    @patch("others.generate_bgm_video.VideoFileClip")
    @patch("others.generate_bgm_video.Loop")
    def test_video_mode_still_uses_video_loop(
        self,
        loop_cls,
        video_clip_cls,
        audio_clip_cls,
        _exists_mock,
    ):
        """Non-target behavior: video loop path remains unchanged."""
        audio_clip = MagicMock()
        audio_clip.duration = 8.0
        audio_clip_cls.return_value = audio_clip

        video_clip = MagicMock()
        video_clip_cls.return_value = video_clip

        loop_effect = object()
        loop_cls.return_value = loop_effect

        looped = MagicMock()
        looped.duration = 8.0
        final_with_audio = MagicMock()
        looped.with_audio.return_value = final_with_audio
        video_clip.with_effects.return_value = looped

        generate_bgm_video(
            audio_path="audio.mp3",
            output_path="out.mp4",
            video_path="video.mp4",
        )

        video_clip.with_effects.assert_called_once_with([loop_effect])
        final_with_audio.write_videofile.assert_called_once()


if __name__ == "__main__":
    unittest.main()
