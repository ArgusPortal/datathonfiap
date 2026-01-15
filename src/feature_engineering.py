"""
Feature Engineering: seleção e criação de features para modelagem.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


# Features permitidas no MVP
ALLOWED_FEATURES = [
    'instituicao', 'idade', 'fase', 'genero', 'anos_pm', 'bolsista',
    'inde', 'ian', 'ida', 'ieg', 'iaa', 'ips', 'ipp', 'ipv', 'ipm',
    'indicador_nutricional',
]

# Indicadores para deltas
INDICATOR_PREFIXES = ['ian', 'ida', 'ieg', 'iaa', 'ips', 'ipp', 'ipv', 'inde']


def get_feature_list(df: pd.DataFrame, exclude_patterns: List[str] = None) -> List[str]:
    """
    Retorna lista ordenada de features finais para modelagem.
    
    Args:
        df: DataFrame com features processadas
        exclude_patterns: Padrões a excluir (default: target, IDs)
        
    Returns:
        Lista ordenada de nomes de features
    """
    if exclude_patterns is None:
        exclude_patterns = ['em_risco', 'target', 'ra', 'nome', 'defasagem']
    
    features = [c for c in df.columns 
                if not any(p in c.lower() for p in exclude_patterns)]
    return sorted(features)


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
    
    # Cria features indicadoras de missing
    df = create_missing_indicators(df)
    
    # Cria deltas se colunas existirem (sempre tenta)
    df = create_delta_features(df)
    
    # Cria feature de tempo na instituição
    df = create_tenure_feature(df)
    
    # Cria features de risco compostas
    df = create_risk_composites(df)
    
    logger.info(f"Features após engenharia: {len(df.columns)} colunas")
    return df


def create_missing_indicators(df: pd.DataFrame, 
                              columns: List[str] = None,
                              min_missing_pct: float = 0.05) -> pd.DataFrame:
    """
    Cria features binárias indicando valores ausentes.
    
    Útil quando missing é informativo (ex: aluno sem nota em IDA 
    pode indicar que não fez avaliação).
    
    Args:
        df: DataFrame com features
        columns: Lista de prefixos de colunas para criar indicadores
        min_missing_pct: Percentual mínimo de missing para criar indicador (default 5%)
        
    Returns:
        DataFrame com features de missing adicionadas
    """
    df = df.copy()
    
    if columns is None:
        # Indicadores numéricos que podem ter missing informativo
        columns = ['ida', 'ieg', 'iaa', 'ips', 'ipp', 'ipv']
    
    indicators_created = []
    for prefix in columns:
        # Busca colunas com este prefixo
        matching = [c for c in df.columns 
                    if c.lower().startswith(prefix.lower()) and 
                    not c.endswith('_missing')]
        
        for col in matching:
            missing_pct = df[col].isna().mean()
            if missing_pct >= min_missing_pct:
                indicator_name = f"{col}_missing"
                df[indicator_name] = df[col].isna().astype(int)
                indicators_created.append(f"{indicator_name} ({missing_pct:.1%})")
    
    if indicators_created:
        logger.info(f"Missing indicators criados: {indicators_created}")
    
    return df


def create_tenure_feature(df: pd.DataFrame, 
                          reference_year: int = 2023) -> pd.DataFrame:
    """
    Cria feature de anos na instituição Passos Mágicos.
    
    Args:
        df: DataFrame com features
        reference_year: Ano de referência para cálculo
        
    Returns:
        DataFrame com feature anos_pm adicionada
    """
    df = df.copy()
    
    # Procura coluna de ano de ingresso
    ano_ingresso_cols = [c for c in df.columns 
                         if 'ano_ingresso' in c.lower() or 'ano ingresso' in c.lower()]
    
    if ano_ingresso_cols:
        col = ano_ingresso_cols[0]
        if pd.api.types.is_numeric_dtype(df[col]):
            # Determina ano de referência baseado nas features
            year_suffix = None
            for c in df.columns:
                if '_2023' in c:
                    year_suffix = 2023
                    break
                elif '_23' in c:
                    year_suffix = 2023
                    break
            
            ref_year = year_suffix or reference_year
            tenure_col = f'anos_pm_{ref_year}'
            df[tenure_col] = ref_year - df[col]
            # Limita a valores razoáveis (0 a 15 anos)
            df[tenure_col] = df[tenure_col].clip(lower=0, upper=15)
            logger.info(f"Feature criada: {tenure_col} (baseado em {col})")
    
    return df


def create_delta_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cria features de delta (variação entre anos).
    Busca pares de colunas como inde_2022/inde_22 e inde_2023/inde_23.
    Silenciosamente pula se colunas não existirem.
    """
    df = df.copy()
    deltas_created = []
    
    for prefix in INDICATOR_PREFIXES:
        # Busca mais flexível de colunas
        col_22 = None
        col_23 = None
        
        for c in df.columns:
            c_lower = c.lower()
            if c_lower.startswith(prefix.lower()):
                # Verifica se é coluna de 2022
                if '_22' in c or '_2022' in c or c_lower.endswith('_22'):
                    col_22 = c
                # Verifica se é coluna de 2023
                elif '_23' in c or '_2023' in c or c_lower.endswith('_23'):
                    col_23 = c
        
        if col_22 and col_23:
            if (pd.api.types.is_numeric_dtype(df[col_22]) and 
                pd.api.types.is_numeric_dtype(df[col_23])):
                delta_col = f"delta_{prefix}_22_23"
                df[delta_col] = df[col_23] - df[col_22]
                deltas_created.append(delta_col)
    
    if deltas_created:
        logger.info(f"Deltas criados: {deltas_created}")
    
    return df


def create_risk_composites(df: pd.DataFrame) -> pd.DataFrame:
    """Cria features compostas de risco baseadas em indicadores."""
    df = df.copy()
    
    # Identifica colunas de indicadores (preferir _2023)
    indicator_cols = []
    for prefix in INDICATOR_PREFIXES:
        matches = [c for c in df.columns 
                   if c.lower().startswith(prefix) and pd.api.types.is_numeric_dtype(df[c])]
        if matches:
            # Preferir 2023 se disponível
            pref = [c for c in matches if '_23' in c or '_2023' in c]
            indicator_cols.extend(pref if pref else matches[:1])
    
    if indicator_cols:
        df['media_indicadores'] = df[indicator_cols].mean(axis=1)
        df['min_indicador'] = df[indicator_cols].min(axis=1)
        df['max_indicador'] = df[indicator_cols].max(axis=1)
        df['std_indicadores'] = df[indicator_cols].std(axis=1)
        df['range_indicadores'] = df['max_indicador'] - df['min_indicador']
        logger.debug(f"Composites criados a partir de: {indicator_cols}")
    
    return df


def create_interaction_features(df: pd.DataFrame) -> pd.DataFrame:
    """Cria features de interação se colunas existirem."""
    df = df.copy()
    
    # Interação fase x indicadores (se existirem)
    if 'media_indicadores' in df.columns:
        fase_cols = [c for c in df.columns if 'fase' in c.lower() and pd.api.types.is_numeric_dtype(df[c])]
        for fase_col in fase_cols:
            df[f'fase_x_media'] = df[fase_col] * df['media_indicadores']
    
    return df


def select_features_by_prefix(
    df: pd.DataFrame, 
    allowed_prefixes: List[str] = None,
    exclude_cols: List[str] = None
) -> List[str]:
    """
    Seleciona colunas baseado em prefixos permitidos.
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
        for prefix in allowed_prefixes:
            if prefix.lower() in col_lower:
                selected.append(col)
                break
    
    return selected


def validate_features_for_year(df: pd.DataFrame, target_year: int) -> Tuple[List[str], List[str]]:
    """
    Valida features contra vazamento de dados do ano alvo.
    
    Returns:
        Tuple[valid_features, blocked_features]
    """
    valid = []
    blocked = []
    target_patterns = [f'_{target_year}', f'_{str(target_year)[-2:]}']
    blocked_prefixes = ['em_risco', 'defasagem', 'ponto_virada', 'pedra', 'fase_ideal']
    
    for col in df.columns:
        col_lower = col.lower()
        
        # Bloqueia colunas do ano alvo (exceto se for institucional como fase)
        is_target_year = any(p in col for p in target_patterns)
        is_blocked_prefix = any(col_lower.startswith(p) for p in blocked_prefixes)
        
        if is_blocked_prefix or (is_target_year and 'instituicao' not in col_lower):
            blocked.append(col)
        else:
            valid.append(col)
    
    return valid, blocked
