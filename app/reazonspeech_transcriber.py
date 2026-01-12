"""
ReazonSpeech (K2-ASR) Transcriber
Sherpa-ONNX バックエンドで高速日本語音声認識
"""
import logging
import time
from typing import Optional, Dict, Any, Union, BinaryIO

logger = logging.getLogger("reazonspeech-transcriber")

class ReazonSpeechTranscriber:
    """ReazonSpeech K2 (Sherpa-ONNX) バックエンド"""
    
    def __init__(self):
        """モデルをロード"""
        logger.info("Initializing ReazonSpeech-k2-v2...")
        
        try:
            from reazonspeech.k2.asr import load_model
            self.load_model = load_model
            from reazonspeech.k2.asr import transcribe as rs_transcribe
            self.rs_transcribe = rs_transcribe
            from reazonspeech.k2.asr import audio_from_path, audio_from_numpy
            self.audio_from_path = audio_from_path
            self.audio_from_numpy = audio_from_numpy
            
            load_start = time.time()
            self.model = self.load_model()
            logger.info(f"✓ ReazonSpeech loaded in {time.time() - load_start:.2f}s")
        except ImportError as e:
            logger.error(f"ReazonSpeech not installed: {e}")
            raise
    
    def transcribe(
        self,
        audio_path: Union[str, BinaryIO],
        language: Optional[str] = "ja",
        prompt: Optional[str] = None,
        response_format: str = "json"
    ) -> Dict[str, Any]:
        """
        音声ファイルを文字起こし
        soundfileで高速デコード + 16kHzリサンプリング
        """
        import tempfile
        import os
        import numpy as np
        import soundfile as sf
        from scipy import signal
        
        start_total = time.perf_counter()
        
        # BinaryIOの場合は一時ファイルに書き出す
        if hasattr(audio_path, 'read'):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                tmp.write(audio_path.read())
                audio_source = tmp.name
            cleanup_needed = True
        else:
            audio_source = audio_path
            cleanup_needed = False
        
        try:
            # soundfileで高速デコード (libsndfile経由)
            decode_start = time.perf_counter()
            try:
                audio_data, sr = sf.read(audio_source, dtype='float32')
            except Exception as sf_err:
                # soundfile失敗時はpydubでフォールバック
                logger.warning(f"soundfile failed, using pydub fallback: {sf_err}")
                from pydub import AudioSegment
                audio_seg = AudioSegment.from_file(audio_source)
                audio_seg = audio_seg.set_channels(1).set_frame_rate(16000)
                audio_data = np.array(audio_seg.get_array_of_samples(), dtype=np.float32) / 32768.0
                sr = 16000
            
            # ステレオならモノラルに変換
            if len(audio_data.shape) > 1:
                audio_data = audio_data.mean(axis=1)
            
            # 16kHzにリサンプリング (ReazonSpeech要求)
            if sr != 16000:
                num_samples = int(len(audio_data) * 16000 / sr)
                audio_data = signal.resample(audio_data, num_samples).astype(np.float32)
                sr = 16000
            
            decode_time = (time.perf_counter() - decode_start) * 1000
            
            # audio_from_numpyでAudioオブジェクト作成
            audio_obj_start = time.perf_counter()
            audio = self.audio_from_numpy(audio_data, sr)
            audio_obj_time = (time.perf_counter() - audio_obj_start) * 1000
            
            # 推論
            infer_start = time.perf_counter()
            result = self.rs_transcribe(self.model, audio)
            infer_time = (time.perf_counter() - infer_start) * 1000
            
            total_time = (time.perf_counter() - start_total) * 1000
            logger.info(f"ReazonSpeech: decode={decode_time:.0f}ms, infer={infer_time:.0f}ms, total={total_time:.0f}ms")
            
            text = result.text if hasattr(result, 'text') else str(result)
            
            if response_format == "verbose_json":
                return {
                    "task": "transcribe",
                    "language": "ja",
                    "duration": len(audio_data) / 16000,
                    "text": text.strip(),
                    "segments": []
                }
            else:
                return {"text": text.strip()}
        finally:
            if cleanup_needed and os.path.exists(audio_source):
                os.remove(audio_source)
    
    @property
    def model_size(self) -> str:
        return "reazonspeech-k2-v2"
    
    @property
    def device(self) -> str:
        return "cpu"
    
    @property
    def compute_type(self) -> str:
        return "float32"
    
    @property
    def is_gpu_enabled(self) -> bool:
        return False
