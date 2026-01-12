"""
ModelRegistry - 複数モデルの管理
"""
import logging
from typing import Dict, Any, Optional, Protocol, Union, BinaryIO

logger = logging.getLogger("model-registry")

class Transcriber(Protocol):
    """Transcriber共通インターフェース"""
    def transcribe(
        self,
        audio_path: Union[str, BinaryIO],
        language: Optional[str] = None,
        prompt: Optional[str] = None,
        response_format: str = "json"
    ) -> Dict[str, Any]: ...
    
    @property
    def model_size(self) -> str: ...
    @property
    def device(self) -> str: ...
    @property
    def compute_type(self) -> str: ...
    @property
    def is_gpu_enabled(self) -> bool: ...


# デプロイメント名とモデルタイプのマッピング
MODEL_ALIASES = {
    # Kotoba-Whisper aliases
    "whisper-1": "kotoba-whisper",
    "kotoba-whisper": "kotoba-whisper",
    "kotoba": "kotoba-whisper",
    
    # ReazonSpeech aliases
    "reazonspeech": "reazonspeech",
    "reazonspeech-k2": "reazonspeech",
    "reazon": "reazonspeech",
}

DEFAULT_MODEL = "kotoba-whisper"


class ModelRegistry:
    """複数モデルを管理するレジストリ"""
    
    def __init__(self):
        self._models: Dict[str, Transcriber] = {}
        self._default_model = DEFAULT_MODEL
    
    def register(self, model_type: str, transcriber: Transcriber):
        """モデルを登録"""
        self._models[model_type] = transcriber
        logger.info(f"Registered model: {model_type} ({transcriber.model_size})")
    
    def get(self, deployment_id: str) -> Transcriber:
        """デプロイメント名からモデルを取得"""
        # エイリアス解決
        model_type = MODEL_ALIASES.get(deployment_id.lower(), self._default_model)
        
        if model_type not in self._models:
            logger.warning(f"Model '{model_type}' not loaded, falling back to default")
            model_type = self._default_model
        
        if model_type not in self._models:
            raise RuntimeError(f"No models available. Requested: {deployment_id}")
        
        return self._models[model_type]
    
    def list_models(self) -> Dict[str, Dict[str, Any]]:
        """利用可能なモデル一覧"""
        result = {}
        for model_type, transcriber in self._models.items():
            result[model_type] = {
                "model": transcriber.model_size,
                "device": transcriber.device,
                "compute_type": transcriber.compute_type,
                "aliases": [k for k, v in MODEL_ALIASES.items() if v == model_type]
            }
        return result
    
    @property
    def available_models(self) -> list:
        return list(self._models.keys())
    
    @property
    def default_model(self) -> str:
        return self._default_model


# グローバルレジストリ
_registry: Optional[ModelRegistry] = None

def get_registry() -> ModelRegistry:
    global _registry
    if _registry is None:
        _registry = ModelRegistry()
    return _registry
