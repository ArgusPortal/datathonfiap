"""
Configurações da aplicação via variáveis de ambiente.
Fase 8: Security, Privacy, SLO configuration.
"""

import os
from pathlib import Path


# Paths
BASE_DIR = Path(__file__).parent.parent
ARTIFACTS_DIR = BASE_DIR / "artifacts"
REGISTRY_DIR = BASE_DIR / os.getenv("REGISTRY_DIR", "models/registry")

# Model version: "champion" usa registry, ou versão específica, ou path direto
MODEL_VERSION = os.getenv("MODEL_VERSION", "")  # "champion", "v1.1.0", ou vazio

# Paths diretos (fallback se MODEL_VERSION não configurado)
MODEL_PATH = Path(os.getenv("MODEL_PATH", str(ARTIFACTS_DIR / "model_v1.joblib")))
METADATA_PATH = Path(os.getenv("METADATA_PATH", str(ARTIFACTS_DIR / "model_metadata_v1.json")))
SIGNATURE_PATH = Path(os.getenv("SIGNATURE_PATH", str(ARTIFACTS_DIR / "model_signature_v1.json")))

# API
PORT = int(os.getenv("PORT", "8000"))
APP_NAME = os.getenv("APP_NAME", "defasagem-risk-api")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Drift
DRIFT_STORE = os.getenv("DRIFT_STORE", "local_jsonl")
DRIFT_LOG_PATH = BASE_DIR / "logs" / "drift_events.jsonl"

# Features policy
EXTRA_FEATURE_POLICY = os.getenv("EXTRA_FEATURE_POLICY", "reject")  # "reject" or "ignore_with_warning"

# Threshold (carregado do metadata, mas pode ser sobrescrito)
DEFAULT_THRESHOLD = float(os.getenv("THRESHOLD", "0.040"))

# --- Phase 8: Security Configuration ---
# API Key authentication (comma-separated keys, empty for dev mode)
API_KEYS = os.getenv("API_KEYS", "")  

# Rate limiting
RATE_LIMIT_RPM = int(os.getenv("RATE_LIMIT_RPM", "60"))  # Requests per minute per key
MAX_BODY_BYTES = int(os.getenv("MAX_BODY_BYTES", "262144"))  # 256KB
REQUEST_TIMEOUT_MS = int(os.getenv("REQUEST_TIMEOUT_MS", "3000"))

# --- Phase 8: Privacy Configuration ---
PRIVACY_MODE = os.getenv("PRIVACY_MODE", "aggregate_only")  # aggregate_only, anonymized, full
RETENTION_DAYS = int(os.getenv("RETENTION_DAYS", "30"))

# --- Phase 8: SLO Configuration ---
SLO_P95_MS = int(os.getenv("SLO_P95_MS", "300"))
SLO_ERROR_RATE = float(os.getenv("SLO_ERROR_RATE", "0.01"))

# --- Phase 8: Observability ---
METRICS_ENABLED = os.getenv("METRICS_ENABLED", "true").lower() == "true"
AUDIT_ENABLED = os.getenv("AUDIT_ENABLED", "true").lower() == "true"

# Inference store path  
INFERENCE_STORE_PATH = BASE_DIR / "logs" / "inference_store.jsonl"

