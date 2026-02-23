import os
import time
import json
import requests
import sys
import random

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "others"))
from others.generate_bgm_video import generate_bgm_video

API_URL = "http://127.0.0.1:8001"
OUTPUT_DIR = "lofi_videos_output"
NUM_TRACKS = 5
TRACK_DURATION = 180
IMAGE_PATH = "image.png"

BPMS = list(range(70, 76))
KEYS = ["Cmaj7", "Dm7", "Am7", "Fmaj7", "Gmaj7", "Em7"]
INSTRUMENTS = ["Vintage Rhodes piano", "mellow jazz guitar", "warm sub bass"]
DRUM_ELEMENTS = ["soft attack kick", "snare velocity 70-85", "low-pass filtered hi-hats"]

# Constraints based on user request
SONIC_REFINEMENTS = (
    "STYLE: lofi hip hop. SWING: 10-15%. HUMANIZE: 5ms timing variation. "
    "HARMONY: Use 7th chords only. No bright major triads alone. 4-bar loop. "
    "MELODY: Max 5 notes per bar. Range: C3-C5. No leaps larger than a fifth. 30% rests minimum. "
    "DRUMS: No harsh transients. "
    "MIX: Low-pass at 10kHz. -3dB cut around 3kHz. Light tape saturation (8%). Vinyl noise at -35dB. "
    "PROHIBITED: No sharp plucks. No strong high-frequency spikes. No aggressive compression. No bright EDM-style clarity."
)

def get_random_prompt():
    bpm = random.choice(BPMS)
    key = random.choice(KEYS)
    insts = random.sample(INSTRUMENTS, 2)
    drums = random.sample(DRUM_ELEMENTS, 2)
    
    prompt = f"Lofi hip hop track, BPM {bpm}, Key {key}. Instruments: {' and '.join(insts)}. Drums: {' with '.join(drums)}. Constraints: {SONIC_REFINEMENTS}"
    return prompt, bpm, key

def wait_for_server():
    print("Waiting for API server to start...")
    for _ in range(30):
        try:
            r = requests.get(f"{API_URL}/health")
            if r.status_code == 200:
                print("API Server connected!")
                return True
        except:
            pass
        time.sleep(5)
    return False

def generate_track(index):
    prompt, bpm, key = get_random_prompt()
    print(f"[{index+1}/{NUM_TRACKS}] Generating: {prompt}...")

    payload = {
        "prompt": prompt,
        "duration": TRACK_DURATION,
        "audio_format": "wav",
        "num_inference_steps": 25,
        "guidance_scale": 7.0,
        "seed": -1,
    }

    try:
        req = requests.post(f"{API_URL}/release_task", json=payload)
        if req.status_code != 200:
            print(f"Error starting task: {req.text}")
            return None
        
        task_id = req.json()['data']['task_id']
        print(f"  Task started. ID: {task_id}")

        while True:
            time.sleep(2)
            query = requests.post(f"{API_URL}/query_result", json={"task_id_list": [task_id]})
            if query.status_code != 200:
                continue
            
            data = query.json()['data'][0]
            if data['status'] == 1:
                result_json = json.loads(data['result'])
                file_path = result_json[0]['file']
                print(f"  Generation complete: {file_path}")
                return file_path
    except Exception as e:
        print(f"Error during generation: {e}")
        return None

def main():
    if not wait_for_server():
        print("Error: Could not connect to API server.")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    for i in range(NUM_TRACKS):
        print(f"\n--- Starting Track {i+1} ---")
        wav_path = generate_track(i)
        if not wav_path or not os.path.exists(wav_path):
            print(f"Skipping video generation for track {i+1} due to missing audio.")
            continue
            
        output_mp4 = os.path.join(OUTPUT_DIR, f"lofi_video_{i+1}.mp4")
        print(f"Creating video: {output_mp4} using audio {wav_path} and image {IMAGE_PATH}")
        
        try:
            generate_bgm_video(
                audio_path=wav_path,
                output_path=output_mp4,
                video_path=None,
                image_path=IMAGE_PATH,
                style="static"
            )
            print(f"Track {i+1} video successfully created at: {output_mp4}")
        except Exception as e:
            print(f"Failed to create video for track {i+1}: {e}")

if __name__ == '__main__':
    main()
