"""
Carregamento de modelo e metadados.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib

from app.config import MODEL_PATH, METADATA_PATH, SIGNATURE_PATH, DEFAULT_THRESHOLD

logger = logging.getLogger("api")


class ModelLoadError(Exception):
    """Erro ao carregar modelo."""
    pass


def load_model(model_path: Path = MODEL_PATH) -> Any:
    """
    Carrega modelo serializado.
    
    Args:
        model_path: Caminho para o arquivo joblib
        
    Returns:
        Pipeline sklearn carregado ou None se não encontrar
    """
    if not model_path.exists():
        logger.warning(f"Modelo não encontrado: {model_path}")
        return None
    
    try:
        model = joblib.load(model_path)
        logger.info(f"Modelo carregado: {model_path}")
        return model
    except Exception as e:
        logger.error(f"Erro ao carregar modelo: {e}")
        return None


def load_json_file(path: Path) -> Optional[Dict[str, Any]]:
    """Carrega arquivo JSON."""
    if not path.exists():
        logger.warning(f"Arquivo não encontrado: {path}")
        return None
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"JSON inválido em {path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Erro ao carregar {path}: {e}")
        return None


def load_metadata(metadata_path: Path = METADATA_PATH) -> Optional[Dict[str, Any]]:
    """Carrega metadados do modelo."""
    return load_json_file(metadata_path)


def load_signature(signature_path: Path = SIGNATURE_PATH) -> Optional[Dict[str, Any]]:
    """Carrega signature do modelo (schema input/output)."""
    return load_json_file(signature_path)


class ModelManager:
    """Gerencia carregamento e cache do modelo."""
    
    def __init__(self):
        self._model: Optional[Any] = None
        self._metadata: Optional[Dict[str, Any]] = None
        self._signature: Optional[Dict[str, Any]] = None
        self._threshold: float = DEFAULT_THRESHOLD
        self._loaded: bool = False
    
    def load(
        self,
        model_path: Path = MODEL_PATH,
        metadata_path: Path = METADATA_PATH,
        signature_path: Optional[Path] = SIGNATURE_PATH
    ) -> None:
        """Carrega modelo e metadados."""
        self._model = load_model(model_path)
        
        if self._model is None:
            raise FileNotFoundError(f"Modelo não encontrado: {model_path}")
        
        self._metadata = load_metadata(metadata_path)
        
        if signature_path:
            self._signature = load_signature(signature_path)
        
        # Extrai threshold do metadata
        if self._metadata:
            threshold_policy = self._metadata.get("threshold_policy", {})
            self._threshold = threshold_policy.get("threshold_value", DEFAULT_THRESHOLD)
        
        self._loaded = True
        logger.info(f"ModelManager inicializado: v{self.version}, threshold={self._threshold:.4f}")
    
    @property
    def model(self) -> Any:
        if not self._loaded:
            raise ModelLoadError("Modelo não carregado. Chame load() primeiro.")
        return self._model
    
    @property
    def metadata(self) -> Dict[str, Any]:
        if not self._loaded:
            raise ModelLoadError("Metadados não carregados.")
        return self._metadata
    
    @property
    def signature(self) -> Dict[str, Any]:
        if not self._loaded:
            raise ModelLoadError("Signature não carregada.")
        return self._signature
    
    @property
    def version(self) -> str:
        if self._metadata:
            return self._metadata.get("model_version", "unknown")
        return "unknown"
    
    @property
    def threshold(self) -> float:
        return self._threshold
    
    @property
    def expected_features(self) -> List[str]:
        if self._metadata:
            return self._metadata.get("expected_features", [])
        return []
    
    @property
    def input_schema(self) -> Dict[str, str]:
        if self._signature:
            return self._signature.get("input_schema", {})
        return {}
    
    @property
    def is_loaded(self) -> bool:
        return self._loaded
    
    def get_safe_metadata(self) -> Dict[str, Any]:
        """Retorna subset seguro dos metadados para exposição via API."""
        if not self._metadata:
            return {}
        
        return {
            "model_version": self._metadata.get("model_version"),
            "created_at": self._metadata.get("created_at"),
            "target_definition": self._metadata.get("target_definition"),
            "model_family": self._metadata.get("model_family"),
            "expected_features": self._metadata.get("expected_features", []),
            "threshold": self._threshold,
            "calibration": self._metadata.get("calibration"),
        }


# Instância global
model_manager = ModelManager()
