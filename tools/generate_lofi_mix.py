import os
import time
import json
import random
import requests
from pydub import AudioSegment
from datetime import datetime

# ==========================================
# User Configuration (Lofi Architecture)
# ==========================================
API_URL = "http://127.0.0.1:7860"
OUTPUT_DIR = "lofi_mix_output"

# Generator Settings
NUM_TRACKS = 15  # Total tracks to generate (Target: 15 tracks)
TRACK_DURATION = 240 # Duration per track in seconds (4 mins)
CROSSFADE_DURATION = 5000 # 5 seconds in milliseconds

# 1. Music Architecture
BPMS = list(range(65, 86)) # 65-85 BPM
KEYS = ["Cmaj7", "Dm7", "Am7", "Fmaj7", "G7", "Em7"] # Jazzy/Lofi keys

# 2. Rhythm & Sound Design (Text Prompts)
# Refined based on 改善書: Focus on "softening" and "rounding" the sound
DRUM_ELEMENTS = ["muted kick", "soft snare", "gentle hi-hats", "lofi boom bap"]
INSTRUMENTS = ["Vintage Rhodes piano", "mellow jazz guitar", "warm sub bass", "dreamy synth pad"]
AMBIENCE = ["soft vinyl crackle", "distant rain", "gentle tape hiss", "analog warmth"]
VIBE = ["understated", "mellow", "rounded transients", "warm analog", "soft aesthetic"]

# Improvements from 改善書: Specific frequency and transient management
SONIC_REFINEMENTS = (
    "Avoid sharp transients. High frequencies should be rolled off around 10kHz. "
    "Muffled and warm sound, reduce energy in 2-5kHz range. "
    "Apply deep tape saturation (8%), very high spectral centroid around 1000Hz (warmth)."
)

def get_random_prompt():
    bpm = random.choice(BPMS)
    key = random.choice(KEYS)
    elements = random.sample(DRUM_ELEMENTS, 2)
    insts = random.sample(INSTRUMENTS, 2)
    amb = random.choice(AMBIENCE)
    vibe = random.choice(VIBE)
    
    # Constructing the prompt with the "softening" instructions
    prompt = (
        f"Lofi hip hop track, BPM {bpm}, Key {key}, {vibe} vibe. "
        f"Instruments: {' and '.join(insts)}. "
        f"Drums: {' with '.join(elements)}. "
        f"Texture: {amb}. "
        f"{SONIC_REFINEMENTS}"
    )
    return prompt, bpm, key

def check_server():
    try:
        response = requests.get(f"{API_URL}/health")
        return response.status_code == 200
    except:
        return False

def generate_track(index):
    prompt, bpm, key = get_random_prompt()
    print(f"[{index+1}/{NUM_TRACKS}] Generating: {prompt}...")

    payload = {
        "prompt": prompt,
        "duration": TRACK_DURATION,
        "audio_format": "wav",
        "num_inference_steps": 25, # Slightly higher for better quality
        "guidance_scale": 7.0,
        "seed": -1,
    }

    try:
        # 1. Release Task
        req = requests.post(f"{API_URL}/release_task", json=payload)
        if req.status_code != 200:
            print(f"Error starting task: {req.text}")
            return None
        
        task_id = req.json()['data']['task_id']
        print(f"  Task started. ID: {task_id}")

        # 2. Poll for Result
        while True:
            time.sleep(2)
            query = requests.post(f"{API_URL}/query_result", json={"task_id_list": [task_id]})
            if query.status_code != 200:
                continue
            
            data = query.json()['data'][0]
            if data['status'] == 1: # Succeeded
                result_json = json.loads(data['result'])
                file_path = result_json[0]['file']
                print(f"  Generation complete: {file_path}")
                return file_path
                
    except Exception as e:
        print(f"Error during generation: {e}")
        return None

def main():
    if not check_server():
        print("Error: ACE-Step server is not running or not accessible at http://127.0.0.1:7860")
        print("Please start it with: uv run acestep --enable-api ...")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    generated_files = []

    print("=== Starting Lofi Mix Generator (Refined Version) ===")
    
    # 1. Generate Tracks
    for i in range(NUM_TRACKS):
        file_path = generate_track(i)
        if file_path and os.path.exists(file_path):
            generated_files.append(file_path)
        else:
            print(f"Skipping track {i+1} due to error.")

    if not generated_files:
        print("No tracks generated. Exiting.")
        return

    # 2. Mix Tracks
    print("\n=== Mixing Tracks & Applying Refinements ===")
    try:
        mix = AudioSegment.from_wav(generated_files[0])
        # Apply gentle low pass filter to ensure "rounded" sound (改善書 suggestion)
        mix = mix.low_pass_filter(10000) 
        
        for i in range(1, len(generated_files)):
            print(f"Mixing track {i+1}...")
            next_track = AudioSegment.from_wav(generated_files[i])
            next_track = next_track.low_pass_filter(10000) # Apply filter to each track
            # Crossfade
            mix = mix.append(next_track, crossfade=CROSSFADE_DURATION)
        
        # Final gentle volume normalization to avoid clipping after filtering
        mix = mix.normalize()

        # 3. Export
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = os.path.join(OUTPUT_DIR, f"lofi_refined_mix_{timestamp}.wav")
        
        print(f"Exporting final refined mix to {output_filename}...")
        mix.export(output_filename, format="wav")
        print("Done!")
        
    except Exception as e:
        print(f"Error during mixing: {e}")
        print("Ensure 'pydub' is installed and you are using WAV files if FFmpeg is missing.")

if __name__ == "__main__":
    main()
