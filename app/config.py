"""
Configurações da aplicação via variáveis de ambiente.
"""

import os
from pathlib import Path


# Paths
BASE_DIR = Path(__file__).parent.parent
ARTIFACTS_DIR = BASE_DIR / "artifacts"

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
