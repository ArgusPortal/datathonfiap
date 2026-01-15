"""
Preprocessing: construção de ColumnTransformer para pipeline sklearn.
"""

import logging
from typing import Tuple, Optional, List
import pandas as pd
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer

logger = logging.getLogger(__name__)


# Colunas bloqueadas (IDs e leakage)
BLOCKED_COLUMNS = [
    'ra', 'nome', 'nome_anonimizado',
    'defasagem', 'em_risco', 'target',
    'ponto_virada', 'pedra', 'fase_ideal',
    'destaque_inde', 'destaque_ida', 'destaque_ieg', 'destaque_ipv',
    'rec_ava', 'rec_inde', 'rec_psicologia',
    'avaliador1', 'avaliador2', 'avaliador3', 'avaliador4',
    'rec_av1', 'rec_av2', 'rec_av3', 'rec_av4',
]


def validate_no_blocked_columns(columns: List[str], target_year: int = 2024) -> None:
    """Valida que não há colunas bloqueadas. Levanta exceção se encontrar."""
    violations = []
    
    # Padrões exatos de bloqueio (evita false positives como 'range_indicadores')
    exact_blocked = ['ra', 'nome', 'nome_anonimizado', 'target']
    prefix_blocked = ['defasagem', 'em_risco', 'ponto_virada', 'pedra', 'fase_ideal',
                      'destaque_', 'rec_', 'avaliador']
    
    for col in columns:
        col_lower = col.lower()
        
        # Verifica match exato
        if col_lower in exact_blocked:
            violations.append(f"{col} (exact match)")
            continue
        
        # Verifica prefixos
        for prefix in prefix_blocked:
            if col_lower.startswith(prefix):
                violations.append(f"{col} (prefix '{prefix}')")
                break
        
        # Colunas do ano do target = leakage temporal (exceto target column itself)
        if f"_{target_year}" in col and not col_lower.startswith('em_risco'):
            violations.append(f"{col} (data from target year {target_year})")
    
    if violations:
        raise ValueError(
            f"LEAKAGE DETECTADO! Colunas bloqueadas:\n" +
            "\n".join(f"  - {v}" for v in violations)
        )


def identify_column_types(df: pd.DataFrame, exclude_cols: List[str] = None) -> Tuple[List[str], List[str]]:
    """Identifica colunas numéricas e categóricas."""
    if exclude_cols is None:
        exclude_cols = []
    
    numeric_cols, categorical_cols = [], []
    
    for col in df.columns:
        if col in exclude_cols:
            continue
        if np.issubdtype(df[col].dtype, np.number):
            numeric_cols.append(col)
        else:
            # Tenta converter para numérico
            numeric_vals = pd.to_numeric(df[col], errors='coerce')
            if numeric_vals.notna().sum() / max(len(df), 1) > 0.8:
                numeric_cols.append(col)
            else:
                categorical_cols.append(col)
    
    return numeric_cols, categorical_cols


def build_preprocessor(
    X: pd.DataFrame,
    target_year: int = 2024,
    numeric_cols: List[str] = None,
    categorical_cols: List[str] = None
) -> Tuple[ColumnTransformer, List[str], List[str]]:
    """
    Constrói ColumnTransformer para preprocessing.
    
    Returns:
        Tuple[preprocessor, numeric_cols, categorical_cols]
    """
    validate_no_blocked_columns(X.columns.tolist(), target_year)
    
    if numeric_cols is None or categorical_cols is None:
        auto_num, auto_cat = identify_column_types(X)
        numeric_cols = numeric_cols or auto_num
        categorical_cols = categorical_cols or auto_cat
    
    numeric_transformer = Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])
    
    categorical_transformer = Pipeline([
        ('imputer', SimpleImputer(strategy='constant', fill_value='missing')),
        ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
    ])
    
    transformers = []
    if numeric_cols:
        transformers.append(('num', numeric_transformer, numeric_cols))
    if categorical_cols:
        transformers.append(('cat', categorical_transformer, categorical_cols))
    
    preprocessor = ColumnTransformer(
        transformers=transformers,
        remainder='drop',
        verbose_feature_names_out=False
    )
    
    return preprocessor, numeric_cols, categorical_cols


def prepare_features(
    df: pd.DataFrame,
    target_col: str,
    id_cols: List[str] = None,
    target_year: int = 2024
) -> Tuple[pd.DataFrame, pd.Series]:
    """Prepara features e target a partir do DataFrame."""
    if id_cols is None:
        id_cols = ['ra']
    
    y = df[target_col].copy()
    cols_to_drop = [target_col] + [c for c in id_cols if c in df.columns]
    X = df.drop(columns=cols_to_drop)
    
    validate_no_blocked_columns(X.columns.tolist(), target_year)
    return X, y


def convert_mixed_types(df: pd.DataFrame) -> pd.DataFrame:
    """Converte colunas com tipos mistos para tipos consistentes."""
    df = df.copy()
    for col in df.columns:
        if df[col].dtype == 'object':
            numeric_converted = pd.to_numeric(df[col], errors='coerce')
            non_null_orig = df[col].notna().sum()
            non_null_num = numeric_converted.notna().sum()
            if non_null_orig > 0 and non_null_num >= non_null_orig * 0.7:
                df[col] = numeric_converted
    return df
