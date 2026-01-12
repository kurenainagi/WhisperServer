"""
ReazonSpeech vs Kotoba-Whisper Benchmark
Compares both models on the same audio file
"""
import time
import os
import requests
import traceback

AUDIO_URL = "https://pro-video.jp/voice/announce/mp3/001-sibutomo.mp3"
FILENAME = "001-sibutomo.mp3"

def download_audio():
    if not os.path.exists(FILENAME):
        print(f"Downloading {AUDIO_URL}...")
        r = requests.get(AUDIO_URL)
        with open(FILENAME, "wb") as f:
            f.write(r.content)
        print(f"Downloaded: {len(r.content)} bytes")
    else:
        print(f"Using existing {FILENAME}")

def benchmark_reazonspeech():
    """Benchmark ReazonSpeech K2 model (Sherpa-ONNX backend)"""
    print("\n" + "="*50)
    print("ReazonSpeech K2 Benchmark")
    print("="*50)
    
    try:
        from reazonspeech.k2.asr import load_model, transcribe, audio_from_path
        
        print("Loading ReazonSpeech model...")
        load_start = time.time()
        model = load_model()
        load_time = time.time() - load_start
        print(f"Model loaded in {load_time:.2f}s")
        
        print(f"Transcribing {FILENAME}...")
        audio = audio_from_path(FILENAME)
        
        start = time.time()
        result = transcribe(model, audio)
        duration = time.time() - start
        
        print(f"Result: {result.text[:100]}...")
        print(f"Time: {duration:.2f} seconds")
        
        return {
            "model": "ReazonSpeech-k2-v2",
            "load_time": load_time,
            "inference_time": duration,
            "text": result.text
        }
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        return None

def benchmark_kotoba_whisper():
    """Benchmark Kotoba-Whisper via API (server must be running)"""
    print("\n" + "="*50)
    print("Kotoba-Whisper Benchmark (via API)")
    print("="*50)
    
    api_url = "http://127.0.0.1:8000/openai/deployments/whisper-1/audio/transcriptions"
    
    try:
        with open(FILENAME, "rb") as f:
            start = time.time()
            response = requests.post(
                api_url,
                files={"file": (FILENAME, f, "audio/mpeg")},
                data={"language": "ja"},
                headers={"api-key": "test"}
            )
            duration = time.time() - start
        
        if response.status_code == 200:
            result = response.json()
            print(f"Result: {result.get('text', '')[:100]}...")
            print(f"Time: {duration:.2f} seconds")
            return {
                "model": "Kotoba-Whisper-v2.2",
                "load_time": 0,  # Already loaded
                "inference_time": duration,
                "text": result.get("text", "")
            }
        else:
            print(f"API Error: {response.status_code}")
            print("Note: Make sure the Whisper server is running (start_server.bat)")
            return None
    except requests.exceptions.ConnectionError:
        print("Server not running. Skipping Kotoba-Whisper benchmark.")
        print("Run start_server.bat first to include Kotoba-Whisper comparison.")
        return None

def main():
    print("="*50)
    print("ASR Model Comparison Benchmark")
    print("="*50)
    
    download_audio()
    
    results = []
    
    # Benchmark ReazonSpeech
    rs_result = benchmark_reazonspeech()
    if rs_result:
        results.append(rs_result)
    
    # Benchmark Kotoba-Whisper (if server running)
    kw_result = benchmark_kotoba_whisper()
    if kw_result:
        results.append(kw_result)
    
    # Summary
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    print(f"{'Model':<30} {'Load Time':<12} {'Inference':<12}")
    print("-"*54)
    for r in results:
        print(f"{r['model']:<30} {r['load_time']:.2f}s{'':<6} {r['inference_time']:.2f}s")
    
    if len(results) == 2:
        diff = results[1]["inference_time"] - results[0]["inference_time"]
        faster = results[0]["model"] if diff > 0 else results[1]["model"]
        print(f"\n🏆 Winner: {faster} (by {abs(diff):.2f}s)")

if __name__ == "__main__":
    main()
