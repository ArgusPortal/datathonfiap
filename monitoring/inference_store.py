"""
Inference Store - Armazenamento de inferências sanitizado.
Suporta modos: aggregate_only (default) e sanitized_row_level.
Não armazena PII.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger("api")

# PII fields to strip
PII_FIELDS = {"ra", "nome", "id", "estudante_id", "student_id", "telefone", "endereco", "email"}


class InferenceStore:
    """Store for inference events with privacy-safe aggregation."""
    
    SCHEMA_VERSION = "1.0.0"
    
    def __init__(
        self,
        store_dir: Path,
        privacy_mode: str = "aggregate_only",
        store_format: str = "parquet"
    ):
        """
        Args:
            store_dir: Directory to store inference data
            privacy_mode: "aggregate_only" or "sanitized_row_level"
            store_format: "parquet" or "csv"
        """
        self.store_dir = Path(store_dir)
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self.privacy_mode = privacy_mode
        self.store_format = store_format
        self._buffer: List[Dict] = []
        self._buffer_size = 100
    
    def _get_partition_path(self, timestamp: datetime) -> Path:
        """Get file path for date partition."""
        date_str = timestamp.strftime("%Y-%m-%d")
        ext = "parquet" if self.store_format == "parquet" else "csv"
        return self.store_dir / f"inferences_{date_str}.{ext}"
    
    def _sanitize_features(
        self,
        features: Dict[str, Any],
        allowed_features: List[str]
    ) -> Dict[str, Any]:
        """Remove PII and keep only allowed features."""
        sanitized = {}
        for key, value in features.items():
            key_lower = key.lower()
            if key_lower in PII_FIELDS:
                continue
            if allowed_features and key not in allowed_features:
                continue
            sanitized[key] = value
        return sanitized
    
    def _compute_numeric_stats(
        self,
        instances: List[Dict[str, Any]],
        allowed_features: List[str]
    ) -> Dict[str, Dict[str, float]]:
        """Compute aggregated numeric stats per feature."""
        numeric_values: Dict[str, List[float]] = {}
        
        for inst in instances:
            for key, value in inst.items():
                if key.lower() in PII_FIELDS:
                    continue
                if allowed_features and key not in allowed_features:
                    continue
                if isinstance(value, (int, float)) and not np.isnan(value) if isinstance(value, float) else True:
                    if key not in numeric_values:
                        numeric_values[key] = []
                    numeric_values[key].append(float(value))
        
        stats = {}
        for key, values in numeric_values.items():
            if values:
                stats[key] = {
                    "mean": float(np.mean(values)),
                    "min": float(np.min(values)),
                    "max": float(np.max(values)),
                    "std": float(np.std(values)) if len(values) > 1 else 0.0,
                }
        return stats
    
    def _count_missing(
        self,
        instances: List[Dict[str, Any]],
        expected_features: List[str]
    ) -> Dict[str, int]:
        """Count missing values per feature."""
        missing_counts = {f: 0 for f in expected_features}
        
        for inst in instances:
            for feat in expected_features:
                value = inst.get(feat)
                if value is None or (isinstance(value, float) and np.isnan(value)):
                    missing_counts[feat] += 1
        
        return missing_counts
    
    def append_event(
        self,
        request_id: str,
        model_version: str,
        timestamp: datetime,
        instances: List[Dict[str, Any]],
        predictions: List[Dict[str, Any]],
        expected_features: List[str],
        latency_ms: float = 0.0,
        warnings: List[str] = None
    ) -> None:
        """
        Append inference event to store.
        
        In aggregate_only mode: stores only aggregated statistics.
        In sanitized_row_level mode: stores sanitized individual rows.
        """
        warnings = warnings or []
        
        # Clean instances from PII
        clean_instances = [
            self._sanitize_features(inst, expected_features)
            for inst in instances
        ]
        
        if self.privacy_mode == "aggregate_only":
            event = self._create_aggregate_event(
                request_id=request_id,
                model_version=model_version,
                timestamp=timestamp,
                instances=clean_instances,
                predictions=predictions,
                expected_features=expected_features,
                latency_ms=latency_ms,
                warnings=warnings
            )
            self._buffer.append(event)
        else:  # sanitized_row_level
            for idx, (inst, pred) in enumerate(zip(clean_instances, predictions)):
                event = self._create_row_event(
                    request_id=request_id,
                    model_version=model_version,
                    timestamp=timestamp,
                    instance_index=idx,
                    instance=inst,
                    prediction=pred,
                    latency_ms=latency_ms
                )
                self._buffer.append(event)
        
        if len(self._buffer) >= self._buffer_size:
            self.flush()
    
    def _create_aggregate_event(
        self,
        request_id: str,
        model_version: str,
        timestamp: datetime,
        instances: List[Dict[str, Any]],
        predictions: List[Dict[str, Any]],
        expected_features: List[str],
        latency_ms: float,
        warnings: List[str]
    ) -> Dict[str, Any]:
        """Create aggregated event record."""
        n_instances = len(instances)
        
        # Compute stats
        numeric_stats = self._compute_numeric_stats(instances, expected_features)
        missing_counts = self._count_missing(instances, expected_features)
        total_cells = n_instances * len(expected_features) if expected_features else 1
        missing_rate = sum(missing_counts.values()) / total_cells if total_cells > 0 else 0
        
        # Prediction stats
        scores = [p.get("risk_score", 0) for p in predictions]
        labels = [p.get("risk_label", 0) for p in predictions]
        
        return {
            "schema_version": self.SCHEMA_VERSION,
            "timestamp": timestamp.isoformat(),
            "request_id": request_id,
            "model_version": model_version,
            "n_instances": n_instances,
            "n_features_expected": len(expected_features),
            "missing_rate_overall": round(missing_rate, 4),
            "numeric_means": json.dumps({k: round(v["mean"], 4) for k, v in numeric_stats.items()}),
            "numeric_mins": json.dumps({k: round(v["min"], 4) for k, v in numeric_stats.items()}),
            "numeric_maxs": json.dumps({k: round(v["max"], 4) for k, v in numeric_stats.items()}),
            "risk_score_mean": round(float(np.mean(scores)), 4) if scores else 0,
            "risk_score_min": round(float(np.min(scores)), 4) if scores else 0,
            "risk_score_max": round(float(np.max(scores)), 4) if scores else 0,
            "risk_score_std": round(float(np.std(scores)), 4) if len(scores) > 1 else 0,
            "positive_rate": round(sum(labels) / len(labels), 4) if labels else 0,
            "latency_ms": round(latency_ms, 2),
            "warnings": json.dumps(warnings),
        }
    
    def _create_row_event(
        self,
        request_id: str,
        model_version: str,
        timestamp: datetime,
        instance_index: int,
        instance: Dict[str, Any],
        prediction: Dict[str, Any],
        latency_ms: float
    ) -> Dict[str, Any]:
        """Create row-level event record."""
        return {
            "schema_version": self.SCHEMA_VERSION,
            "timestamp": timestamp.isoformat(),
            "request_id": request_id,
            "model_version": model_version,
            "instance_index": instance_index,
            "features_sanitized": json.dumps(instance),
            "risk_score": prediction.get("risk_score", 0),
            "risk_label": prediction.get("risk_label", 0),
            "latency_ms": round(latency_ms, 2),
        }
    
    def flush(self) -> None:
        """Flush buffer to disk."""
        if not self._buffer:
            return
        
        try:
            import pandas as pd
            
            df = pd.DataFrame(self._buffer)
            
            # Get timestamp from first record for partition
            ts_str = self._buffer[0].get("timestamp", datetime.now(timezone.utc).isoformat())
            ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            path = self._get_partition_path(ts)
            
            # Append to existing file or create new
            if path.exists():
                if self.store_format == "parquet":
                    existing = pd.read_parquet(path)
                    df = pd.concat([existing, df], ignore_index=True)
                else:
                    existing = pd.read_csv(path)
                    df = pd.concat([existing, df], ignore_index=True)
            
            if self.store_format == "parquet":
                df.to_parquet(path, index=False)
            else:
                df.to_csv(path, index=False)
            
            logger.debug(f"Flushed {len(self._buffer)} events to {path}")
            self._buffer.clear()
            
        except Exception as e:
            logger.warning(f"Failed to flush inference store: {e}")
    
    def read_events(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 10000
    ) -> List[Dict[str, Any]]:
        """Read events from store within date range."""
        import pandas as pd
        
        all_events = []
        
        # List all files in store
        ext = "parquet" if self.store_format == "parquet" else "csv"
        files = sorted(self.store_dir.glob(f"inferences_*.{ext}"))
        
        for file_path in files:
            # Extract date from filename
            date_str = file_path.stem.replace("inferences_", "")
            try:
                file_date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            except ValueError:
                continue
            
            # Filter by date range
            if start_date and file_date.date() < start_date.date():
                continue
            if end_date and file_date.date() > end_date.date():
                continue
            
            # Read file
            try:
                if self.store_format == "parquet":
                    df = pd.read_parquet(file_path)
                else:
                    df = pd.read_csv(file_path)
                
                all_events.extend(df.to_dict("records"))
                
                if len(all_events) >= limit:
                    break
            except Exception as e:
                logger.warning(f"Failed to read {file_path}: {e}")
        
        return all_events[:limit]
    
    def __del__(self):
        """Flush remaining buffer on destruction."""
        try:
            self.flush()
        except Exception:
            pass


# Default instance (lazy initialized)
_inference_store: Optional[InferenceStore] = None


def get_inference_store(
    store_dir: Optional[Path] = None,
    privacy_mode: str = "aggregate_only",
    store_format: str = "parquet"
) -> InferenceStore:
    """Get or create inference store instance."""
    global _inference_store
    
    if _inference_store is None:
        if store_dir is None:
            store_dir = Path(__file__).parent / "inference_store"
        _inference_store = InferenceStore(store_dir, privacy_mode, store_format)
    
    return _inference_store
