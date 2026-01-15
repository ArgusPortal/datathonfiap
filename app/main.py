"""
API FastAPI para predição de risco de defasagem escolar.
Passos Mágicos - Datathon FIAP 2025
Phase 8: Production Hardening - Security, Metrics, Audit
"""

import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, PlainTextResponse

from app.config import (
    APP_NAME,
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
from app.security import SecurityMiddleware, rate_limiter
from app.metrics import metrics
from app.audit import audit_trail, init_model_lineage, create_inference_audit_record, hash_dict
from app.privacy import sanitize_dict_for_logging, aggregate_features

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
            f"Modelo carregado com sucesso",
            extra={
                "model_version": model_manager.version,
                "threshold": model_manager.threshold,
                "n_features": len(model_manager.expected_features),
            }
        )
        
        # Phase 8: Initialize model lineage and metrics
        init_model_lineage(str(MODEL_PATH), model_manager.version)
        metrics.set_model_info(model_manager.version)
        
        if AUDIT_ENABLED:
            audit_trail.add_record("startup", details={
                "model_version": model_manager.version,
                "model_path": str(MODEL_PATH),
            })
        
    except Exception as e:
        logger.error(f"Falha ao carregar modelo: {e}")
        raise
    
    yield
    
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
    warnings_list = []
    
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
                input_hash=hash_dict({"instances": [dict(i) for i in payload.instances]}),
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
