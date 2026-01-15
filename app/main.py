"""
FastAPI application for school dropout risk prediction.

Endpoints:
    - POST /predict: predict dropout risk for a student
    - GET /health: health check
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator
import joblib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Datathon FIAP - Dropout Risk Prediction API",
    description="API for predicting school dropout risk for Passos Mágicos students",
    version="0.1.0",
)

# Model loading (placeholder - will load real model in later phases)
MODEL_PATH = Path(__file__).parent / "model" / "model.pkl"
MODEL_METADATA_PATH = Path(__file__).parent / "model" / "model_metadata.json"

# Global model holder
_model = None
_model_version = "v0.1.0-placeholder"


def load_model():
    """Load trained model. Falls back to dummy model if not found."""
    global _model, _model_version
    
    try:
        if MODEL_PATH.exists():
            _model = joblib.load(MODEL_PATH)
            logger.info(f"Model loaded from {MODEL_PATH}")
        else:
            logger.warning(f"Model file not found at {MODEL_PATH}. Using dummy predictor.")
            _model = DummyModel()
            
        # Load metadata if exists
        if MODEL_METADATA_PATH.exists():
            import json
            with open(MODEL_METADATA_PATH, 'r') as f:
                metadata = json.load(f)
                _model_version = metadata.get('version', _model_version)
                
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        _model = DummyModel()


class DummyModel:
    """Placeholder model for development phase."""
    
    def predict_proba(self, X):
        """Returns dummy probabilities."""
        import numpy as np
        n = len(X) if isinstance(X, list) else 1
        # Return dummy probabilities [P(class=0), P(class=1)]
        return np.array([[0.4, 0.6]] * n)


# Load model on startup
@app.on_event("startup")
async def startup_event():
    load_model()
    logger.info("API startup complete")


# Request/Response models
class StudentFeatures(BaseModel):
    """Features for a single student at year t."""
    
    inde_ano_t: float = Field(..., description="INDE score for year t")
    ian_ano_t: float = Field(..., description="IAN score for year t")
    taxa_presenca_ano_t: float = Field(..., ge=0.0, le=1.0, description="Attendance rate [0-1]")
    fase_programa: int = Field(..., ge=0, le=7, description="Program phase [0-7]")
    # Add more features as defined in data contract
    
    @field_validator('inde_ano_t', 'ian_ano_t')
    @classmethod
    def validate_scores(cls, v):
        if v < 0:
            raise ValueError('Score must be non-negative')
        return v


class PredictRequest(BaseModel):
    """Request schema for /predict endpoint."""
    
    estudante_id: str = Field(..., description="Student identifier (not used for prediction)")
    ano_base: int = Field(..., description="Base year (t)")
    features: StudentFeatures
    
    @field_validator('ano_base')
    @classmethod
    def validate_year(cls, v):
        if v < 2022 or v > 2030:
            raise ValueError('Year must be between 2022 and 2030')
        return v


class PredictResponse(BaseModel):
    """Response schema for /predict endpoint."""
    
    score: float = Field(..., ge=0.0, le=1.0, description="Risk score [0-1]")
    classe_predita: int = Field(..., description="Predicted class (0=not at risk, 1=at risk)")
    threshold: float = Field(default=0.5, description="Classification threshold")
    versao_modelo: str = Field(..., description="Model version")
    timestamp: str = Field(..., description="Prediction timestamp (ISO format)")


class HealthResponse(BaseModel):
    """Response schema for /health endpoint."""
    
    status: str
    model_loaded: bool
    version: str


# Endpoints
@app.get("/", tags=["root"])
async def root():
    """Root endpoint."""
    return {
        "message": "Datathon FIAP - Dropout Risk Prediction API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        model_loaded=_model is not None,
        version=_model_version
    )


@app.post("/predict", response_model=PredictResponse, tags=["prediction"])
async def predict_dropout_risk(request: PredictRequest):
    """
    Predict dropout risk for a student.
    
    Args:
        request: Student features and metadata
        
    Returns:
        PredictResponse with risk score and predicted class
        
    Raises:
        HTTPException: If model is not loaded or prediction fails
    """
    if _model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        # Extract features (in production, this would match training feature order)
        features_dict = request.features.model_dump()
        
        # For dummy model, convert to list format (in production, use proper feature vector)
        # This is a placeholder - real implementation would use feature engineering pipeline
        X = [[
            features_dict['inde_ano_t'],
            features_dict['ian_ano_t'],
            features_dict['taxa_presenca_ano_t'],
            features_dict['fase_programa']
        ]]
        
        # Get prediction
        proba = _model.predict_proba(X)
        score = float(proba[0][1])  # Probability of class 1 (at risk)
        
        # Apply threshold
        threshold = 0.5
        classe_predita = 1 if score >= threshold else 0
        
        # Log prediction (in production, log to structured logging system)
        logger.info(
            f"Prediction: student={request.estudante_id}, "
            f"year={request.ano_base}, score={score:.3f}, class={classe_predita}"
        )
        
        return PredictResponse(
            score=score,
            classe_predita=classe_predita,
            threshold=threshold,
            versao_modelo=_model_version,
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
        
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@app.get("/model/info", tags=["model"])
async def get_model_info():
    """Get information about the loaded model."""
    if _model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    return {
        "version": _model_version,
        "type": type(_model).__name__,
        "is_dummy": isinstance(_model, DummyModel),
        "metadata_path": str(MODEL_METADATA_PATH) if MODEL_METADATA_PATH.exists() else None
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
