"""
Audit Module - Rastreabilidade de modelo, dados e configuração.
Fase 8: Hardening de Produção.
"""

import hashlib
import json
import logging
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("api.audit")


def get_git_sha() -> str:
    """Get current git commit SHA."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()[:12]
    except Exception:
        pass
    return "unknown"


def get_git_branch() -> str:
    """Get current git branch."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return "unknown"


def hash_file(filepath: str) -> str:
    """Calculate SHA-256 hash of a file."""
    try:
        h = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception as e:
        logger.warning(f"Could not hash file {filepath}: {e}")
        return "error"


def hash_dict(data: Dict[str, Any]) -> str:
    """Calculate hash of a dictionary (deterministic)."""
    serialized = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode()).hexdigest()[:16]


def hash_model_artifact(model_path: str) -> Dict[str, str]:
    """
    Calculate hashes for model artifacts.
    Returns dict of filename -> hash.
    """
    path = Path(model_path)
    hashes = {}
    
    if path.is_file():
        hashes[path.name] = hash_file(str(path))
    elif path.is_dir():
        for f in path.glob("*"):
            if f.is_file():
                hashes[f.name] = hash_file(str(f))
    
    return hashes


class AuditTrail:
    """
    Audit trail for model inference and operations.
    """
    
    def __init__(self):
        self._records: List[Dict] = []
        self._max_records = 1000  # In-memory limit
        self.startup_time = datetime.now(timezone.utc).isoformat()
        self.git_sha = get_git_sha()
        self.git_branch = get_git_branch()
    
    def add_record(
        self,
        action: str,
        request_id: str = None,
        details: Dict[str, Any] = None,
    ) -> Dict:
        """Add an audit record."""
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "request_id": request_id,
            "details": details or {},
            "git_sha": self.git_sha,
        }
        
        self._records.append(record)
        
        # Trim old records if exceeding limit
        if len(self._records) > self._max_records:
            self._records = self._records[-self._max_records:]
        
        return record
    
    def get_records(
        self,
        action: str = None,
        limit: int = 100,
    ) -> List[Dict]:
        """Get audit records, optionally filtered by action."""
        records = self._records
        if action:
            records = [r for r in records if r["action"] == action]
        return list(reversed(records[:limit]))
    
    def get_summary(self) -> Dict:
        """Get audit summary."""
        actions = {}
        for r in self._records:
            action = r["action"]
            actions[action] = actions.get(action, 0) + 1
        
        return {
            "startup_time": self.startup_time,
            "git_sha": self.git_sha,
            "git_branch": self.git_branch,
            "total_records": len(self._records),
            "actions": actions,
        }
    
    def clear(self) -> None:
        """Clear audit trail - useful for testing."""
        self._records.clear()


class ModelLineage:
    """
    Track model lineage and provenance.
    """
    
    def __init__(self, model_path: str = None, version: str = None):
        self.model_path = model_path
        self.version = version
        self.loaded_at = datetime.now(timezone.utc).isoformat()
        self.artifact_hashes: Dict[str, str] = {}
        self.training_config: Dict[str, Any] = {}
        self.data_sources: List[str] = []
        
        if model_path:
            self.artifact_hashes = hash_model_artifact(model_path)
    
    def set_training_info(
        self,
        config: Dict[str, Any] = None,
        data_sources: List[str] = None,
    ) -> None:
        """Set training configuration and data sources."""
        if config:
            self.training_config = config
        if data_sources:
            self.data_sources = data_sources
    
    def get_lineage(self) -> Dict:
        """Get full lineage information."""
        return {
            "model_path": self.model_path,
            "version": self.version,
            "loaded_at": self.loaded_at,
            "artifact_hashes": self.artifact_hashes,
            "training_config": self.training_config,
            "data_sources": self.data_sources,
            "code": {
                "git_sha": get_git_sha(),
                "git_branch": get_git_branch(),
            },
        }
    
    def verify_integrity(self) -> Dict[str, bool]:
        """Verify model artifact integrity against stored hashes."""
        if not self.model_path or not self.artifact_hashes:
            return {"verified": False, "reason": "no_hashes"}
        
        current_hashes = hash_model_artifact(self.model_path)
        results = {}
        all_match = True
        
        for name, expected_hash in self.artifact_hashes.items():
            actual_hash = current_hashes.get(name)
            match = actual_hash == expected_hash
            results[name] = match
            if not match:
                all_match = False
                logger.warning(
                    f"Hash mismatch for {name}: expected {expected_hash}, got {actual_hash}"
                )
        
        return {
            "verified": all_match,
            "files": results,
        }


def create_inference_audit_record(
    request_id: str,
    input_hash: str,
    output_probability: float,
    model_version: str,
    latency_ms: float,
    success: bool,
) -> Dict:
    """
    Create a standardized inference audit record.
    No PII - only hashes and aggregates.
    """
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request_id": request_id,
        "input_hash": input_hash,
        "output": {
            "probability": round(output_probability, 6),
        },
        "model": {
            "version": model_version,
        },
        "performance": {
            "latency_ms": round(latency_ms, 2),
            "success": success,
        },
        "code_sha": get_git_sha(),
    }


# Global instances
audit_trail = AuditTrail()
model_lineage: Optional[ModelLineage] = None


def init_model_lineage(model_path: str, version: str) -> ModelLineage:
    """Initialize global model lineage."""
    global model_lineage
    model_lineage = ModelLineage(model_path, version)
    return model_lineage


def get_model_lineage() -> Optional[ModelLineage]:
    """Get global model lineage."""
    return model_lineage
