"""
Privacy Module - Sanitização e anonimização de dados.
Fase 8: Hardening de Produção.
"""

import hashlib
import logging
import re
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger("api.privacy")

# --- PII Patterns (Brazilian context) ---
PII_PATTERNS = {
    "cpf": re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b"),
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
    "phone": re.compile(r"\b(?:\+55)?\s*\(?\d{2}\)?\s*\d{4,5}-?\d{4}\b"),
    "cep": re.compile(r"\b\d{5}-?\d{3}\b"),
    "rg": re.compile(r"\b\d{2}\.?\d{3}\.?\d{3}-?\d{1}\b"),
}

# Fields that might contain PII and should never be logged
PII_FIELDS: Set[str] = {
    "nome", "name", "cpf", "email", "telefone", "phone",
    "endereco", "address", "cep", "rg", "documento", "document",
    "senha", "password", "token", "api_key", "secret",
}

# Fields safe to aggregate/log
SAFE_FIELDS: Set[str] = {
    "turnover", "headcount", "idade", "idade_empresa", "setor",
    "nota_exame", "horas_treinamento", "participou_projeto",
    "numero_avaliacoes", "promocoes_ultimos_3_anos",
    "nivel_senioridade", "nivel_escolaridade", "area_atuacao",
    "percentual_meta_batida", "pedido_demissao",
}


def hash_identifier(value: str, salt: str = "") -> str:
    """
    Hash an identifier for pseudonymization.
    Uses SHA-256 with optional salt for different contexts.
    """
    data = f"{salt}:{value}".encode()
    return hashlib.sha256(data).hexdigest()[:16]


def detect_pii(text: str) -> Dict[str, List[str]]:
    """
    Detect potential PII in text.
    Returns dict of pattern_name -> list of matches.
    """
    findings = {}
    for pattern_name, pattern in PII_PATTERNS.items():
        matches = pattern.findall(str(text))
        if matches:
            findings[pattern_name] = matches
    return findings


def has_pii(text: str) -> bool:
    """Check if text contains any PII patterns."""
    for pattern in PII_PATTERNS.values():
        if pattern.search(str(text)):
            return True
    return False


def redact_pii(text: str, replacement: str = "[REDACTED]") -> str:
    """Redact all detected PII patterns from text."""
    result = str(text)
    for pattern in PII_PATTERNS.values():
        result = pattern.sub(replacement, result)
    return result


def sanitize_dict_for_logging(
    data: Dict[str, Any],
    redact_pii_fields: bool = True,
    include_safe_only: bool = False,
) -> Dict[str, Any]:
    """
    Sanitize a dictionary for safe logging.
    
    Args:
        data: Input dictionary
        redact_pii_fields: If True, redact known PII fields
        include_safe_only: If True, only include explicitly safe fields
    
    Returns:
        Sanitized dictionary safe for logging
    """
    result = {}
    
    for key, value in data.items():
        key_lower = key.lower()
        
        # Skip if include_safe_only and not in safe list
        if include_safe_only and key_lower not in SAFE_FIELDS:
            continue
        
        # Redact known PII fields
        if redact_pii_fields and key_lower in PII_FIELDS:
            result[key] = "[REDACTED]"
            continue
        
        # Recursively sanitize nested dicts
        if isinstance(value, dict):
            result[key] = sanitize_dict_for_logging(
                value, redact_pii_fields, include_safe_only
            )
            continue
        
        # Check string values for PII patterns
        if isinstance(value, str):
            if has_pii(value):
                result[key] = redact_pii(value)
            else:
                result[key] = value
            continue
        
        # Pass through other types
        result[key] = value
    
    return result


def aggregate_features(features: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract only aggregate-safe features for metrics/logging.
    No individual-identifying information retained.
    """
    safe_data = {}
    
    for key, value in features.items():
        key_lower = key.lower()
        
        # Only include known safe fields
        if key_lower not in SAFE_FIELDS:
            continue
        
        # Convert to safe types
        if isinstance(value, (int, float)):
            safe_data[key] = value
        elif isinstance(value, str):
            # Only include categorical/enum-like strings
            if not has_pii(value) and len(value) < 50:
                safe_data[key] = value
    
    return safe_data


class PrivacyContext:
    """
    Context manager for privacy-aware operations.
    Ensures PII is not accidentally leaked.
    """
    
    def __init__(self, context_name: str = "default"):
        self.context_name = context_name
        self._original_data = None
    
    def sanitize_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize incoming request data."""
        self._original_data = data
        return sanitize_dict_for_logging(data, redact_pii_fields=True)
    
    def get_loggable(self, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get loggable version of data."""
        target = data or self._original_data or {}
        return sanitize_dict_for_logging(target, include_safe_only=True)
    
    def create_audit_record(
        self,
        action: str,
        data: Dict[str, Any],
        result: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create an audit record with sanitized data.
        """
        return {
            "context": self.context_name,
            "action": action,
            "data_hash": hash_identifier(str(sorted(data.items()))),
            "field_count": len(data),
            "safe_fields": list(set(data.keys()) & SAFE_FIELDS),
            "result": result,
        }


# Convenience instance
privacy = PrivacyContext("api")


def log_safe(logger_instance: logging.Logger, level: int, message: str, data: Dict[str, Any] = None):
    """
    Log message with sanitized data.
    Ensures no PII leaks into logs.
    """
    extra = {}
    if data:
        extra = sanitize_dict_for_logging(data, include_safe_only=True)
    logger_instance.log(level, message, extra=extra)
