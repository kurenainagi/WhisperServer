import os
import sys
import argparse
import uvicorn
import multiprocessing

# Windowsでのmultiprocessing対応 (PyInstallerで必要)
multiprocessing.freeze_support()

def main():
    parser = argparse.ArgumentParser(description="Whisper API Server (Windows Native)")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind (default: 8000)")
    parser.add_argument("--model", type=str, default="RoachLin/kotoba-whisper-v2.2-faster", help="Whisper model path/name")
    parser.add_argument("--gpu", action="store_true", help="Enable GPU (CUDA)")
    parser.add_argument("--reload", action="store_true", help="Enable hot reload (dev only)")
    
    args = parser.parse_args()
    
    # Set environment variables
    os.environ["WHISPER_MODEL"] = args.model
    os.environ["USE_GPU"] = "1" if args.gpu else "0"
    
    print(f"Starting Whisper Server on port {args.port}...")
    print(f"Model: {args.model}")
    print(f"GPU: {'Enabled' if args.gpu else 'Disabled'}")
    
    # Run uvicorn
    # Note: When frozen, we can't use "app.main:app" string format easily implicitly without import
    # But uvicorn.run works with string if the module is importable.
    # In PyInstaller, it's safer to import the app object directly if possible, or ensure app is in path.
    # However, passing the app object instance directly prevents uvicorn from using multiple workers properly,
    # but we are single process usually.
    
    try:
        from app.main import app
        uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="info")
    except ImportError as e:
        print(f"Failed to import app: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
