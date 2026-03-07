"""
Metrics Module - In-memory metrics for observabilidade.
Fase 8: Hardening de Produção.

Counters are persisted to disk so they survive container restarts.
"""

import json
import logging
import os
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("api.metrics")

# SLO Configuration
SLO_P95_MS = int(os.getenv("SLO_P95_MS", "300"))
SLO_ERROR_RATE = float(os.getenv("SLO_ERROR_RATE", "0.01"))


@dataclass
class MetricBucket:
    """Rolling window metric bucket."""

    window_seconds: int = 60
    _values: List[float] = field(default_factory=list)
    _timestamps: List[float] = field(default_factory=list)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def add(self, value: float) -> None:
        """Add a value to the bucket."""
        with self._lock:
            now = time.time()
            self._values.append(value)
            self._timestamps.append(now)
            self._cleanup(now)

    def _cleanup(self, now: float) -> None:
        """Remove old values outside window."""
        cutoff = now - self.window_seconds
        while self._timestamps and self._timestamps[0] < cutoff:
            self._timestamps.pop(0)
            self._values.pop(0)

    def get_values(self) -> List[float]:
        """Get current values in window."""
        with self._lock:
            self._cleanup(time.time())
            return list(self._values)

    def count(self) -> int:
        """Count of values in window."""
        return len(self.get_values())

    def sum(self) -> float:
        """Sum of values in window."""
        return sum(self.get_values())

    def mean(self) -> Optional[float]:
        """Mean of values in window."""
        values = self.get_values()
        return sum(values) / len(values) if values else None

    def percentile(self, p: float) -> Optional[float]:
        """Calculate percentile (0-100)."""
        values = sorted(self.get_values())
        if not values:
            return None
        k = (len(values) - 1) * (p / 100)
        f = int(k)
        c = min(f + 1, len(values) - 1)
        return values[f] + (values[c] - values[f]) * (k - f)

    def reset(self) -> None:
        """Reset bucket."""
        with self._lock:
            self._values.clear()
            self._timestamps.clear()


@dataclass
class Counter:
    """Thread-safe counter."""

    _value: int = 0
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def inc(self, amount: int = 1) -> None:
        """Increment counter."""
        with self._lock:
            self._value += amount

    def get(self) -> int:
        """Get current value."""
        with self._lock:
            return self._value

    def reset(self) -> None:
        """Reset counter."""
        with self._lock:
            self._value = 0


class MetricsStore:
    """
    In-memory metrics store with optional disk persistence for counters.

    NOTE: For production multi-replica deployments,
    consider using Prometheus client library or external metrics service.
    """

    PERSIST_FILE = os.getenv(
        "METRICS_PERSIST_PATH", os.path.join("logs", "metrics_state.json")
    )
    _PERSIST_EVERY = 10  # persist after every N predictions

    def __init__(self):
        # Request latencies (ms)
        self.latency = MetricBucket(window_seconds=60)

        # Request counts
        self.requests_total = Counter()
        self.requests_success = Counter()
        self.requests_error = Counter()

        # Prediction specific
        self.predictions_total = Counter()
        self.predictions_positive = Counter()  # Above threshold
        self.predictions_negative = Counter()  # Below threshold

        # Model info
        self.model_version: str = "unknown"
        self.model_loaded_at: float = 0

        # Health checks
        self.health_checks = Counter()
        self.last_health_check: float = 0

        self._start_time = time.time()
        self._persist_counter = 0
        self._persist_lock = threading.Lock()

        # Snapshot history for latency/traffic charts
        self._history: deque[Dict[str, Any]] = deque(maxlen=120)
        self._snapshot_interval = 10  # seconds
        self._last_snapshot_time: float = 0
        self._prev_totals: Dict[str, int] | None = None

    def record_request(self, latency_ms: float, success: bool) -> None:
        """Record a request."""
        self.latency.add(latency_ms)
        self.requests_total.inc()
        if success:
            self.requests_success.inc()
        else:
            self.requests_error.inc()
        self._maybe_snapshot()

    def _maybe_snapshot(self) -> None:
        """Append a metrics snapshot if enough time has passed."""
        now = time.time()
        if now - self._last_snapshot_time < self._snapshot_interval:
            return
        self._last_snapshot_time = now

        total_req = self.requests_total.get()
        total_err = self.requests_error.get()

        prev = self._prev_totals
        req_delta = max(0, total_req - prev["requests"]) if prev else 0
        err_delta = max(0, total_err - prev["errors"]) if prev else 0
        self._prev_totals = {"requests": total_req, "errors": total_err}

        # Skip first tick (no delta baseline yet)
        if prev is None:
            return

        ts = time.strftime("%H:%M:%S", time.localtime(now))
        self._history.append(
            {
                "time": ts,
                "timestamp": now,
                "latency": round(self.latency.percentile(95) or 0, 2),
                "requests": req_delta,
                "errors": err_delta,
            }
        )

    def get_history(self, limit: int = 60) -> List[Dict[str, Any]]:
        """Return recent metrics snapshots for charting."""
        items = list(self._history)
        return items[-limit:]

    def record_prediction(self, probability: float, threshold: float) -> None:
        """Record a prediction result and periodically persist."""
        self.predictions_total.inc()
        if probability >= threshold:
            self.predictions_positive.inc()
        else:
            self.predictions_negative.inc()

        self._persist_counter += 1
        if self._persist_counter >= self._PERSIST_EVERY:
            self._persist_counter = 0
            self.persist()

    def record_health_check(self) -> None:
        """Record a health check."""
        self.health_checks.inc()
        self.last_health_check = time.time()

    def set_model_info(self, version: str) -> None:
        """Set model information."""
        self.model_version = version
        self.model_loaded_at = time.time()

    def get_slo_status(self) -> Dict:
        """Get SLO compliance status."""
        p95 = self.latency.percentile(95)
        total = self.requests_total.get()
        errors = self.requests_error.get()

        error_rate = errors / total if total > 0 else 0.0

        return {
            "latency_p95_ms": p95,
            "latency_slo_ms": SLO_P95_MS,
            "latency_slo_met": p95 is None or p95 <= SLO_P95_MS,
            "error_rate": error_rate,
            "error_rate_slo": SLO_ERROR_RATE,
            "error_rate_slo_met": error_rate <= SLO_ERROR_RATE,
            "overall_healthy": (p95 is None or p95 <= SLO_P95_MS)
            and error_rate <= SLO_ERROR_RATE,
        }

    def get_summary(self) -> Dict:
        """Get full metrics summary."""
        uptime = time.time() - self._start_time
        total_requests = self.requests_total.get()

        return {
            "uptime_seconds": round(uptime, 2),
            "requests": {
                "total": total_requests,
                "success": self.requests_success.get(),
                "error": self.requests_error.get(),
                "rate_per_minute": round(total_requests / (uptime / 60), 2)
                if uptime > 0
                else 0,
            },
            "latency_ms": {
                "p50": self.latency.percentile(50),
                "p95": self.latency.percentile(95),
                "p99": self.latency.percentile(99),
                "mean": self.latency.mean(),
            },
            "predictions": {
                "total": self.predictions_total.get(),
                "positive": self.predictions_positive.get(),
                "negative": self.predictions_negative.get(),
            },
            "model": {
                "version": self.model_version,
                "loaded_at": self.model_loaded_at,
            },
            "slo": self.get_slo_status(),
        }

    def to_prometheus_format(self) -> str:
        """Export metrics in Prometheus text format."""
        lines = []
        summary = self.get_summary()

        # Requests
        lines.append("# HELP api_requests_total Total number of requests")
        lines.append("# TYPE api_requests_total counter")
        lines.append(f'api_requests_total {summary["requests"]["total"]}')

        lines.append("# HELP api_requests_success_total Successful requests")
        lines.append("# TYPE api_requests_success_total counter")
        lines.append(f'api_requests_success_total {summary["requests"]["success"]}')

        lines.append("# HELP api_requests_error_total Failed requests")
        lines.append("# TYPE api_requests_error_total counter")
        lines.append(f'api_requests_error_total {summary["requests"]["error"]}')

        # Latency
        for pct in ["p50", "p95", "p99"]:
            val = summary["latency_ms"][pct]
            if val is not None:
                lines.append(f"# HELP api_latency_ms_{pct} Latency {pct}")
                lines.append(f"# TYPE api_latency_ms_{pct} gauge")
                lines.append(f"api_latency_ms_{pct} {val:.2f}")

        # Predictions
        lines.append("# HELP api_predictions_total Total predictions")
        lines.append("# TYPE api_predictions_total counter")
        lines.append(f'api_predictions_total {summary["predictions"]["total"]}')

        # Model info
        lines.append("# HELP api_model_info Model information")
        lines.append("# TYPE api_model_info gauge")
        lines.append(f'api_model_info{{version="{summary["model"]["version"]}"}} 1')

        # Uptime
        lines.append("# HELP api_uptime_seconds API uptime")
        lines.append("# TYPE api_uptime_seconds gauge")
        lines.append(f'api_uptime_seconds {summary["uptime_seconds"]}')

        # SLO
        lines.append("# HELP api_slo_healthy SLO compliance (1=healthy, 0=unhealthy)")
        lines.append("# TYPE api_slo_healthy gauge")
        lines.append(f'api_slo_healthy {1 if summary["slo"]["overall_healthy"] else 0}')

        return "\n".join(lines)

    def persist(self) -> None:
        """Persist prediction counters to disk."""
        with self._persist_lock:
            state = {
                "predictions_total": self.predictions_total.get(),
                "predictions_positive": self.predictions_positive.get(),
                "predictions_negative": self.predictions_negative.get(),
                "requests_total": self.requests_total.get(),
                "requests_success": self.requests_success.get(),
                "requests_error": self.requests_error.get(),
            }
            try:
                path = Path(self.PERSIST_FILE)
                path.parent.mkdir(parents=True, exist_ok=True)
                tmp = path.with_suffix(".tmp")
                tmp.write_text(json.dumps(state))
                tmp.replace(path)
            except Exception:
                logger.debug("Failed to persist metrics state", exc_info=True)

    def _load(self) -> None:
        """Load persisted counters from disk."""
        try:
            path = Path(self.PERSIST_FILE)
            if not path.exists():
                return
            state = json.loads(path.read_text())
            self.predictions_total.inc(state.get("predictions_total", 0))
            self.predictions_positive.inc(state.get("predictions_positive", 0))
            self.predictions_negative.inc(state.get("predictions_negative", 0))
            self.requests_total.inc(state.get("requests_total", 0))
            self.requests_success.inc(state.get("requests_success", 0))
            self.requests_error.inc(state.get("requests_error", 0))
            logger.info(
                "Loaded persisted metrics: %d predictions, %d requests",
                state.get("predictions_total", 0),
                state.get("requests_total", 0),
            )
        except Exception:
            logger.debug("Failed to load persisted metrics", exc_info=True)

    def reset(self) -> None:
        """Reset all metrics - useful for testing."""
        self.latency.reset()
        self.requests_total.reset()
        self.requests_success.reset()
        self.requests_error.reset()
        self.predictions_total.reset()
        self.predictions_positive.reset()
        self.predictions_negative.reset()
        self.health_checks.reset()
        self._start_time = time.time()


# Global metrics instance
metrics = MetricsStore()
