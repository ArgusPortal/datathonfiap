"""
Testes para feature_engineering.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from feature_engineering import (
    make_features,
    create_delta_features,
    create_risk_composites,
    create_missing_indicators,
    create_tenure_feature,
    get_feature_list,
    validate_features_for_year,
)


class TestCreateDeltaFeatures:
    """Testes para criação de deltas."""
    
    def test_creates_deltas_when_columns_exist(self):
        """Cria deltas quando colunas 2022 e 2023 existem."""
        df = pd.DataFrame({
            'ian_2022': [5.0, 6.0, 7.0],
            'ian_2023': [6.0, 7.0, 8.0],
            'ida_2022': [4.0, 5.0, 6.0],
            'ida_2023': [5.0, 6.0, 7.0],
        })
        
        result = create_delta_features(df)
        
        assert 'delta_ian_22_23' in result.columns
        assert 'delta_ida_22_23' in result.columns
        np.testing.assert_array_equal(result['delta_ian_22_23'], [1.0, 1.0, 1.0])
    
    def test_skips_when_columns_missing(self):
        """Não quebra quando colunas não existem."""
        df = pd.DataFrame({
            'ian_2023': [6.0, 7.0, 8.0],
            'idade_2023': [10, 11, 12],
        })
        
        result = create_delta_features(df)
        
        # Não deve criar delta (falta 2022)
        delta_cols = [c for c in result.columns if 'delta' in c]
        assert len(delta_cols) == 0
    
    def test_handles_mixed_availability(self):
        """Cria deltas apenas para pares disponíveis."""
        df = pd.DataFrame({
            'ian_2022': [5.0, 6.0],
            'ian_2023': [6.0, 7.0],
            'ida_2023': [5.0, 6.0],  # Sem 2022
        })
        
        result = create_delta_features(df)
        
        assert 'delta_ian_22_23' in result.columns
        assert 'delta_ida_22_23' not in result.columns


class TestCreateRiskComposites:
    """Testes para features compostas de risco."""
    
    def test_creates_composites(self):
        """Cria media, min, max, std de indicadores."""
        df = pd.DataFrame({
            'ian_2023': [5.0, 6.0, 7.0],
            'ida_2023': [4.0, 5.0, 8.0],
            'ieg_2023': [6.0, 7.0, 6.0],
        })
        
        result = create_risk_composites(df)
        
        assert 'media_indicadores' in result.columns
        assert 'min_indicador' in result.columns
        assert 'max_indicador' in result.columns
        assert 'std_indicadores' in result.columns
        assert 'range_indicadores' in result.columns
        
        # Verifica valores
        np.testing.assert_almost_equal(result['media_indicadores'].iloc[0], 5.0)
        assert result['min_indicador'].iloc[0] == 4.0
        assert result['max_indicador'].iloc[0] == 6.0
    
    def test_handles_no_indicators(self):
        """Não quebra se não houver indicadores."""
        df = pd.DataFrame({
            'nome': ['A', 'B'],
            'idade': [10, 11],
        })
        
        result = create_risk_composites(df)
        
        # Não deve criar composites se não houver indicadores
        # mas não deve quebrar
        assert len(result) == 2


class TestGetFeatureList:
    """Testes para listagem de features."""
    
    def test_excludes_target_and_id(self):
        """Exclui colunas de target e ID."""
        df = pd.DataFrame({
            'ra': [1, 2],
            'ian_2023': [5.0, 6.0],
            'em_risco_2024': [0, 1],
        })
        
        features = get_feature_list(df)
        
        assert 'ra' not in features
        assert 'em_risco_2024' not in features
        assert 'ian_2023' in features
    
    def test_returns_sorted_list(self):
        """Retorna lista ordenada."""
        df = pd.DataFrame({
            'z_col': [1],
            'a_col': [2],
            'm_col': [3],
        })
        
        features = get_feature_list(df)
        
        assert features == sorted(features)


class TestValidateFeaturesForYear:
    """Testes para validação anti-leakage."""
    
    def test_blocks_target_year_features(self):
        """Bloqueia features do ano alvo."""
        df = pd.DataFrame({
            'ian_2023': [5.0],
            'ian_2024': [6.0],  # Ano alvo - deve bloquear
            'em_risco_2024': [1],
        })
        
        valid, blocked = validate_features_for_year(df, target_year=2024)
        
        assert 'ian_2023' in valid
        assert 'ian_2024' in blocked
        assert 'em_risco_2024' in blocked
    
    def test_blocks_leakage_prefixes(self):
        """Bloqueia prefixos conhecidos de vazamento."""
        df = pd.DataFrame({
            'ian_2023': [5.0],
            'defasagem_2023': [0],
            'ponto_virada_2023': [1],
        })
        
        valid, blocked = validate_features_for_year(df, target_year=2024)
        
        assert 'ian_2023' in valid
        assert 'defasagem_2023' in blocked
        assert 'ponto_virada_2023' in blocked


class TestMakeFeatures:
    """Testes integrados para make_features."""
    
    def test_full_pipeline(self):
        """Testa pipeline completo de feature engineering."""
        df = pd.DataFrame({
            'ra': [1, 2, 3],
            'ian_2023': [5.0, 6.0, 7.0],
            'ida_2023': [4.0, 5.0, 6.0],
            'ieg_2023': [6.0, 7.0, 8.0],
            'em_risco_2024': [0, 1, 0],
        })
        
        result = make_features(df)
        
        # Deve criar composites
        assert 'media_indicadores' in result.columns
        assert 'min_indicador' in result.columns
        
        # Deve preservar originais
        assert 'ian_2023' in result.columns
        assert 'ra' in result.columns


class TestCreateMissingIndicators:
    """Testes para criação de indicadores de missing."""
    
    def test_creates_indicators_when_missing_above_threshold(self):
        """Cria indicadores quando missing >= threshold."""
        df = pd.DataFrame({
            'ida_2023': [5.0, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],  # 90% missing
            'ieg_2023': [5.0, 6.0, 7.0, 8.0, 9.0, 10.0, np.nan, np.nan, np.nan, np.nan],  # 40% missing
        })
        
        result = create_missing_indicators(df, min_missing_pct=0.05)
        
        assert 'ida_2023_missing' in result.columns
        assert 'ieg_2023_missing' in result.columns
        assert result['ida_2023_missing'].sum() == 9  # 9 missings
        assert result['ieg_2023_missing'].sum() == 4  # 4 missings
    
    def test_skips_when_missing_below_threshold(self):
        """Não cria indicadores quando missing < threshold."""
        df = pd.DataFrame({
            'ida_2023': [5.0, 6.0, 7.0, 8.0, np.nan],  # 20% missing
        })
        
        result = create_missing_indicators(df, min_missing_pct=0.25)  # Threshold 25%
        
        assert 'ida_2023_missing' not in result.columns
    
    def test_respects_column_filter(self):
        """Respeita filtro de colunas."""
        df = pd.DataFrame({
            'ida_2023': [np.nan] * 10,  # 100% missing
            'other_2023': [np.nan] * 10,  # 100% missing
        })
        
        result = create_missing_indicators(df, columns=['ida'])
        
        assert 'ida_2023_missing' in result.columns
        assert 'other_2023_missing' not in result.columns


class TestCreateTenureFeature:
    """Testes para criação de feature de tempo na instituição."""
    
    def test_creates_tenure_from_ano_ingresso(self):
        """Cria anos_pm a partir de ano_ingresso."""
        df = pd.DataFrame({
            'ano_ingresso': [2020, 2021, 2022],
            'ian_2023': [5.0, 6.0, 7.0],  # Para detectar ano de referência
        })
        
        result = create_tenure_feature(df, reference_year=2023)
        
        assert 'anos_pm_2023' in result.columns
        np.testing.assert_array_equal(result['anos_pm_2023'], [3, 2, 1])
    
    def test_clips_unreasonable_values(self):
        """Limita valores a range razoável (0-15)."""
        df = pd.DataFrame({
            'ano_ingresso': [2000, 2030, 2020],  # Valores extremos
            'ian_2023': [5.0, 6.0, 7.0],
        })
        
        result = create_tenure_feature(df, reference_year=2023)
        
        assert result['anos_pm_2023'].max() <= 15
        assert result['anos_pm_2023'].min() >= 0
    
    def test_handles_missing_ano_ingresso(self):
        """Não quebra se ano_ingresso não existe."""
        df = pd.DataFrame({
            'ian_2023': [5.0, 6.0, 7.0],
        })
        
        result = create_tenure_feature(df)
        
        # Não deve criar coluna se ano_ingresso não existe
        tenure_cols = [c for c in result.columns if 'anos_pm' in c]
        assert len(tenure_cols) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
