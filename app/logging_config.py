"""
Configuração de logging estruturado.
"""

import json
import logging
import time
import uuid
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Dict, Optional

from app.config import LOG_LEVEL


class StructuredFormatter(logging.Formatter):
    """Formatter que gera logs em JSON estruturado."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Adiciona campos extras se existirem como atributos do record
        for key in ("request_id", "latency_ms", "status_code", "method", "path", 
                   "endpoint", "model_version", "n_instances"):
            if hasattr(record, key):
                log_data[key] = getattr(record, key)
        
        return json.dumps(log_data, default=str)


def setup_logging(level: str = LOG_LEVEL) -> logging.Logger:
    """Configura logging estruturado."""
    logger = logging.getLogger("api")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Remove handlers existentes
    logger.handlers.clear()
    
    # Console handler com formato estruturado
    handler = logging.StreamHandler()
    handler.setFormatter(StructuredFormatter())
    logger.addHandler(handler)
    
    return logger


def generate_request_id() -> str:
    """Gera ID único para request."""
    return str(uuid.uuid4())[:8]


class RequestLogger:
    """Helper para logging de requests com request_id."""
    
    def __init__(self, request_id: str):
        self.request_id = request_id
        self.start_time: float = time.time()
        self.logger = logging.getLogger("api")
    
    def log_request_start(self, method: str, path: str) -> None:
        """Loga início do request."""
        self.logger.info(
            f"{method} {path}",
            extra={
                "request_id": self.request_id,
                "method": method,
                "path": path,
            }
        )
    
    def log_request_end(self, status_code: int, latency_ms: float) -> None:
        """Loga fim do request."""
        level = logging.INFO if status_code < 400 else logging.WARNING
        self.logger.log(
            level,
            f"Request completed with status {status_code}",
            extra={
                "request_id": self.request_id,
                "status_code": status_code,
                "latency_ms": round(latency_ms, 2),
            }
        )
    
    def log_error(self, error: str, latency_ms: float = None) -> None:
        """Loga erro."""
        extra = {"request_id": self.request_id}
        if latency_ms is not None:
            extra["latency_ms"] = round(latency_ms, 2)
        
        self.logger.error(error, extra=extra)
    
    def get_latency_ms(self) -> float:
        """Retorna latência em ms."""
        return (time.time() - self.start_time) * 1000


# Logger global
api_logger = setup_logging()
