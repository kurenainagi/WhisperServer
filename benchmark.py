import requests
import time
import os
import sys

AUDIO_URL = "https://pro-video.jp/voice/announce/mp3/001-sibutomo.mp3"
FILENAME = "001-sibutomo.mp3"
API_URL = "http://127.0.0.1:8000/openai/deployments/whisper-1/audio/transcriptions"

def download_audio():
    if not os.path.exists(FILENAME):
        print(f"1. Downloading {AUDIO_URL}...")
        start = time.time()
        r = requests.get(AUDIO_URL)
        with open(FILENAME, "wb") as f:
            f.write(r.content)
        print(f"Download complete: {len(r.content)} bytes in {time.time() - start:.2f}s")
    else:
        print(f"1. Using existing {FILENAME}")

def benchmark(runs=3):
    print(f"2. Transcribing ({runs} runs)...")
    times = []
    
    for i in range(runs):
        print(f"\n--- Run {i+1}/{runs} ---")
        try:
            with open(FILENAME, "rb") as f:
                start = time.time()
                response = requests.post(
                    API_URL, 
                    files={"file": (FILENAME, f, "audio/mpeg")},
                    data={"language": "ja"},
                    headers={"api-key": "test"} # Dummy key
                )
                duration = time.time() - start
                
            if response.status_code == 200:
                result = response.json()
                print(f"Result: {result.get('text', '')[:50]}...")
                print(f"Time: {duration:.2f} seconds")
                times.append(duration)
            else:
                print(f"Error: {response.status_code}")
                print(response.text)
        except Exception as e:
            print(f"Exception: {e}")

    if times:
        print("\n" + "="*30)
        print("Benchmark Results")
        print("="*30)
        for i, t in enumerate(times):
            print(f"Run {i+1}: {t:.2f}s")
        print("-" * 30)
        print(f"Average: {sum(times)/len(times):.2f}s")
        print(f"Fastest: {min(times):.2f}s")
        print("="*30)

if __name__ == "__main__":
    download_audio()
    benchmark()
