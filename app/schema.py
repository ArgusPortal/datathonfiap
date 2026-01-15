"""
Schemas Pydantic para validação de requests e responses da API.
"""

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.config import EXTRA_FEATURE_POLICY


class StudentFeatures(BaseModel):
    """
    Features de entrada para um estudante.
    Todos os campos são opcionais para permitir flexibilidade.
    """
    model_config = ConfigDict(extra="allow")
    
    # Indicadores de desempenho
    iaa_2023: Optional[float] = None  # Autoavaliação
    ian_2023: Optional[float] = None  # Aprendizagem
    ida_2023: Optional[float] = None  # Desenvolvimento Acadêmico
    ieg_2023: Optional[float] = None  # Engajamento
    ipp_2023: Optional[float] = None  # Psicopedagógico
    ips_2023: Optional[float] = None  # Psicossocial
    ipv_2023: Optional[float] = None  # Ponto de Virada
    
    # Fase e idade
    fase_2023: Optional[float] = None
    idade_2023: Optional[float] = None
    
    # Instituição
    instituicao_2023: Optional[str] = None
    
    # Features derivadas
    media_indicadores: Optional[float] = None
    std_indicadores: Optional[float] = None
    max_indicador: Optional[float] = None
    min_indicador: Optional[float] = None
    range_indicadores: Optional[float] = None


class PredictRequest(BaseModel):
    """Request para predição (single ou batch)."""
    
    instances: List[Dict[str, Any]]
    
    @field_validator("instances")
    @classmethod
    def validate_instances(cls, v: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not v:
            raise ValueError("instances não pode ser vazio")
        if len(v) > 1000:
            raise ValueError("Máximo de 1000 instâncias por request")
        return v


class PredictionResult(BaseModel):
    """Resultado de predição para uma instância."""
    
    risk_score: float
    risk_label: int
    model_version: str


class PredictResponse(BaseModel):
    """Response da predição."""
    
    predictions: List[PredictionResult]
    request_id: str
    processing_time_ms: float


class HealthResponse(BaseModel):
    """Response do health check."""
    
    status: str
    model_loaded: bool
    model_version: Optional[str] = None
    uptime_seconds: float


class MetadataResponse(BaseModel):
    """Response do endpoint de metadata."""
    
    model_version: str
    model_family: str
    threshold: float
    expected_features: List[str]
    calibration: Optional[str] = None
    created_at: Optional[str] = None


class ErrorResponse(BaseModel):
    """Response de erro."""
    
    detail: str
    request_id: Optional[str] = None


def validate_features(
    features: Dict[str, Any],
    expected_features: List[str],
    extra_policy: str = EXTRA_FEATURE_POLICY
) -> Dict[str, Any]:
    """
    Valida e prepara features para predição.
    
    Args:
        features: Features recebidas
        expected_features: Features esperadas pelo modelo
        extra_policy: "reject" rejeita features extras, "ignore" ignora
        
    Returns:
        Features validadas e ordenadas
        
    Raises:
        ValueError: Se houver features extras e policy="reject"
    """
    # Verifica features extras
    extra_features = set(features.keys()) - set(expected_features)
    
    # Remove campos de ID que não devem ir para o modelo
    id_fields = {'ra', 'id', 'nome', 'estudante_id', 'student_id'}
    extra_features = extra_features - id_fields
    
    if extra_features and extra_policy == "reject":
        raise ValueError(f"Features não esperadas: {sorted(extra_features)}")
    
    # Prepara features na ordem correta
    validated = {}
    for feat in expected_features:
        validated[feat] = features.get(feat)
    
    return validated


def validate_batch_features(
    instances: List[Dict[str, Any]],
    expected_features: List[str],
    extra_policy: str = EXTRA_FEATURE_POLICY
) -> List[Dict[str, Any]]:
    """
    Valida um batch de instâncias.
    
    Args:
        instances: Lista de dicionários de features
        expected_features: Features esperadas pelo modelo
        extra_policy: Política para features extras
        
    Returns:
        Lista de features validadas
    """
    validated = []
    for i, inst in enumerate(instances):
        try:
            validated.append(validate_features(inst, expected_features, extra_policy))
        except ValueError as e:
            raise ValueError(f"Instância {i}: {e}")
    return validated
