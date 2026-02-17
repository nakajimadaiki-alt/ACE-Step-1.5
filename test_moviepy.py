from moviepy import ColorClip, CompositeVideoClip, ImageClip
import os

# Create a dummy image
from PIL import Image
img = Image.new('RGB', (100, 100), color = 'red')
img.save('test_img.png')

try:
    print("Testing ColorClip...")
    # Test ColorClip
    bg_clip = ColorClip(size=(640, 480), color=(0, 0, 0), duration=5)
    print("ColorClip created.")

    print("Testing ImageClip with resize/position...")
    img_clip = ImageClip('test_img.png').with_duration(5)
    img_clip = img_clip.resized(0.5)
    
    # Calculate position like in the script
    w, h = img_clip.size
    pos_x = (640 - w) // 2 + 50
    pos_y = (480 - h) // 2 + 50
    img_clip = img_clip.with_position((pos_x, pos_y))
    
    print("Testing CompositeVideoClip...")
    final_clip = CompositeVideoClip([bg_clip, img_clip])
    print("CompositeVideoClip created.")
    
    # Test Audio
    print("Testing Audio (dummy)...")
    # Create empty audio array or just test import
    from moviepy import AudioArrayClip
    import numpy as np
    # 5 seconds of silence
    silence = AudioArrayClip(np.zeros((44100 * 5, 2)), fps=44100)
    print("AudioArrayClip created.")
    
    final_clip = final_clip.with_audio(silence)
    
    # Write a frame
    final_clip.save_frame("test_frame.png", t=1)
    print("Frame saved successfully.")

except Exception as e:
    print(f"Error occurred: {e}")
finally:
    if os.path.exists('test_img.png'):
        os.remove('test_img.png')
    if os.path.exists('test_frame.png'):
        os.remove('test_frame.png')
