"""
Azure OpenAI Whisper API 互換サーバー
マルチモデル対応版 (Kotoba-Whisper + ReazonSpeech)
"""
import os
import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form, Header, HTTPException, Depends
from fastapi.responses import JSONResponse

from .model_registry import get_registry, MODEL_ALIASES
from .transcriber import WhisperTranscriber
from .reazonspeech_transcriber import ReazonSpeechTranscriber

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
    logger.info("Starting Multi-Model ASR Server")
    logger.info("=" * 50)
    
    registry = get_registry()
    
    # Kotoba-Whisper をロード
    try:
        logger.info("Loading Kotoba-Whisper (faster-whisper)...")
        kotoba = WhisperTranscriber(
            model_size=os.getenv("WHISPER_MODEL", "RoachLin/kotoba-whisper-v2.2-faster"),
            use_gpu=os.getenv("USE_GPU", "0") == "1"
        )
        registry.register("kotoba-whisper", kotoba)
    except Exception as e:
        logger.error(f"Failed to load Kotoba-Whisper: {e}")
    
    # ReazonSpeech をロード
    try:
        logger.info("Loading ReazonSpeech (k2-asr)...")
        reazon = ReazonSpeechTranscriber()
        registry.register("reazonspeech", reazon)
    except Exception as e:
        logger.warning(f"ReazonSpeech not available: {e}")
    
    logger.info("=" * 50)
    logger.info(f"Available models: {registry.available_models}")
    logger.info("=" * 50)
    
    yield
    
    logger.info("Shutting down ASR Server...")


app = FastAPI(
    title="Multi-Model ASR API",
    description="""
## Azure OpenAI Whisper API 互換のローカル音声認識サーバー

### 利用可能なモデル
- **whisper-1** / **kotoba-whisper**: Kotoba-Whisper v2.2 (高精度、日本語特化)
- **reazonspeech** / **reazonspeech-k2**: ReazonSpeech K2 (超高速、159Mパラメータ)

### 使用例
```
POST /openai/deployments/whisper-1/audio/transcriptions      # Kotoba-Whisper
POST /openai/deployments/reazonspeech/audio/transcriptions   # ReazonSpeech
```
    """,
    version="2.0.0",
    lifespan=lifespan
)


async def verify_api_key(api_key: Optional[str] = Header(None, alias="api-key")):
    """Azure OpenAI互換のAPIキー認証 (ローカル用: 空でなければOK)"""
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail={"error": {"code": "401", "message": "Missing api-key header."}}
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
    音声ファイルを文字起こし (Azure OpenAI Whisper API 互換)
    
    - **deployment_id**: モデル選択 (`whisper-1`, `kotoba-whisper`, `reazonspeech`, `reazonspeech-k2`)
    - **file**: 音声ファイル (mp3, wav, m4a, etc.)
    - **language**: 言語コード (ja, en, etc.) - Kotoba-Whisperのみ有効
    - **response_format**: `json` または `verbose_json`
    """
    registry = get_registry()
    
    try:
        transcriber = registry.get(deployment_id)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    
    try:
        await file.seek(0)
        
        logger.info(
            f"Request: model={deployment_id} -> {transcriber.model_size}, "
            f"file={file.filename}, language={language}"
        )
        
        result = transcriber.transcribe(
            audio_path=file.file,
            language=language or "ja",
            prompt=prompt,
            response_format=response_format
        )
        
        logger.info(f"Result: {result.get('text', '')[:80]}...")
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Transcription error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "InternalServerError", "message": str(e)}}
        )


@app.get("/health")
async def health_check():
    """ヘルスチェック & モデル一覧"""
    registry = get_registry()
    return {
        "status": "ok",
        "available_models": registry.list_models(),
        "default_model": registry.default_model,
        "model_aliases": MODEL_ALIASES
    }


@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "service": "Multi-Model ASR API",
        "version": "2.0.0",
        "endpoints": {
            "transcription": "/openai/deployments/{model}/audio/transcriptions",
            "health": "/health",
            "docs": "/docs"
        },
        "models": ["whisper-1", "reazonspeech"]
    }
