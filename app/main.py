"""
Azure OpenAI Whisper API 互換サーバー
Windows Native + ONNX Runtime DirectML
"""
import os
import uuid
import shutil
import logging
import tempfile
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form, Header, HTTPException, Depends
from fastapi.responses import JSONResponse

from .transcriber import init_transcriber, get_transcriber

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("whisper-api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションの起動・終了処理"""
    logger.info("=" * 50)
    logger.info("Starting Whisper API Server (Windows Native)")
    logger.info("=" * 50)
    
    # 環境変数から設定を取得
    model_size = os.getenv("WHISPER_MODEL", "RoachLin/kotoba-whisper-v2.2-faster")
    use_gpu = os.getenv("USE_GPU", "0") == "1" # Default to CPU
    cache_dir = os.getenv("MODEL_CACHE_DIR", None)
    
    logger.info(f"Configuration:")
    logger.info(f"  Model: {model_size}")
    logger.info(f"  GPU: {'enabled' if use_gpu else 'disabled'}")
    logger.info(f"  Cache: {cache_dir or 'default'}")
    
    try:
        init_transcriber(
            model_size=model_size,
            use_gpu=use_gpu,
            cache_dir=cache_dir
        )
        transcriber = get_transcriber()
        logger.info(f"  Device: {transcriber.device}")
        logger.info(f"  Compute: {transcriber.compute_type}")
        logger.info("=" * 50)
    except Exception as e:
        logger.critical(f"Failed to initialize Whisper: {e}")
        raise
    
    yield
    
    logger.info("Shutting down Whisper API Server...")


app = FastAPI(
    title="Local Azure OpenAI Whisper API",
    description="Azure OpenAI Whisper API互換のローカルサーバー (ONNX Runtime + DirectML)",
    version="1.0.0",
    lifespan=lifespan
)


async def verify_api_key(api_key: Optional[str] = Header(None, alias="api-key")):
    """
    Azure OpenAI互換のAPIキー認証 (ローカル用: 空でなければOK)
    """
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail={
                "error": {
                    "code": "401",
                    "message": "Access denied due to missing api-key header."
                }
            }
        )
    return api_key


@app.post("/openai/deployments/{deployment_id}/audio/transcriptions")
async def create_transcription(
    deployment_id: str,
    file: UploadFile = File(...),
    language: Optional[str] = Form(None),
    prompt: Optional[str] = Form(None),
    response_format: Optional[str] = Form("json"),
    api_key: str = Depends(verify_api_key)
):
    """
    Azure OpenAI Whisper API 互換エンドポイント
    
    - deployment_id: デプロイメント名 (任意の値を受け付け)
    - file: 音声ファイル (mp3, wav, m4a, etc.)
    - language: 言語コード (ja, en, etc.)
    - prompt: 初期プロンプト (現在未サポート)
    - response_format: json または verbose_json
    """
    try:
        transcriber = get_transcriber()
    except RuntimeError:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    
    # 以前の一時ファイルロジックを廃止し、ストリームを直接渡す
    try:
        # ファイルポインタを先頭に戻す (念のため)
        await file.seek(0)
        
        logger.info(
            f"Request: deployment={deployment_id}, "
            f"file={file.filename}, language={language}, format={response_format}"
        )
        
        # 実際に文字起こし
        result = transcriber.transcribe(
            audio_path=file.file,
            language=language or "ja", # デフォルトはモデルに合わせて日本語
            prompt=prompt,
            response_format=response_format
        )
        
        logger.info(f"Result: {result.get('text', '')[:100]}...")
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Transcription error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "InternalServerError",
                    "message": str(e)
                }
            }
        )

@app.get("/health")
async def health_check():
    """ヘルスチェックエンドポイント"""
    try:
        transcriber = get_transcriber()
        return {
            "status": "ok",
            "model_loaded": True,
            "model": transcriber.model_size,
            "device": transcriber.device,
            "compute_type": transcriber.compute_type,
            "gpu_enabled": transcriber.is_gpu_enabled
        }
    except RuntimeError:
        return {
            "status": "degraded",
            "model_loaded": False
        }


@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "service": "Local Azure OpenAI Whisper API",
        "version": "1.0.0",
        "endpoints": {
            "transcription": "/openai/deployments/{deployment_id}/audio/transcriptions",
            "health": "/health"
        }
    }
