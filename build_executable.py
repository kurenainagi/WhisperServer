import PyInstaller.__main__
import os
import shutil

# Clean previous build
if os.path.exists("build"):
    shutil.rmtree("build")
if os.path.exists("dist"):
    shutil.rmtree("dist")

print("Building WhisperServer executable...")

PyInstaller.__main__.run([
    'run_app.py',
    '--name=WhisperServer',
    '--clean',
    '--noconfirm',
    # Collect generic data often needed
    '--collect-all=sherpa_onnx',
    '--collect-all=soundfile',
    '--collect-all=uvicorn',
    '--collect-all=fastapi',
    # Hidden imports that PyInstaller might miss
    '--hidden-import=uvicorn.logging',
    '--hidden-import=uvicorn.loops',
    '--hidden-import=uvicorn.loops.auto',
    '--hidden-import=uvicorn.protocols',
    '--hidden-import=uvicorn.protocols.http',
    '--hidden-import=uvicorn.protocols.http.auto',
    '--hidden-import=uvicorn.lifespan.on',
    '--hidden-import=faster_whisper',
    '--hidden-import=reazonspeech',

    # Exclude unnecessary heavy modules if possible (though we need most)
    # '--exclude-module=tkinter',
])

# Create a launcher batch file for the exe
print("Creating launcher batch file...")
launcher_content = """@echo off
cd /d %~dp0
echo Starting Whisper Server...
WhisperServer.exe --port 8000
if %errorlevel% neq 0 (
    echo.
    echo Server exited with error.
    pause
)
"""
with open(os.path.join("dist", "WhisperServer", "start.bat"), "w") as f:
    f.write(launcher_content)

print("\nBuild complete. Check 'dist/WhisperServer' folder.")
