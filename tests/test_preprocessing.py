"""
Testes de preprocessing.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from preprocessing import (
    build_preprocessor,
    identify_column_types,
    validate_no_blocked_columns,
    prepare_features,
    convert_mixed_types,
    BLOCKED_COLUMNS
)


class TestBuildPreprocessor:
    """Testes para build_preprocessor."""
    
    @pytest.fixture
    def sample_df(self):
        """DataFrame de exemplo."""
        return pd.DataFrame({
            'idade_2023': [10.0, 11.0, np.nan, 12.0, 9.0],
            'fase_2023': ['ALFA', 'F1', 'F2', 'ALFA', 'F1'],
            'ian_2023': [7.5, 8.0, 6.5, np.nan, 7.0],
            'ida_2023': [6.0, 7.0, 8.0, 5.0, np.nan],
        })
    
    def test_build_preprocessor_runs(self, sample_df):
        """Verifica que build_preprocessor executa sem erros."""
        preprocessor, num_cols, cat_cols = build_preprocessor(sample_df, target_year=2024)
        
        assert preprocessor is not None
        assert isinstance(num_cols, list)
        assert isinstance(cat_cols, list)
    
    def test_preprocessor_handles_missing(self, sample_df):
        """Verifica que preprocessor lida com missing values."""
        preprocessor, _, _ = build_preprocessor(sample_df, target_year=2024)
        
        # Fit e transform
        X_transformed = preprocessor.fit_transform(sample_df)
        
        # Não deve ter NaN após transform
        assert not np.isnan(X_transformed).any()
    
    def test_preprocessor_handles_new_categories(self, sample_df):
        """Verifica que preprocessor lida com categorias novas."""
        preprocessor, _, _ = build_preprocessor(sample_df, target_year=2024)
        preprocessor.fit(sample_df)
        
        # Cria dados com categoria nova
        new_df = pd.DataFrame({
            'idade_2023': [10.0],
            'fase_2023': ['NOVA_FASE'],  # Categoria não vista no treino
            'ian_2023': [7.5],
            'ida_2023': [6.0],
        })
        
        # Deve funcionar sem erro (handle_unknown='ignore')
        X_transformed = preprocessor.transform(new_df)
        assert X_transformed is not None


class TestValidateBlockedColumns:
    """Testes para validação de leakage."""
    
    def test_blocked_column_raises_error(self):
        """Verifica que coluna bloqueada levanta erro."""
        columns = ['idade_2023', 'defasagem', 'ian_2023']
        
        with pytest.raises(ValueError, match="LEAKAGE"):
            validate_no_blocked_columns(columns, target_year=2024)
    
    def test_target_year_column_raises_error(self):
        """Verifica que coluna do ano do target levanta erro."""
        columns = ['idade_2023', 'inde_2024']  # 2024 é o ano do target
        
        with pytest.raises(ValueError, match="target year 2024"):
            validate_no_blocked_columns(columns, target_year=2024)
    
    def test_clean_columns_pass(self):
        """Verifica que colunas limpas passam."""
        columns = ['idade_2023', 'ian_2023', 'fase_2023']
        
        # Não deve levantar erro
        validate_no_blocked_columns(columns, target_year=2024)


class TestIdentifyColumnTypes:
    """Testes para identificação de tipos."""
    
    def test_identifies_numeric(self):
        """Verifica identificação de colunas numéricas."""
        df = pd.DataFrame({
            'numeric1': [1.0, 2.0, 3.0],
            'numeric2': [1, 2, 3],
            'categorical': ['a', 'b', 'c'],
        })
        
        num_cols, cat_cols = identify_column_types(df)
        
        assert 'numeric1' in num_cols
        assert 'numeric2' in num_cols
        assert 'categorical' in cat_cols
    
    def test_converts_numeric_strings(self):
        """Verifica conversão de strings numéricas."""
        df = pd.DataFrame({
            'numeric_as_string': ['1.0', '2.0', '3.0', '4.0', '5.0'],
        })
        
        num_cols, cat_cols = identify_column_types(df)
        
        # Deve identificar como numérico (>80% conversível)
        assert 'numeric_as_string' in num_cols


class TestConvertMixedTypes:
    """Testes para conversão de tipos mistos."""
    
    def test_converts_numeric_object_columns(self):
        """Verifica conversão de colunas object com valores numéricos."""
        df = pd.DataFrame({
            'mixed': ['1', '2', '3', '4', '5'],
        })
        
        df_converted = convert_mixed_types(df)
        
        assert df_converted['mixed'].dtype in [np.float64, np.int64]
    
    def test_preserves_categorical(self):
        """Verifica que categóricas são preservadas."""
        df = pd.DataFrame({
            'categorical': ['ALFA', 'F1', 'F2', 'F3', 'F4'],
        })
        
        df_converted = convert_mixed_types(df)
        
        # Deve permanecer object
        assert df_converted['categorical'].dtype == object


class TestPrepareFeatures:
    """Testes para prepare_features."""
    
    def test_separates_target(self):
        """Verifica separação de target."""
        df = pd.DataFrame({
            'ra': [1, 2, 3],
            'feature1': [1.0, 2.0, 3.0],
            'em_risco_2024': [0, 1, 0],
        })
        
        X, y = prepare_features(df, 'em_risco_2024', ['ra'], target_year=2024)
        
        assert 'em_risco_2024' not in X.columns
        assert 'ra' not in X.columns
        assert len(y) == 3
        assert y.sum() == 1
    
    def test_raises_on_leakage(self):
        """Verifica que levanta erro em leakage."""
        df = pd.DataFrame({
            'ra': [1, 2, 3],
            'defasagem': [0, -1, 1],  # LEAKAGE!
            'em_risco_2024': [0, 1, 0],
        })
        
        with pytest.raises(ValueError, match="LEAKAGE"):
            prepare_features(df, 'em_risco_2024', ['ra'], target_year=2024)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
