"""
ONNX Runtime + DirectML を使用した Whisper推論エンジン
WSL2環境でAMD GPU (Radeon 780M) を使用
"""
import os
import logging
from typing import Optional, Dict, Any

import onnxruntime as ort
from optimum.onnxruntime import ORTModelForSpeechSeq2Seq
from transformers import AutoProcessor, pipeline

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WhisperInference:
    def __init__(self, model_size: str = "large-v3", device: str = "gpu", compute_type: str = "float32"):
        """
        ONNX Runtime + DirectML バックエンドでWhisperモデルをロード
        
        Args:
            model_size: モデルサイズ (base, small, medium, large-v3等)
            device: "gpu" (DirectML) or "cpu"
            compute_type: 現在は float32 のみ対応
        """
        self.model_id = f"openai/whisper-{model_size}"
        if model_size == "large-v3":
            self.model_id = "openai/whisper-large-v3"
        
        # ONNX Runtime のプロバイダー設定
        # DirectML execution provider を使用してGPU加速
        available_providers = ort.get_available_providers()
        logger.info(f"Available ONNX Runtime providers: {available_providers}")
        
        if device == "gpu" and "DmlExecutionProvider" in available_providers:
            self.provider = "DmlExecutionProvider"
            logger.info("Using DirectML (DmlExecutionProvider) for GPU acceleration")
        elif device == "gpu":
            logger.warning("DmlExecutionProvider not available, falling back to CPU")
            self.provider = "CPUExecutionProvider"
        else:
            self.provider = "CPUExecutionProvider"
            logger.info("Using CPU execution provider")
        
        logger.info(f"Loading ONNX model: {self.model_id} with provider: {self.provider}")
        
        try:
            # Optimum を使用して ONNX 形式でモデルをロード
            # export=True で自動的に ONNX にエクスポート (初回のみ)
            self.processor = AutoProcessor.from_pretrained(self.model_id)
            self.model = ORTModelForSpeechSeq2Seq.from_pretrained(
                self.model_id,
                export=True,  # 初回は変換が必要
                provider=self.provider
            )
            
            # パイプラインを作成 (device_id はDirectMLでは使用しない)
            self.pipe = pipeline(
                "automatic-speech-recognition",
                model=self.model,
                tokenizer=self.processor.tokenizer,
                feature_extractor=self.processor.feature_extractor,
                chunk_length_s=30,
            )
            
            logger.info("ONNX model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load ONNX model: {e}")
            logger.warning("Attempting CPU fallback...")
            
            try:
                self.provider = "CPUExecutionProvider"
                self.processor = AutoProcessor.from_pretrained(self.model_id)
                self.model = ORTModelForSpeechSeq2Seq.from_pretrained(
                    self.model_id,
                    export=True,
                    provider=self.provider
                )
                self.pipe = pipeline(
                    "automatic-speech-recognition",
                    model=self.model,
                    tokenizer=self.processor.tokenizer,
                    feature_extractor=self.processor.feature_extractor,
                    chunk_length_s=30,
                )
                logger.info("Fallback to CPU successful.")
            except Exception as fb_e:
                logger.error(f"CPU fallback also failed: {fb_e}")
                raise RuntimeError("All model loading attempts failed.") from fb_e

    def transcribe(
        self, 
        audio_file: str, 
        language: Optional[str] = None, 
        prompt: Optional[str] = None,
        response_format: str = "json"
    ) -> Dict[str, Any]:
        """
        音声ファイルを文字起こし
        
        Args:
            audio_file: 音声ファイルのパス
            language: 言語コード (ja, en など)
            prompt: 初期プロンプト (現在は未使用)
            response_format: "json" or "verbose_json"
        
        Returns:
            Azure OpenAI互換のレスポンス
        """
        logger.info(f"Transcribing {audio_file} (Language: {language})")
        
        generate_kwargs = {}
        if language:
            generate_kwargs["language"] = language
        
        try:
            result = self.pipe(
                audio_file,
                return_timestamps=True,
                generate_kwargs=generate_kwargs
            )
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise e
        
        text = result["text"]
        
        if response_format == "verbose_json":
            segments = []
            if "chunks" in result:
                for i, chunk in enumerate(result["chunks"]):
                    start_time = chunk["timestamp"][0] if chunk["timestamp"][0] is not None else 0.0
                    end_time = chunk["timestamp"][1] if chunk["timestamp"][1] is not None else start_time
                    segments.append({
                        "id": i,
                        "seek": 0,
                        "start": start_time,
                        "end": end_time,
                        "text": chunk["text"],
                        "tokens": [],
                        "temperature": 0.0,
                        "avg_logprob": 0.0,
                        "compression_ratio": 0.0,
                        "no_speech_prob": 0.0
                    })
            
            return {
                "task": "transcribe",
                "language": language or "unknown",
                "duration": segments[-1]["end"] if segments else 0.0,
                "text": text,
                "segments": segments
            }
        else:
            return {
                "text": text
            }
