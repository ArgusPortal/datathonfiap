"""
Observability module for structured request logging.
Provides helpers for logging inference requests with full context.
"""

import json
import logging
import time
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Callable, Dict, List, Optional

import numpy as np

logger = logging.getLogger("api")

# Fields to exclude from logs (PII)
PII_FIELDS = {"ra", "nome", "id", "estudante_id", "student_id", "telefone", "endereco", "email"}


class Timer:
    """Context manager for timing operations."""
    
    def __init__(self):
        self.start_time: float = 0
        self.end_time: float = 0
        self.elapsed_ms: float = 0
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, *args):
        self.end_time = time.perf_counter()
        self.elapsed_ms = (self.end_time - self.start_time) * 1000


def safe_summarize_inputs(
    instances: List[Dict[str, Any]],
    expected_features: List[str],
    top_n: int = 10
) -> Dict[str, Any]:
    """
    Summarize input features without exposing raw values or PII.
    Returns aggregated statistics only.
    """
    n_instances = len(instances)
    
    if n_instances == 0:
        return {
            "n_instances": 0,
            "n_features_expected": len(expected_features),
            "n_features_received": 0,
            "missing_features_count": 0,
            "extra_features_count": 0,
        }
    
    # Count features across instances
    all_received_features = set()
    missing_counts: Dict[str, int] = {f: 0 for f in expected_features}
    extra_features = set()
    numeric_values: Dict[str, List[float]] = {}
    
    for inst in instances:
        received = set(k for k in inst.keys() if k.lower() not in PII_FIELDS)
        all_received_features.update(received)
        
        # Count missing
        for feat in expected_features:
            value = inst.get(feat)
            if value is None or (isinstance(value, float) and np.isnan(value)):
                missing_counts[feat] += 1
            elif isinstance(value, (int, float)):
                if feat not in numeric_values:
                    numeric_values[feat] = []
                numeric_values[feat].append(float(value))
        
        # Track extra features
        extra_features.update(received - set(expected_features))
    
    # Compute numeric summary (top N features by variance)
    numeric_summary = {}
    feature_variances = []
    
    for feat, values in numeric_values.items():
        if len(values) > 0:
            mean_val = float(np.mean(values))
            var_val = float(np.var(values)) if len(values) > 1 else 0
            feature_variances.append((feat, var_val, mean_val, min(values), max(values)))
    
    # Sort by variance (descending) and take top N
    feature_variances.sort(key=lambda x: -x[1])
    for feat, var_val, mean_val, min_val, max_val in feature_variances[:top_n]:
        numeric_summary[feat] = {
            "mean": round(mean_val, 4),
            "min": round(min_val, 4),
            "max": round(max_val, 4),
        }
    
    return {
        "n_instances": n_instances,
        "n_features_expected": len(expected_features),
        "n_features_received": len(all_received_features),
        "missing_features_count": sum(1 for c in missing_counts.values() if c > 0),
        "extra_features_count": len(extra_features),
        "total_missing_cells": sum(missing_counts.values()),
        "numeric_summary": numeric_summary,
    }


def safe_summarize_outputs(predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Summarize prediction outputs without exposing individual results.
    """
    if not predictions:
        return {"n_predictions": 0}
    
    scores = [p.get("risk_score", 0) for p in predictions]
    labels = [p.get("risk_label", 0) for p in predictions]
    
    return {
        "n_predictions": len(predictions),
        "score_min": round(float(np.min(scores)), 4),
        "score_mean": round(float(np.mean(scores)), 4),
        "score_max": round(float(np.max(scores)), 4),
        "score_std": round(float(np.std(scores)), 4) if len(scores) > 1 else 0,
        "positive_count": sum(labels),
        "positive_rate": round(sum(labels) / len(labels), 4),
    }


def log_inference_request(
    request_id: str,
    model_version: str,
    instances: List[Dict[str, Any]],
    predictions: List[Dict[str, Any]],
    expected_features: List[str],
    latency_ms: float,
    status_code: int = 200,
    warnings: List[str] = None
) -> Dict[str, Any]:
    """
    Log complete inference request with all required fields.
    Returns the log entry dict.
    """
    warnings = warnings or []
    
    input_summary = safe_summarize_inputs(instances, expected_features)
    output_summary = safe_summarize_outputs(predictions)
    
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "request_id": request_id,
        "endpoint": "/predict",
        "status_code": status_code,
        "latency_ms": round(latency_ms, 2),
        "model_version": model_version,
        "n_instances": input_summary["n_instances"],
        "n_features_expected": input_summary["n_features_expected"],
        "n_features_received": input_summary["n_features_received"],
        "missing_features_count": input_summary["missing_features_count"],
        "extra_features_count": input_summary["extra_features_count"],
        "input_numeric_summary": input_summary.get("numeric_summary", {}),
        "output_summary": output_summary,
        "warnings": warnings,
    }
    
    # Log as structured JSON
    logger.info(
        "Inference request completed",
        extra={
            "request_id": request_id,
            "model_version": model_version,
            "latency_ms": log_entry["latency_ms"],
            "n_instances": log_entry["n_instances"],
            "status_code": status_code,
        }
    )
    
    return log_entry


def timed_inference(func: Callable) -> Callable:
    """Decorator to time inference functions."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        with Timer() as timer:
            result = func(*args, **kwargs)
        return result, timer.elapsed_ms
    return wrapper
