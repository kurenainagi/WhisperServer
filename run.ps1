# Windows Native Whisper API Server - Run Script

param(
    [string]$Model = "RoachLin/kotoba-whisper-v2.2-faster",
    [int]$Port = 8000,
    [switch]$GPU, # Default to CPU
    [switch]$Reload
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Whisper API Server (Windows Native)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 仮想環境の確認と有効化
if (-not (Test-Path ".venv")) {
    Write-Host "ERROR: Virtual environment not found. Run setup.ps1 first." -ForegroundColor Red
    exit 1
}

# FFmpegのパス設定 (WinGetでインストールされた場合)
$ffmpegPath = Get-ChildItem "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\Gyan.FFmpeg_*" -ErrorAction SilentlyContinue | 
              Select-Object -ExpandProperty FullName | 
              Join-Path -ChildPath "ffmpeg-8.0.1-full_build\bin"

if ($ffmpegPath -and (Test-Path $ffmpegPath)) {
    Write-Host "Found FFmpeg at: $ffmpegPath" -ForegroundColor Green
    $env:Path = "$ffmpegPath;$env:Path"
} else {
    Write-Host "WARNING: FFmpeg path not found in standard WinGet location." -ForegroundColor Yellow
}

& ".\.venv\Scripts\Activate.ps1"

# 環境変数の設定
$env:WHISPER_MODEL = $Model
$env:USE_GPU = if ($GPU) { "1" } else { "0" }

Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  Model: $Model" -ForegroundColor White
Write-Host "  GPU: $(if ($GPU) { 'enabled (CUDA)' } else { 'disabled (CPU INT8)' })" -ForegroundColor White
Write-Host "  Port: $Port" -ForegroundColor White
Write-Host ""

# サーバー起動 (Reloadフラグは下で使用)
Write-Host "Starting server..." -ForegroundColor Green
Write-Host "API: http://127.0.0.1:$Port" -ForegroundColor Cyan
Write-Host "Health: http://127.0.0.1:$Port/health" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop" -ForegroundColor Gray
Write-Host ""

if ($Reload) {
    python -m uvicorn app.main:app --host 127.0.0.1 --port $Port --reload
} else {
    python -m uvicorn app.main:app --host 127.0.0.1 --port $Port
}
