"""
faster-whisper (CTranslate2) を使用した Whisper推論エンジン
CPU (INT8) 最適化版 - Kotoba-Whisper v2.2 対応
"""
import logging
import os
import time
from typing import Optional, Dict, Any, List, Union, BinaryIO
from faster_whisper import WhisperModel

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("whisper-transcriber")

class WhisperTranscriber:
    """faster-whisper バックエンドでWhisperを実行"""
    
    def __init__(
        self, 
        model_size: str = "RoachLin/kotoba-whisper-v2.2-faster", 
        use_gpu: bool = False, # CPU推論をデフォルトにする
        cache_dir: Optional[str] = None
    ):
        """
        Args:
            model_size: モデル名またはパス。デフォルトは 'RoachLin/kotoba-whisper-v2.2-faster'
            use_gpu: GPUを使用するか (Recommended: False for INT8 CPU speed with faster-whisper on Ryzen)
            cache_dir: モデルキャッシュディレクトリ (未使用、faster-whisperが管理)
        """
        self.model_size = model_size
        self.use_gpu = use_gpu
        self.device = "cuda" if use_gpu else "cpu"
        self.compute_type = "float16" if use_gpu else "int8"
        
        logger.info(f"Initializing faster-whisper with model: {self.model_size}")
        logger.info(f"Device: {self.device}, Compute Type: {self.compute_type}")
        
        self._load_model()
    
    def _load_model(self):
        """モデルをロード"""
        try:
            self.model = WhisperModel(
                self.model_size, 
                device=self.device, 
                compute_type=self.compute_type,
                cpu_threads=os.cpu_count() # 全スレッド使用
            )
            logger.info("✓ Model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    def transcribe(
        self,
        audio_path: Union[str, BinaryIO],
        language: Optional[str] = "ja", # 日本語特化モデルのためデフォルトja
        prompt: Optional[str] = None,
        response_format: str = "json"
    ) -> Dict[str, Any]:
        """
        音声ファイルを文字起こし
        
        Args:
            audio_path: 音声ファイルのパス または ファイルオブジェクト
            language: 言語コード
            prompt: 初期プロンプト (faster-whisperでは initial_prompt)
            response_format: "json" or "verbose_json"
        
        Returns:
            Azure OpenAI互換のレスポンス
        """
        logger.info(f"Transcribing: {audio_path if isinstance(audio_path, str) else 'Buffered Reader'} (language={language})")
        
        try:
            # inference
            start_time = time.time()
            segments_generator, info = self.model.transcribe(
                audio_path, 
                language=language,
                beam_size=5,
                initial_prompt=prompt
            )
            
            # ジェネレータを展開して結果を取得 (ここで推論が実行される)
            segments = list(segments_generator)
            inference_time = time.time() - start_time
            logger.info(f"Inference completed in {inference_time:.2f}s")
            
            # テキスト結合
            full_text = "".join([segment.text for segment in segments])
            
            # infoからduration取得
            duration = info.duration
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise
        
        # レスポンス形式の構築
        if response_format == "verbose_json":
            start_build = time.time()
            resp = self._build_verbose_response(segments, full_text, duration, language)
            logger.info(f"Response build time: {time.time() - start_build:.4f}s")
            return resp
        else:
            return {"text": full_text.strip()}
    
    def _build_verbose_response(
        self, 
        segments: List[Any], 
        full_text: str,
        duration: float,
        language: Optional[str]
    ) -> Dict[str, Any]:
        """verbose_json形式のレスポンスを構築"""
        
        api_segments = []
        for i, seg in enumerate(segments):
            api_segments.append({
                "id": i,
                "seek": getattr(seg, "seek", 0), # faster-whisperのバージョンによる
                "start": seg.start,
                "end": seg.end,
                "text": seg.text.strip(),
                "tokens": seg.tokens,
                "temperature": getattr(seg, "temperature", 0.0),
                "avg_logprob": getattr(seg, "avg_logprob", 0.0),
                "compression_ratio": getattr(seg, "compression_ratio", 0.0),
                "no_speech_prob": getattr(seg, "no_speech_prob", 0.0)
            })
        
        return {
            "task": "transcribe",
            "language": language or "unknown",
            "duration": duration,
            "text": full_text.strip(),
            "segments": api_segments
        }
    
    @property
    def is_gpu_enabled(self) -> bool:
        return self.use_gpu

# モジュールレベルのシングルトン
_transcriber: Optional[WhisperTranscriber] = None

def get_transcriber() -> WhisperTranscriber:
    """グローバルなTranscriberインスタンスを取得"""
    global _transcriber
    if _transcriber is None:
        raise RuntimeError("Transcriber not initialized. Call init_transcriber() first.")
    return _transcriber

def init_transcriber(
    model_size: str = "RoachLin/kotoba-whisper-v2.2-faster",
    use_gpu: bool = False,
    cache_dir: Optional[str] = None
) -> WhisperTranscriber:
    """Transcriberを初期化"""
    global _transcriber
    
    # 環境変数での上書きを許容
    env_model = os.getenv("WHISPER_MODEL")
    if env_model and env_model != "small": # run.ps1 default is "small", ignore if standard default
         model_size = env_model
         # しかしユーザーがrun.ps1経由で別のモデルを指定した場合は尊重したい
         # run.ps1のデフォルトが "small" になっているので、
         # これを "RoachLin/kotoba-whisper-v2.2-faster" に変更する必要がある
    
    # ここでは引数を優先するが、呼び出し元の main.py で調整が必要
    
    _transcriber = WhisperTranscriber(
        model_size=model_size,
        use_gpu=use_gpu,
        cache_dir=cache_dir
    )
    return _transcriber
