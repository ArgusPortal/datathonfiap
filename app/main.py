"""
API FastAPI para predição de risco de defasagem escolar.
Passos Mágicos - Datathon FIAP 2025
"""

import time
from contextlib import asynccontextmanager

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from app.config import (
    APP_NAME,
    EXTRA_FEATURE_POLICY,
    LOG_LEVEL,
    METADATA_PATH,
    MODEL_PATH,
    PORT,
    SIGNATURE_PATH,
)
from app.drift_store import drift_store
from app.logging_config import RequestLogger, generate_request_id, setup_logging
from app.model_loader import ModelManager
from app.schema import (
    ErrorResponse,
    HealthResponse,
    MetadataResponse,
    PredictionResult,
    PredictRequest,
    PredictResponse,
    validate_batch_features,
)

# Setup logging
logger = setup_logging(LOG_LEVEL)

# Model manager global
model_manager = ModelManager()

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
    except Exception as e:
        logger.error(f"Falha ao carregar modelo: {e}")
        raise
    
    yield
    
    logger.info("Encerrando aplicação...")


# Cria app FastAPI
app = FastAPI(
    title=APP_NAME,
    description="API para predição de risco de defasagem escolar - Passos Mágicos",
    version="1.0.0",
    lifespan=lifespan,
)


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
        request.state.logger.log_error(str(e), latency_ms=latency_ms)
        raise


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check do serviço.
    Retorna status do modelo e uptime.
    """
    uptime = time.time() - _startup_time
    
    return HealthResponse(
        status="healthy" if model_manager.model is not None else "degraded",
        model_loaded=model_manager.model is not None,
        model_version=model_manager.version,
        uptime_seconds=round(uptime, 2),
    )


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


@app.post("/predict", response_model=PredictResponse, tags=["Prediction"])
async def predict(request: Request, payload: PredictRequest):
    """
    Realiza predição de risco de defasagem.
    
    Aceita batch de instâncias (até 1000).
    Retorna score de risco (0-1) e label binário (0/1).
    """
    request_id = getattr(request.state, "request_id", generate_request_id())
    start_time = time.time()
    
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
        
        # Log drift stats (assíncrono, não bloqueia)
        try:
            drift_store.log_event(
                request_id=request_id,
                model_version=model_manager.version,
                instances=payload.instances,
                predictions=[p.model_dump() for p in predictions],
            )
        except Exception as e:
            logger.warning(f"Falha ao logar drift: {e}")
        
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
