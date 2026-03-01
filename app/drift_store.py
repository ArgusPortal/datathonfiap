"""
Armazenamento de estatísticas para monitoramento de drift.
NÃO armazena dados sensíveis (IDs, valores crus completos).
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

from app.config import DRIFT_LOG_PATH

logger = logging.getLogger("api")


def compute_feature_stats(features: Dict[str, Any]) -> Dict[str, Any]:
    """
    Computa estatísticas agregadas de features (sem valores crus).

    Args:
        features: Dicionário de features de uma instância

    Returns:
        Estatísticas agregadas
    """
    stats = {
        "n_features": len(features),
        "missing_features": [],
        "numeric_summary": {},
    }  # type: Dict[str, Any]

    for key, value in features.items():
        # Identifica missing
        if value is None or (isinstance(value, float) and np.isnan(value)):
            stats["missing_features"].append(key)

        # Categorical / string features — bin by value
        elif isinstance(value, str):
            stats["numeric_summary"][key] = f"cat_{value}"

        # Boolean-like (0/1) and small integer features
        elif isinstance(value, (int, float)):
            is_binary = isinstance(value, bool) or (
                isinstance(value, (int, float))
                and value in (0, 1)
                and key.endswith("_missing")
            )
            if is_binary:
                # Binary features: keep as 0/1 bins
                bin_label = "one" if value else "zero"
            elif value < 2:
                bin_label = "very_low"
            elif value < 4:
                bin_label = "low"
            elif value < 6:
                bin_label = "medium_low"
            elif value < 7:
                bin_label = "medium"
            elif value < 8.5:
                bin_label = "medium_high"
            else:
                bin_label = "high"
            stats["numeric_summary"][key] = bin_label

    return stats


def aggregate_batch_stats(instances: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Agrega estatísticas de um batch de instâncias.

    Args:
        instances: Lista de dicionários de features

    Returns:
        Estatísticas agregadas do batch
    """
    if not instances:
        return {"n_instances": 0}

    all_missing = []
    feature_bins = {}

    for inst in instances:
        stats = compute_feature_stats(inst)
        all_missing.extend(stats["missing_features"])

        for feat, bin_label in stats["numeric_summary"].items():
            if feat not in feature_bins:
                feature_bins[feat] = {}
            feature_bins[feat][bin_label] = feature_bins[feat].get(bin_label, 0) + 1

    # Conta missing por feature
    missing_counts: Dict[str, int] = {}
    for feat in all_missing:
        missing_counts[feat] = missing_counts.get(feat, 0) + 1

    # All features with missing values (not just top-5) for drift monitoring
    top_missing = sorted(missing_counts.items(), key=lambda x: -x[1])

    return {
        "n_instances": len(instances),
        "missing_summary": dict(top_missing),
        "feature_distribution": feature_bins,
    }


# Mapa de normalização: colapsa bins granulares em 3 bins canônicos
# para comparação PSI compatível entre versões de schema
BIN_NORMALIZATION_MAP = {
    "very_low": "low",  # <2  → canônico "low" (0-4)
    "low": "low",  # 2-4 → canônico "low"
    "medium_low": "medium",  # 4-6 → canônico "medium" (4-7)
    "medium": "medium",  # 6-7 → canônico "medium"
    "medium_high": "high",  # 7-8.5 → canônico "high" (7+)
    "high": "high",  # ≥8.5 → canônico "high"
    "zero": "binary",  # 0   → canônico "binary" (0/1 features)
    "one": "binary",  # 1   → canônico "binary"
}


def normalize_bins(dist: Dict[str, int]) -> Dict[str, int]:
    """
    Normaliza distribuição de bins para esquema canônico de 3 bins.
    Garante comparação PSI correta entre versões de schema de binning.

    Mapeamento:
      very_low + low → low
      medium_low + medium → medium
      medium_high + high → high
      zero + one → binary
      cat_* → preservado

    Args:
        dist: Distribuição original {bin_name: count}

    Returns:
        Distribuição normalizada {canonical_bin: count}
    """
    normalized: Dict[str, int] = {}
    for bin_key, count in dist.items():
        if bin_key.startswith("cat_"):
            canonical = bin_key  # Categorical bins preservados
        else:
            canonical = BIN_NORMALIZATION_MAP.get(bin_key, bin_key)
        normalized[canonical] = normalized.get(canonical, 0) + count
    return normalized


class DriftStore:
    """Armazena eventos de drift em arquivo JSONL."""

    def __init__(self, log_path: Path = DRIFT_LOG_PATH):
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log_event(
        self,
        request_id: str,
        model_version: str,
        instances: List[Dict[str, Any]],
        predictions: List[Dict[str, Any]],
    ) -> None:
        """
        Loga evento de predição com estatísticas agregadas.
        NÃO armazena IDs ou valores crus completos.
        """
        # Limpa IDs sensíveis das instâncias
        clean_instances = []
        for inst in instances:
            clean = {
                k: v
                for k, v in inst.items()
                if k.lower() not in ("ra", "id", "nome", "estudante_id", "student_id")
            }
            clean_instances.append(clean)

        # Agrega estatísticas
        batch_stats = aggregate_batch_stats(clean_instances)

        # Resumo de predições (sem vincular a instâncias específicas)
        pred_scores = [p.get("risk_score", 0) for p in predictions]
        pred_labels = [p.get("risk_label", 0) for p in predictions]

        event = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "request_id": request_id,
            "model_version": model_version,
            "bin_schema_version": 2,
            "batch_stats": batch_stats,
            "prediction_summary": {
                "n_predictions": len(predictions),
                "n_high_risk": sum(pred_labels),
                "mean_score": float(np.mean(pred_scores)) if pred_scores else 0,
                "score_bins": {
                    "low": sum(1 for s in pred_scores if s < 0.3),
                    "medium": sum(1 for s in pred_scores if 0.3 <= s < 0.7),
                    "high": sum(1 for s in pred_scores if s >= 0.7),
                },
            },
        }

        self._write_event(event)

    def _write_event(self, event: Dict[str, Any]) -> None:
        """Escreve evento no arquivo JSONL."""
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(event, default=str) + "\n")
        except Exception as e:
            logger.warning(f"Falha ao gravar drift event: {e}")

    def read_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Lê últimos eventos do log."""
        events: List[Dict[str, Any]] = []
        if not self.log_path.exists():
            return events

        with open(self.log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            for line in lines[-limit:]:
                try:
                    events.append(json.loads(line.strip()))
                except json.JSONDecodeError:
                    continue

        return events

    def clear_events(self) -> int:
        """Remove todos os eventos do log. Retorna contagem de eventos removidos."""
        count = 0
        if self.log_path.exists():
            with open(self.log_path, "r", encoding="utf-8") as f:
                count = sum(1 for _ in f)
            self.log_path.unlink()
            logger.info(f"Drift log cleared: {count} events removed")
        return count

    def event_count(self) -> int:
        """Retorna contagem total de eventos no log."""
        if not self.log_path.exists():
            return 0
        with open(self.log_path, "r", encoding="utf-8") as f:
            return sum(1 for _ in f)


# Instância global
drift_store = DriftStore()
