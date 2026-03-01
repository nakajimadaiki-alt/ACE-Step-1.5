"""BGM動画生成ロジック。音声と映像素材を合成してMP4を出力する。"""

import argparse
import os

from moviepy import AudioFileClip, VideoFileClip

try:
    from moviepy.video.fx import Loop
except ImportError:
    import moviepy.video.fx as vfx

    Loop = vfx.Loop

try:
    from .bgm_disc_renderer import build_disc_clip, build_static_image_clip
except ImportError:
    from bgm_disc_renderer import build_disc_clip, build_static_image_clip


def generate_bgm_video(
    audio_path, 
    output_path, 
    video_path=None, 
    image_path=None, 
    style="static", 
    rotation_speed=0.2, 
    image_scale=1.0, 
    image_offset_x=0, 
    image_offset_y=0, 
    test_duration=None
):
    """音声と動画/画像を合成してBGM動画を書き出す。

    Args:
        audio_path: 入力音声ファイルパス。
        output_path: 出力動画ファイルパス。
        video_path: ループ再生する動画素材パス。
        image_path: 静止画素材パス。
        style: 画像モードの表示スタイル (`static`/`disc`)。
        rotation_speed: `disc`時の回転速度 (回転/秒)。
        image_scale: 画像拡大率。
        image_offset_x: 画像のXオフセット (px)。
        image_offset_y: 画像のYオフセット (px)。
        test_duration: テスト時に切り詰める秒数。

    Raises:
        FileNotFoundError: 入力ファイルが存在しない場合。
        ValueError: 動画/画像素材がどちらも未指定の場合。
    """
    
    if not audio_path or not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    # Load audio
    audio_clip = AudioFileClip(audio_path)
    
    if test_duration:
        print(f"Test mode: Truncating to {test_duration} seconds")
        audio_clip = audio_clip.subclipped(0, test_duration)

    audio_duration = audio_clip.duration
    print(f"Audio Duration: {audio_duration:.2f} seconds")

    final_clip = None

    if video_path:
        if not os.path.exists(video_path):
             raise FileNotFoundError(f"Video file not found: {video_path}")
        
        print(f"Using video: {video_path}")
        video_clip = VideoFileClip(video_path)
        
        # Loop the video to match audio duration
        final_clip = video_clip.with_effects([Loop(duration=audio_duration)])
        
    elif image_path:
        if not os.path.exists(image_path):
             raise FileNotFoundError(f"Image file not found: {image_path}")

        print(f"Using image: {image_path} with style: {style}, scale: {image_scale}, offset: ({image_offset_x}, {image_offset_y})")
        if style == "disc":
            final_clip = build_disc_clip(
                image_path=image_path,
                duration=audio_duration,
                rotation_speed=rotation_speed,
                image_scale=image_scale,
                offset_x=image_offset_x,
                offset_y=image_offset_y,
            )
        else:
            final_clip = build_static_image_clip(
                image_path=image_path,
                duration=audio_duration,
                image_scale=image_scale,
                offset_x=image_offset_x,
                offset_y=image_offset_y,
            )
        
    else:
        raise ValueError("Either --video or --image must be provided.")

    # Set audio
    if final_clip.duration is None:
         final_clip = final_clip.with_duration(audio_duration)
         
    final_clip = final_clip.with_audio(audio_clip)

    # Write output
    print(f"Writing video to: {output_path}")
    final_clip.write_videofile(
        output_path, 
        codec="libx264", 
        audio_codec="aac", 
        fps=24,
        threads=4,
        preset="medium"
    )
    print("Done!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a BGM video from audio and video/image.")
    parser.add_argument("--audio", required=True, help="Path to the audio file (wav, mp3, etc.)")
    parser.add_argument("--output", required=True, help="Path to the output video file (mp4)")
    parser.add_argument("--video", help="Path to a video file to loop")
    parser.add_argument("--image", help="Path to an image file")
    parser.add_argument("--style", choices=["static", "disc"], default="static", help="Visual style for image input: 'static' or 'disc'")
    parser.add_argument("--speed", type=float, default=0.1, help="Rotation speed (rotations per second) for image mode")
    parser.add_argument("--scale", type=float, default=1.0, help="Image scale factor")
    parser.add_argument("--offset-x", type=int, default=0, help="Image X offset (pixels)")
    parser.add_argument("--offset-y", type=int, default=0, help="Image Y offset (pixels)")
    parser.add_argument("--test-duration", type=float, help="Duration in seconds for testing purposes")

    args = parser.parse_args()

    generate_bgm_video(
        audio_path=args.audio,
        output_path=args.output,
        video_path=args.video,
        image_path=args.image,
        style=args.style,
        rotation_speed=args.speed,
        image_scale=args.scale,
        image_offset_x=args.offset_x,
        image_offset_y=args.offset_y,
        test_duration=args.test_duration
    )
