import logging
import torch
from typing import Optional, Dict, Any
from transformers import pipeline
import torch_directml

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WhisperInference:
    def __init__(self, model_size: str = "large-v3", device: str = "dml", compute_type: str = "float16"):
        self.model_id = f"openai/whisper-{model_size}"
        if model_size == "large-v3":
            self.model_id = "openai/whisper-large-v3"
            
        # DirectML Device Selection
        try:
            if device == "dml" and torch_directml.is_available():
                self.device = torch_directml.device()
                logger.info(f"Using DirectML Device: {self.device}")
            else:
                self.device = "cpu"
                logger.warning("DirectML not requested or available, falling back to CPU")
        except Exception as e:
            logger.error(f"Failed to initialize DirectML: {e}")
            self.device = "cpu"

        # FP16 is often supported on DML, but depends on the card.
        # "float16" in transformers usually means `torch_dtype=torch.float16`.
        if compute_type == "float16" and self.device != "cpu":
            # Force float32 for stability on DML if needed. Recent torch-directml is better but let's try 32 if 16 crashes.
            # self.torch_dtype = torch.float16
            logger.warning("Forcing float32 for DirectML stability despite float16 request.")
            self.torch_dtype = torch.float32
        else:
            self.torch_dtype = torch.float32

        logger.info(f"Loading Transformers Model: {self.model_id} on {self.device} ({self.torch_dtype})")
        
        try:
            self.pipe = pipeline(
                "automatic-speech-recognition",
                model=self.model_id,
                torch_dtype=self.torch_dtype,
                device=self.device, # Pass the actual device object
                chunk_length_s=30,
            )
            logger.info("Model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise e

    def transcribe(
        self, 
        audio_file: str, 
        language: Optional[str] = None, 
        prompt: Optional[str] = None,
        response_format: str = "json"
    ) -> Dict[str, Any]:
        
        logger.info(f"Transcribing {audio_file} (Language: {language})")
        
        generate_kwargs = {}
        if language:
            generate_kwargs["language"] = language
        if prompt:
            # Transformers uses 'prompt_ids' or similar, strict prompt support is tricky in pipeline
            # utilizing 'task' or forced_decoder_ids might be needed.
            # For simplicity, we skip prompt mapping unless specific transformers update allows "intial_prompt"
            pass

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
                    segments.append({
                        "id": i,
                        "seek": 0, # Transformers doesn't easily expose seek
                        "start": chunk["timestamp"][0],
                        "end": chunk["timestamp"][1],
                        "text": chunk["text"],
                        "tokens": [], # Not exposed easily
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
