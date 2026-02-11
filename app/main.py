"""
API FastAPI para predição de risco de defasagem escolar.
Passos Mágicos - Datathon FIAP 2025
Phase 8: Production Hardening - Security, Metrics, Audit
Phase 9: Extended endpoints for frontend integration
"""

import json
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse

from app.config import (
    APP_NAME,
    ARTIFACTS_DIR,
    AUDIT_ENABLED,
    EXTRA_FEATURE_POLICY,
    LOG_LEVEL,
    METADATA_PATH,
    METRICS_ENABLED,
    MODEL_PATH,
    PORT,
    SIGNATURE_PATH,
)
from app.drift_store import drift_store
from app.logging_config import RequestLogger, generate_request_id, setup_logging
from app.model_loader import ModelManager
from app.observability import log_inference_request
from app.schema import (
    ErrorResponse,
    HealthResponse,
    MetadataResponse,
    PredictionResult,
    PredictRequest,
    PredictResponse,
    validate_batch_features,
)

# Phase 8: Security, Metrics, Audit, Privacy
from app.security import SecurityMiddleware
from app.metrics import metrics
from app.audit import (
    audit_trail,
    init_model_lineage,
    create_inference_audit_record,
    hash_dict,
)

# Base directory
BASE_DIR = Path(__file__).parent.parent

# Try to import inference store
INFERENCE_STORE_ENABLED = False
try:
    from monitoring.inference_store import InferenceStore

    INFERENCE_STORE_ENABLED = True
except ImportError:
    pass


def get_inference_store(store_dir: Path) -> "InferenceStore":
    """Lazy factory for inference store."""
    return InferenceStore(store_dir=store_dir)


# Setup logging
logger = setup_logging(LOG_LEVEL)

# Model manager global
model_manager = ModelManager()

# Inference store (lazy init)
_inference_store = None

# Track startup time
_startup_time: float = 0.0


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager para carregar modelo no startup."""
    global _startup_time
    _startup_time = time.time()

    logger.info("Iniciando aplicação...")

    # Carrega modelo
    try:
        model_manager.load(MODEL_PATH, METADATA_PATH, SIGNATURE_PATH)
        logger.info(
            "Modelo carregado com sucesso",
            extra={
                "model_version": model_manager.version,
                "threshold": model_manager.threshold,
                "n_features": len(model_manager.expected_features),
            },
        )

        # Phase 8: Initialize model lineage and metrics
        init_model_lineage(str(MODEL_PATH), model_manager.version)
        metrics._load()  # restore persisted counters from previous run
        metrics.set_model_info(model_manager.version)

        if AUDIT_ENABLED:
            audit_trail.add_record(
                "startup",
                details={
                    "model_version": model_manager.version,
                    "model_path": str(MODEL_PATH),
                },
            )

    except Exception as e:
        logger.error(f"Falha ao carregar modelo: {e}")
        raise

    yield

    # Persist metrics counters before shutdown
    if METRICS_ENABLED:
        metrics.persist()

    if AUDIT_ENABLED:
        audit_trail.add_record("shutdown")
    logger.info("Encerrando aplicação...")


# Cria app FastAPI
app = FastAPI(
    title=APP_NAME,
    description="API para predição de risco de defasagem escolar - Passos Mágicos",
    version="1.0.0",
    lifespan=lifespan,
)

# Phase 9: CORS for Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:80",
        "http://localhost",
        "http://127.0.0.1:3000",
        "http://127.0.0.1",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Phase 8: Add Security Middleware
app.add_middleware(SecurityMiddleware)


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Middleware para logging estruturado de requests."""
    request_id = generate_request_id()
    request.state.request_id = request_id
    request.state.logger = RequestLogger(request_id)

    # Log início do request
    request.state.logger.log_request_start(
        method=request.method,
        path=request.url.path,
    )

    # Processa request
    start_time = time.time()
    try:
        response = await call_next(request)
        latency_ms = (time.time() - start_time) * 1000

        # Phase 8: Record metrics
        if METRICS_ENABLED:
            success = response.status_code < 400
            metrics.record_request(latency_ms, success)

        # Log fim do request
        request.state.logger.log_request_end(
            status_code=response.status_code,
            latency_ms=latency_ms,
        )

        # Adiciona request_id no header
        response.headers["X-Request-ID"] = request_id

        return response

    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        if METRICS_ENABLED:
            metrics.record_request(latency_ms, success=False)
        request.state.logger.log_error(str(e), latency_ms=latency_ms)
        raise


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check do serviço.
    Retorna status do modelo e uptime.
    """
    uptime = time.time() - _startup_time

    if METRICS_ENABLED:
        metrics.record_health_check()

    return HealthResponse(
        status="healthy" if model_manager.model is not None else "degraded",
        model_loaded=model_manager.model is not None,
        model_version=model_manager.version,
        uptime_seconds=round(uptime, 2),
    )


@app.get("/ready", tags=["Health"])
async def readiness_check():
    """
    Readiness probe para Kubernetes/orchestrators.
    Returns 200 if model is loaded and ready to serve.
    """
    if model_manager.model is None:
        return JSONResponse(
            status_code=503,
            content={"ready": False, "reason": "model_not_loaded"},
        )

    return {"ready": True, "model_version": model_manager.version}


@app.get("/metadata", response_model=MetadataResponse, tags=["Model"])
async def get_metadata():
    """
    Retorna metadata do modelo carregado.
    """
    if model_manager.model is None:
        raise HTTPException(status_code=503, detail="Modelo não carregado")

    safe_metadata = model_manager.get_safe_metadata()

    return MetadataResponse(
        model_version=safe_metadata.get("model_version", "unknown"),
        model_family=safe_metadata.get("model_family", "unknown"),
        threshold=safe_metadata.get("threshold", 0.5),
        expected_features=safe_metadata.get("expected_features", []),
        calibration=safe_metadata.get("calibration"),
        created_at=safe_metadata.get("created_at"),
    )


@app.get("/metrics", tags=["Observability"])
async def get_metrics(format: str = "json"):
    """
    Retorna métricas da API.

    Args:
        format: 'json' or 'prometheus'
    """
    if not METRICS_ENABLED:
        return {"error": "Metrics disabled"}

    if format == "prometheus":
        return PlainTextResponse(
            content=metrics.to_prometheus_format(),
            media_type="text/plain",
        )

    return metrics.get_summary()


@app.get("/slo", tags=["Observability"])
async def get_slo_status():
    """
    Retorna status de compliance com SLOs.
    """
    if not METRICS_ENABLED:
        return {"error": "Metrics disabled"}

    return metrics.get_slo_status()


@app.post("/predict", response_model=PredictResponse, tags=["Prediction"])
async def predict(request: Request, payload: PredictRequest):
    """
    Realiza predição de risco de defasagem.

    Aceita batch de instâncias (até 1000).
    Retorna score de risco (0-1) e label binário (0/1).
    """
    global _inference_store

    request_id = getattr(request.state, "request_id", generate_request_id())
    start_time = time.time()
    warnings_list: list[str] = []

    if model_manager.model is None:
        raise HTTPException(status_code=503, detail="Modelo não carregado")

    try:
        # Valida features
        validated_instances = validate_batch_features(
            payload.instances,
            model_manager.expected_features,
            EXTRA_FEATURE_POLICY,
        )

        # Converte para DataFrame
        df = pd.DataFrame(validated_instances)

        # Predição de probabilidades
        probas = model_manager.model.predict_proba(df)[:, 1]

        # Aplica threshold
        threshold = model_manager.threshold
        labels = (probas >= threshold).astype(int)

        # Monta resultados
        predictions = []
        for score, label in zip(probas, labels):
            predictions.append(
                PredictionResult(
                    risk_score=round(float(score), 6),
                    risk_label=int(label),
                    model_version=model_manager.version,
                )
            )

        processing_time = (time.time() - start_time) * 1000

        # Phase 8: Record metrics and audit
        if METRICS_ENABLED:
            for p in predictions:
                metrics.record_prediction(p.risk_score, threshold)

        if AUDIT_ENABLED:
            # Create audit record with sanitized data (no PII)
            audit_record = create_inference_audit_record(
                request_id=request_id,
                input_hash=hash_dict(
                    {"instances": [dict(i) for i in payload.instances]}
                ),
                output_probability=float(np.mean(probas)),
                model_version=model_manager.version,
                latency_ms=processing_time,
                success=True,
            )
            audit_trail.add_record("inference", request_id, audit_record)

        # Log completo de inferência (observability)
        log_inference_request(
            request_id=request_id,
            model_version=model_manager.version,
            instances=[dict(inst) for inst in payload.instances],
            predictions=[p.model_dump() for p in predictions],
            expected_features=model_manager.expected_features,
            latency_ms=processing_time,
            status_code=200,
            warnings=warnings_list,
        )

        # Log drift stats (legacy)
        try:
            drift_store.log_event(
                request_id=request_id,
                model_version=model_manager.version,
                instances=payload.instances,
                predictions=[p.model_dump() for p in predictions],
            )
        except Exception as e:
            logger.warning(f"Falha ao logar drift: {e}")

        # Log to inference store (if enabled)
        if INFERENCE_STORE_ENABLED:
            try:
                if _inference_store is None:
                    _inference_store = get_inference_store(
                        store_dir=BASE_DIR / "monitoring" / "inference_store"
                    )
                _inference_store.append_event(
                    request_id=request_id,
                    model_version=model_manager.version,
                    timestamp=datetime.now(timezone.utc),
                    instances=[dict(inst) for inst in payload.instances],
                    predictions=[p.model_dump() for p in predictions],
                    expected_features=model_manager.expected_features,
                    latency_ms=processing_time,
                    warnings=warnings_list,
                )
            except Exception as e:
                logger.warning(f"Falha ao logar inference store: {e}")

        return PredictResponse(
            predictions=predictions,
            request_id=request_id,
            processing_time_ms=round(processing_time, 2),
        )

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Erro na predição: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro interno na predição")


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handler customizado para HTTPException."""
    request_id = getattr(request.state, "request_id", None)

    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            detail=exc.detail,
            request_id=request_id,
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handler para exceções não tratadas."""
    request_id = getattr(request.state, "request_id", None)
    logger.error(f"Exceção não tratada: {exc}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            detail="Erro interno do servidor",
            request_id=request_id,
        ).model_dump(),
    )


# =========================================================
# Phase 9: Extended endpoints for rich frontend integration
# =========================================================


def _load_json_artifact(filename: str):
    """Load a JSON file from the artifacts directory."""
    path = ARTIFACTS_DIR / filename
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@app.get("/artifacts/metrics", tags=["Artifacts"])
async def get_artifact_metrics():
    """Serve model_comparison.json with all validation/test metrics."""
    data = _load_json_artifact("model_comparison.json")
    if data is None:
        raise HTTPException(status_code=404, detail="model_comparison.json not found")
    return data


@app.get("/artifacts/metadata", tags=["Artifacts"])
async def get_artifact_metadata():
    """Serve model_metadata.json complete."""
    data = _load_json_artifact("model_metadata.json")
    if data is None:
        # Fallback to v1
        data = _load_json_artifact("model_metadata_v1.json")
    if data is None:
        raise HTTPException(status_code=404, detail="model_metadata.json not found")
    return data


@app.get("/artifacts/report", tags=["Artifacts"])
async def get_artifact_report():
    """Serve model_report.md as text."""
    path = ARTIFACTS_DIR / "model_report.md"
    if not path.exists():
        raise HTTPException(status_code=404, detail="model_report.md not found")
    content = path.read_text(encoding="utf-8")
    return {"content": content, "format": "markdown"}


@app.get("/artifacts/fairness", tags=["Artifacts"])
async def get_artifact_fairness():
    """Serve fairness_analysis.json with subgroup metrics."""
    data = _load_json_artifact("fairness_analysis.json")
    if data is None:
        raise HTTPException(status_code=404, detail="fairness_analysis.json not found")
    return data


# -------------------------------------------------------------------
# EDA (Exploratory Data Analysis) endpoint
# -------------------------------------------------------------------


@app.get("/analysis/eda", tags=["Analysis"])
async def get_eda():
    """
    Return exploratory data analysis computed from data_card.json
    and modeling_dataset.parquet.
    """
    data_dir = BASE_DIR / "data" / "processed"
    card_path = data_dir / "data_card.json"
    parquet_path = data_dir / "modeling_dataset.parquet"

    if not card_path.exists():
        raise HTTPException(status_code=404, detail="data_card.json not found")

    with open(card_path, "r", encoding="utf-8") as f:
        data_card = json.load(f)

    # --- Dataset overview ---
    modeling = data_card.get("modeling_dataset", {})
    interim = data_card.get("interim_datasets", {})
    year_counts = {yr: info.get("n_rows", 0) for yr, info in interim.items()}

    overview = {
        "total_samples": modeling.get("n_rows", 0),
        "n_features": modeling.get("n_features", 0),
        "target": modeling.get("target_column", "em_risco_2024"),
        "target_distribution": modeling.get("target_distribution", {}),
        "years": sorted(interim.keys()),
        "year_counts": year_counts,
        "features": modeling.get("features", []),
    }

    # --- Missing data ---
    missing_features = modeling.get("missing_features", {})
    n_total = modeling.get("n_rows", 1)
    missing_data = []
    for feat, cnt in missing_features.items():
        missing_data.append(
            {
                "feature": feat,
                "count": cnt,
                "percentage": round(cnt / n_total * 100, 1) if n_total else 0,
            }
        )
    missing_data.sort(key=lambda x: x["count"], reverse=True)

    # --- Feature statistics from parquet ---
    feature_stats = []
    correlations = []

    if parquet_path.exists():
        try:
            df = pd.read_parquet(parquet_path)
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

            # Descriptive stats
            for col in numeric_cols:
                s = df[col].dropna()
                if len(s) == 0:
                    continue
                hist_values, hist_edges = np.histogram(s, bins=10)
                histogram = []
                for i in range(len(hist_values)):
                    histogram.append(
                        {
                            "bin": f"{hist_edges[i]:.1f}-{hist_edges[i+1]:.1f}",
                            "count": int(hist_values[i]),
                        }
                    )
                feature_stats.append(
                    {
                        "name": col,
                        "mean": round(float(s.mean()), 3),
                        "std": round(float(s.std()), 3),
                        "min": round(float(s.min()), 3),
                        "max": round(float(s.max()), 3),
                        "q25": round(float(s.quantile(0.25)), 3),
                        "q50": round(float(s.quantile(0.50)), 3),
                        "q75": round(float(s.quantile(0.75)), 3),
                        "missing": int(df[col].isna().sum()),
                        "histogram": histogram,
                    }
                )

            # Correlation matrix (top features only)
            target_col = modeling.get("target_column", "em_risco_2024")
            feat_cols = [c for c in modeling.get("features", []) if c in numeric_cols]
            if target_col in df.columns:
                feat_cols_with_target = feat_cols + [target_col]
            else:
                feat_cols_with_target = feat_cols

            if feat_cols_with_target:
                corr_df = df[feat_cols_with_target].corr()
                for row_name in corr_df.index:
                    for col_name in corr_df.columns:
                        val = corr_df.loc[row_name, col_name]
                        if not np.isnan(val):
                            correlations.append(
                                {
                                    "x": col_name,
                                    "y": row_name,
                                    "value": round(float(val), 3),
                                }
                            )
        except Exception as e:
            logger.warning(f"EDA parquet read error: {e}")

    # --- Year-over-year missing data comparison ---
    year_missing = {}
    for yr, info in interim.items():
        m = info.get("missing_by_column", {})
        n = info.get("n_rows", 1)
        total_missing = sum(m.values())
        total_cells = n * info.get("n_columns", 1)
        year_missing[yr] = {
            "n_rows": n,
            "n_columns": info.get("n_columns", 0),
            "total_missing_cells": total_missing,
            "missing_percentage": round(total_missing / total_cells * 100, 1)
            if total_cells
            else 0,
        }

    return {
        "overview": overview,
        "missing_data": missing_data,
        "feature_stats": feature_stats,
        "correlations": correlations,
        "year_missing": year_missing,
    }


@app.get("/inference/history", tags=["Inference"])
async def get_inference_history(
    limit: int = Query(default=200, ge=1, le=1000),
):
    """Return last N inference events from drift store (no PII)."""
    events = drift_store.read_events(limit=limit)
    return {
        "events": events,
        "total": len(events),
    }


@app.get("/drift/status", tags=["Drift"])
async def get_drift_status():
    """
    Compute simplified PSI-like drift status per feature.
    Compares last 50 events vs first 50 events (baseline).
    Returns green/yellow/red status per feature.
    """
    events = drift_store.read_events(limit=500)

    if len(events) < 10:
        return {
            "status": "insufficient_data",
            "message": "Need at least 10 inference events to compute drift",
            "features": {},
            "score_drift": {"status": "insufficient_data", "psi": 0.0},
            "overall_status": "green",
        }

    # Split into baseline (first half) and current (second half)
    mid = len(events) // 2
    baseline_events = events[:mid]
    current_events = events[mid:]

    # Aggregate feature distributions
    def aggregate_feature_dist(event_list):
        agg = {}
        for ev in event_list:
            batch_stats = ev.get("batch_stats", {})
            feat_dist = batch_stats.get("feature_distribution", {})
            for feat, bins in feat_dist.items():
                if feat not in agg:
                    agg[feat] = {"low": 0, "medium": 0, "high": 0}
                for b in ("low", "medium", "high"):
                    agg[feat][b] += bins.get(b, 0)
        return agg

    baseline_dist = aggregate_feature_dist(baseline_events)
    current_dist = aggregate_feature_dist(current_events)

    # Simple PSI calculation
    def compute_psi(base_bins, curr_bins):
        total_base = sum(base_bins.values()) or 1
        total_curr = sum(curr_bins.values()) or 1
        psi = 0.0
        for b in ("low", "medium", "high"):
            p = max(base_bins.get(b, 0) / total_base, 0.0001)
            q = max(curr_bins.get(b, 0) / total_curr, 0.0001)
            psi += (p - q) * np.log(p / q)
        return abs(psi)

    feature_status = {}
    all_features = set(list(baseline_dist.keys()) + list(current_dist.keys()))

    for feat in all_features:
        base = baseline_dist.get(feat, {"low": 1, "medium": 1, "high": 1})
        curr = current_dist.get(feat, {"low": 1, "medium": 1, "high": 1})
        psi = compute_psi(base, curr)
        if psi < 0.1:
            status = "green"
        elif psi < 0.25:
            status = "yellow"
        else:
            status = "red"
        feature_status[feat] = {
            "psi": round(psi, 4),
            "status": status,
            "baseline_dist": base,
            "current_dist": curr,
        }

    # Score drift
    def aggregate_score_bins(event_list):
        bins = {"low": 0, "medium": 0, "high": 0}
        for ev in event_list:
            pred_summary = ev.get("prediction_summary", {})
            score_bins = pred_summary.get("score_bins", {})
            for b in ("low", "medium", "high"):
                bins[b] += score_bins.get(b, 0)
        return bins

    base_scores = aggregate_score_bins(baseline_events)
    curr_scores = aggregate_score_bins(current_events)
    score_psi = compute_psi(base_scores, curr_scores)

    if score_psi < 0.1:
        score_status = "green"
    elif score_psi < 0.25:
        score_status = "yellow"
    else:
        score_status = "red"

    # Missing rate comparison
    def aggregate_missing(event_list):
        missing = {}
        n_events = len(event_list)
        for ev in event_list:
            batch_stats = ev.get("batch_stats", {})
            miss_summary = batch_stats.get("missing_summary", {})
            for feat, count in miss_summary.items():
                missing[feat] = missing.get(feat, 0) + count
        return {k: v / max(n_events, 1) for k, v in missing.items()}

    baseline_missing = aggregate_missing(baseline_events)
    current_missing = aggregate_missing(current_events)

    # Overall status
    statuses = [f["status"] for f in feature_status.values()] + [score_status]
    if "red" in statuses:
        overall = "red"
    elif "yellow" in statuses:
        overall = "yellow"
    else:
        overall = "green"

    return {
        "status": "ok",
        "features": feature_status,
        "score_drift": {
            "status": score_status,
            "psi": round(score_psi, 4),
            "baseline_dist": base_scores,
            "current_dist": curr_scores,
        },
        "missing_rates": {
            "baseline": baseline_missing,
            "current": current_missing,
        },
        "overall_status": overall,
        "n_baseline_events": len(baseline_events),
        "n_current_events": len(current_events),
    }


@app.get("/audit/recent", tags=["Audit"])
async def get_recent_audit(
    limit: int = Query(default=50, ge=1, le=500),
    action: Optional[str] = Query(default=None),
):
    """Return recent audit trail records."""
    records = audit_trail.get_records(action=action, limit=limit)
    summary = audit_trail.get_summary()
    return {
        "records": records,
        "summary": summary,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=PORT)
