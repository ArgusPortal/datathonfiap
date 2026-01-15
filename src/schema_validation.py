"""
Schema Validation - valida inputs de treino e inferência.

Uso:
    from src.schema_validation import validate_input_schema
    validate_input_schema(df, signature, mode="inference")
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import numpy as np
import pandas as pd

logger = logging.getLogger("schema_validation")

# Features esperadas v1.x
EXPECTED_FEATURES_V1 = [
    "fase_2023", "iaa_2023", "ian_2023", "ida_2023", "idade_2023",
    "ieg_2023", "instituicao_2023", "ipp_2023", "ips_2023", "ipv_2023",
    "max_indicador", "media_indicadores", "min_indicador",
    "range_indicadores", "std_indicadores"
]

# Ranges esperados (soft validation)
FEATURE_RANGES = {
    "fase_2023": (0, 8),
    "iaa_2023": (0, 10),
    "ian_2023": (0, 10),
    "ida_2023": (0, 10),
    "idade_2023": (5, 25),
    "ieg_2023": (0, 10),
    "ipp_2023": (0, 10),
    "ips_2023": (0, 10),
    "ipv_2023": (0, 10),
    "max_indicador": (0, 10),
    "media_indicadores": (0, 10),
    "min_indicador": (0, 10),
    "range_indicadores": (0, 10),
    "std_indicadores": (0, 5),
}

# Campos PII proibidos
PII_FIELDS = {"ra", "nome", "student_id", "email", "telefone", "endereco", "id"}

# Target para treino
TARGET_COL = "em_risco_2024"


class SchemaValidationError(ValueError):
    """Erro de validação de schema."""
    pass


def get_expected_features(signature: Optional[Dict[str, Any]] = None) -> List[str]:
    """Obtém lista de features esperadas do signature ou usa default."""
    if signature and "input_schema" in signature:
        return list(signature["input_schema"].keys())
    return EXPECTED_FEATURES_V1.copy()


def validate_input_schema(
    df: pd.DataFrame,
    signature: Optional[Dict[str, Any]] = None,
    mode: str = "inference",
    extra_policy: str = "reject",
    check_ranges: bool = True,
    check_pii: bool = True
) -> None:
    """
    Valida schema do DataFrame de entrada.
    
    Args:
        df: DataFrame a validar
        signature: Signature do modelo com input_schema
        mode: "inference" ou "training"
        extra_policy: "reject" ou "ignore" para features extras
        check_ranges: Se True, valida ranges das features
        check_pii: Se True, valida ausência de campos PII
        
    Raises:
        SchemaValidationError: Se validação falhar
    """
    errors = []
    warnings = []
    
    expected_features = get_expected_features(signature)
    received_features = set(df.columns)
    expected_set = set(expected_features)
    
    # 1. Verifica features faltantes
    missing = expected_set - received_features
    if missing:
        errors.append(f"Features obrigatórias faltando: {sorted(missing)}")
    
    # 2. Verifica features extras
    extra = received_features - expected_set - PII_FIELDS
    if mode == "inference":
        extra = extra - {TARGET_COL}  # Target não é extra em inferência
    
    if extra:
        if extra_policy == "reject":
            errors.append(f"Features extras não permitidas: {sorted(extra)}")
        else:
            warnings.append(f"Features extras ignoradas: {sorted(extra)}")
    
    # 3. Verifica PII (sempre erro)
    if check_pii:
        pii_found = received_features & PII_FIELDS
        if pii_found:
            errors.append(f"Campos PII detectados (proibidos): {sorted(pii_found)}")
    
    # 4. Verifica target em treino
    if mode == "training":
        if TARGET_COL not in received_features:
            errors.append(f"Target '{TARGET_COL}' obrigatório para treino")
        else:
            # Valida valores do target
            target_values = df[TARGET_COL].dropna().unique()
            invalid_target = set(target_values) - {0, 1, 0.0, 1.0}
            if invalid_target:
                errors.append(f"Target deve ser binário (0/1), encontrado: {invalid_target}")
    
    # 5. Verifica tipos básicos
    for feature in expected_features:
        if feature in df.columns:
            dtype = df[feature].dtype
            if not (np.issubdtype(dtype, np.number) or dtype == object):
                warnings.append(f"Feature '{feature}' tem tipo inesperado: {dtype}")
    
    # 6. Verifica ranges (soft - apenas warnings)
    if check_ranges:
        for feature, (min_val, max_val) in FEATURE_RANGES.items():
            if feature in df.columns:
                col = pd.to_numeric(df[feature], errors="coerce")
                out_of_range = ((col < min_val) | (col > max_val)).sum()
                if out_of_range > 0:
                    warnings.append(
                        f"Feature '{feature}': {out_of_range} valores fora do range [{min_val}, {max_val}]"
                    )
    
    # Log warnings
    for w in warnings:
        logger.warning(w)
    
    # Raise se houver erros
    if errors:
        error_msg = "Validação de schema falhou:\n" + "\n".join(f"  - {e}" for e in errors)
        logger.error(error_msg)
        raise SchemaValidationError(error_msg)
    
    logger.info(f"Schema validado com sucesso (mode={mode}, features={len(expected_features)})")


def validate_inference_batch(
    instances: List[Dict[str, Any]],
    signature: Optional[Dict[str, Any]] = None,
    extra_policy: str = "reject"
) -> List[str]:
    """
    Valida batch de inferência (lista de dicts).
    
    Returns:
        Lista de warnings (vazia se ok)
        
    Raises:
        SchemaValidationError: Se validação crítica falhar
    """
    if not instances:
        raise SchemaValidationError("Batch vazio")
    
    df = pd.DataFrame(instances)
    validate_input_schema(df, signature, mode="inference", extra_policy=extra_policy)
    
    return []


def validate_training_data(
    df: pd.DataFrame,
    signature: Optional[Dict[str, Any]] = None
) -> None:
    """
    Valida dados de treino.
    
    Raises:
        SchemaValidationError: Se validação falhar
    """
    validate_input_schema(df, signature, mode="training", extra_policy="ignore")
    
    # Validações extras para treino
    if len(df) < 100:
        logger.warning(f"Dataset de treino muito pequeno: {len(df)} amostras")
    
    # Verifica balanceamento
    if TARGET_COL in df.columns:
        class_counts = df[TARGET_COL].value_counts()
        minority_ratio = class_counts.min() / class_counts.sum()
        if minority_ratio < 0.1:
            logger.warning(f"Dataset desbalanceado: classe minoritária = {minority_ratio:.1%}")
