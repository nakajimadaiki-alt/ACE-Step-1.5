import argparse
import os
from moviepy.editor import VideoFileClip, AudioFileClip, ImageClip, CompositeVideoClip, vfx
import numpy as np

def generate_bgm_video(audio_path, output_path, video_path=None, image_path=None, rotation_speed=0.2):
    """
    Generates a BGM video by combining audio with a video loop or a rotating image.

    Args:
        audio_path (str): Path to the audio file.
        output_path (str): Path to the output video file.
        video_path (str, optional): Path to the video file to loop.
        image_path (str, optional): Path to the image file to rotate.
        rotation_speed (float, optional): Rotation speed for the image (rotations per second?). 
                                          Actually, moviepy's rotate expects degrees or a function.
                                          We will implement a simple rotation function.
    """
    
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    # Load audio
    audio_clip = AudioFileClip(audio_path)
    audio_duration = audio_clip.duration
    print(f"Audio Duration: {audio_duration:.2f} seconds")

    final_clip = None

    if video_path:
        if not os.path.exists(video_path):
             raise FileNotFoundError(f"Video file not found: {video_path}")
        
        print(f"Using video: {video_path}")
        video_clip = VideoFileClip(video_path)
        
        # Loop the video to match audio duration
        final_clip = video_clip.fx(vfx.loop, duration=audio_duration)
        
    elif image_path:
        if not os.path.exists(image_path):
             raise FileNotFoundError(f"Image file not found: {image_path}")

        print(f"Using image: {image_path}")
        # Create an image clip
        # For rotation, we need to ensure the canvas is large enough or handle resizing.
        # Simple rotation:
        img_clip = ImageClip(image_path).set_duration(audio_duration)
        
        # Rotation function: t -> angle
        # speed * 360 * t
        def rotate_filter(t):
            return rotation_speed * 360 * t

        # Apply rotation
        # Note: 'rotate' might crop if not resized properly. 
        # For a circular image on a black background, it should be fine if centered.
        final_clip = img_clip.add_mask().rotate(rotate_filter, expand=False)
        
        # If we want a background, we can composite. 
        # For now, let's keep it simple: just the rotating image on black (default).
    else:
        raise ValueError("Either --video or --image must be provided.")

    # Set audio
    final_clip = final_clip.set_audio(audio_clip)

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
    parser.add_argument("--image", help="Path to an image file to rotate")
    parser.add_argument("--speed", type=float, default=0.1, help="Rotation speed (rotations per second) for image mode")

    args = parser.parse_args()

    generate_bgm_video(
        audio_path=args.audio,
        output_path=args.output,
        video_path=args.video,
        image_path=args.image,
        rotation_speed=args.speed
    )
