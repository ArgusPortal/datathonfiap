"""
Feature Engineering: seleção e criação de features para modelagem.
"""

import logging
from typing import List, Optional, Dict, Any
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


# Features permitidas no MVP
ALLOWED_FEATURES = [
    'instituicao', 'idade', 'fase', 'genero', 'anos_pm', 'bolsista',
    'inde', 'ian', 'ida', 'ieg', 'iaa', 'ips', 'ipp', 'ipv', 'ipm',
    'indicador_nutricional',
]


def make_features(df: pd.DataFrame, config: Dict[str, Any] = None) -> pd.DataFrame:
    """
    Aplica engenharia de features no DataFrame.
    
    Args:
        df: DataFrame com features brutas
        config: Dicionário de configuração (opcional)
            - create_deltas: bool (criar deltas 22→23)
            - allowed_features: lista de prefixos permitidos
            
    Returns:
        DataFrame com features processadas
    """
    if config is None:
        config = {}
    
    df = df.copy()
    
    # Identifica colunas de features (exclui target e IDs)
    exclude_patterns = ['em_risco', 'target', 'ra', 'nome']
    feature_cols = [c for c in df.columns 
                    if not any(p in c.lower() for p in exclude_patterns)]
    
    # Cria deltas se solicitado e colunas existirem
    if config.get('create_deltas', False):
        df = create_delta_features(df)
    
    # Cria features de risco compostas
    df = create_risk_composites(df)
    
    logger.info(f"Features após engenharia: {len(df.columns)} colunas")
    return df


def create_delta_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cria features de delta (variação entre anos).
    Busca pares de colunas como inde_2022 e inde_2023.
    """
    df = df.copy()
    
    # Busca pares de colunas por ano
    cols_22 = [c for c in df.columns if '_22' in c or '_2022' in c]
    cols_23 = [c for c in df.columns if '_23' in c or '_2023' in c]
    
    for col_22 in cols_22:
        # Extrai nome base
        base_name = col_22.replace('_22', '').replace('_2022', '')
        
        # Busca correspondente em 2023
        col_23_candidates = [c for c in cols_23 if base_name in c]
        
        if col_23_candidates:
            col_23 = col_23_candidates[0]
            
            # Verifica se ambas são numéricas
            if pd.api.types.is_numeric_dtype(df[col_22]) and pd.api.types.is_numeric_dtype(df[col_23]):
                delta_col = f"delta_{base_name}_22_23"
                df[delta_col] = df[col_23] - df[col_22]
                logger.debug(f"Criado delta: {delta_col}")
    
    return df


def create_risk_composites(df: pd.DataFrame) -> pd.DataFrame:
    """Cria features compostas de risco."""
    df = df.copy()
    
    # Identifica colunas de indicadores
    indicator_cols = [c for c in df.columns 
                      if any(ind in c.lower() for ind in ['ian', 'ida', 'ieg', 'iaa', 'ips', 'ipp', 'ipv'])]
    
    # Média dos indicadores disponíveis
    numeric_indicators = []
    for col in indicator_cols:
        if pd.api.types.is_numeric_dtype(df[col]):
            numeric_indicators.append(col)
    
    if numeric_indicators:
        df['media_indicadores'] = df[numeric_indicators].mean(axis=1)
        df['min_indicador'] = df[numeric_indicators].min(axis=1)
        df['std_indicadores'] = df[numeric_indicators].std(axis=1)
    
    return df


def select_features_by_prefix(
    df: pd.DataFrame, 
    allowed_prefixes: List[str] = None,
    exclude_cols: List[str] = None
) -> List[str]:
    """
    Seleciona colunas baseado em prefixos permitidos.
    
    Args:
        df: DataFrame
        allowed_prefixes: Lista de prefixos de colunas permitidas
        exclude_cols: Colunas a excluir explicitamente
        
    Returns:
        Lista de nomes de colunas selecionadas
    """
    if allowed_prefixes is None:
        allowed_prefixes = ALLOWED_FEATURES
    
    if exclude_cols is None:
        exclude_cols = []
    
    selected = []
    
    for col in df.columns:
        if col in exclude_cols:
            continue
        
        col_lower = col.lower()
        # Verifica se começa com algum prefixo permitido
        for prefix in allowed_prefixes:
            if prefix.lower() in col_lower:
                selected.append(col)
                break
    
    return selected
