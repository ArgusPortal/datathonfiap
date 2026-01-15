"""
Testes da Fase 1: Data Product.

Testa ingestão, normalização, qualidade e anti-leakage.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Adiciona src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from data_quality import DataQualityChecker, QualityCheckResult


class TestDataQualityChecker:
    """Testes para DataQualityChecker."""
    
    @pytest.fixture
    def sample_df(self):
        """DataFrame de exemplo para testes."""
        return pd.DataFrame({
            'ra': [1, 2, 3, 4, 5],
            'nome': ['A', 'B', 'C', 'D', 'E'],
            'inde': [7.5, 8.0, np.nan, 9.0, 6.5],
            'ida': [6.0, 7.0, 8.0, 5.0, 7.5],
            'fase': [2, 3, 4, 5, 6],
        })
    
    @pytest.fixture
    def df_with_duplicates(self):
        """DataFrame com duplicatas."""
        return pd.DataFrame({
            'ra': [1, 2, 3, 1, 4],  # RA 1 duplicado
            'nome': ['A', 'B', 'C', 'A', 'D'],
        })
    
    @pytest.fixture
    def df_out_of_range(self):
        """DataFrame com valores fora do range."""
        return pd.DataFrame({
            'ra': [1, 2, 3],
            'inde': [7.5, 15.0, 8.0],  # 15.0 fora do range [0,10]
            'defasagem': [-1, 0, 20],  # 20 fora do range [-10,10]
        })
    
    def test_check_duplicates_clean(self, sample_df):
        """Testa detecção de duplicatas em dados limpos."""
        checker = DataQualityChecker(sample_df)
        result = checker.check_duplicates(key_column='ra')
        
        assert result.passed is True
        assert result.details['n_duplicates'] == 0
    
    def test_check_duplicates_with_dups(self, df_with_duplicates):
        """Testa detecção de duplicatas em dados com duplicatas."""
        checker = DataQualityChecker(df_with_duplicates)
        result = checker.check_duplicates(key_column='ra')
        
        assert result.passed is False
        assert result.details['n_duplicates'] == 2  # 2 linhas com RA=1
        assert 1 in result.details['duplicate_keys']
    
    def test_check_ranges_clean(self, sample_df):
        """Testa validação de ranges em dados limpos."""
        checker = DataQualityChecker(sample_df)
        result = checker.check_ranges()
        
        assert result.passed is True
    
    def test_check_ranges_violation(self, df_out_of_range):
        """Testa detecção de violações de range."""
        checker = DataQualityChecker(df_out_of_range)
        result = checker.check_ranges()
        
        assert result.passed is False
        assert 'inde' in result.details['violations']
        assert 'defasagem' in result.details['violations']
    
    def test_check_missing_values(self, sample_df):
        """Testa verificação de missing values."""
        checker = DataQualityChecker(sample_df)
        result = checker.check_missing_values(critical_columns=['ra'])
        
        assert result.passed is True
        assert 'inde' in result.details['all_missing']  # inde tem 1 NaN
    
    def test_check_missing_critical_column(self):
        """Testa falha quando coluna crítica tem missing."""
        df = pd.DataFrame({
            'ra': [1, np.nan, 3],  # RA com missing
            'nome': ['A', 'B', 'C'],
        })
        
        checker = DataQualityChecker(df)
        result = checker.check_missing_values(critical_columns=['ra'])
        
        assert result.passed is False
        assert 'ra' in result.details['critical_failures']
    
    def test_leakage_detection_clean(self, sample_df):
        """Testa que features limpas não disparam leakage."""
        checker = DataQualityChecker(sample_df)
        feature_cols = ['nome', 'inde', 'ida', 'fase']
        result = checker.check_leakage(feature_cols)
        
        assert result.passed is True
    
    def test_leakage_detection_blocked_columns(self):
        """Testa detecção de leakage com colunas bloqueadas."""
        df = pd.DataFrame({
            'ra': [1, 2, 3],
            'inde': [7.0, 8.0, 6.0],
            'defasagem': [-1, 0, 1],  # LEAKAGE!
            'ponto_virada': ['Sim', 'Não', 'Sim'],  # LEAKAGE!
        })
        
        checker = DataQualityChecker(df)
        feature_cols = ['inde', 'defasagem', 'ponto_virada']
        result = checker.check_leakage(feature_cols)
        
        assert result.passed is False
        assert 'defasagem' in result.details['leakage_columns']
        assert 'ponto_virada' in result.details['leakage_columns']
    
    def test_run_all_checks(self, sample_df):
        """Testa execução de todas as verificações."""
        checker = DataQualityChecker(sample_df, year=2023)
        all_passed, results = checker.run_all_checks(critical_columns=['ra'])
        
        assert isinstance(all_passed, bool)
        assert len(results) >= 4  # duplicates, ranges, missing, dtypes
    
    def test_get_summary(self, sample_df):
        """Testa geração de resumo."""
        checker = DataQualityChecker(sample_df, year=2023)
        checker.run_all_checks()
        summary = checker.get_summary()
        
        assert "Data Quality Report" in summary
        assert "2023" in summary


class TestTargetComputation:
    """Testes para computação do target."""
    
    def test_target_negative_defasagem(self):
        """Testa que defasagem negativa = em_risco=1."""
        from make_dataset import compute_target
        
        defasagem = pd.Series([-1, -2, -3])
        target = compute_target(defasagem)
        
        assert target.sum() == 3
        assert all(target == 1)
    
    def test_target_zero_defasagem(self):
        """Testa que defasagem zero = em_risco=0."""
        from make_dataset import compute_target
        
        defasagem = pd.Series([0, 0, 0])
        target = compute_target(defasagem)
        
        assert target.sum() == 0
        assert all(target == 0)
    
    def test_target_positive_defasagem(self):
        """Testa que defasagem positiva = em_risco=0."""
        from make_dataset import compute_target
        
        defasagem = pd.Series([1, 2, 3])
        target = compute_target(defasagem)
        
        assert target.sum() == 0
        assert all(target == 0)
    
    def test_target_mixed_defasagem(self):
        """Testa distribuição mista de defasagem."""
        from make_dataset import compute_target
        
        defasagem = pd.Series([-2, -1, 0, 1, 2])
        target = compute_target(defasagem)
        
        expected = pd.Series([1, 1, 0, 0, 0])
        assert all(target == expected)


class TestColumnNormalization:
    """Testes para normalização de colunas."""
    
    def test_normalize_basic(self):
        """Testa normalização básica de coluna."""
        from make_dataset import normalize_column_name
        
        assert normalize_column_name('RA') == 'ra'
        assert normalize_column_name('  INDE  ') == 'inde'
        assert normalize_column_name('Fase') == 'fase'
    
    def test_normalize_with_spaces(self):
        """Testa normalização de colunas com espaços."""
        from make_dataset import normalize_column_name
        
        assert normalize_column_name('Fase Ideal') == 'fase_ideal'
        assert normalize_column_name('Anos PM') == 'anos_pm'
        assert normalize_column_name('Ponto de Virada') == 'ponto_virada'
    
    def test_normalize_preserves_unknown(self):
        """Testa que colunas desconhecidas são preservadas."""
        from make_dataset import normalize_column_name
        
        result = normalize_column_name('Coluna Nova Estranha')
        assert result == 'coluna_nova_estranha'


class TestFeatureAvailability:
    """Testes para regras de feature availability."""
    
    def test_blocked_columns_defined(self):
        """Testa que colunas bloqueadas estão definidas."""
        from make_dataset import BLOCKED_COLUMNS
        
        assert 'defasagem' in BLOCKED_COLUMNS
        assert 'ponto_virada' in BLOCKED_COLUMNS
        assert 'pedra' in BLOCKED_COLUMNS
    
    def test_allowed_columns_defined(self):
        """Testa que colunas permitidas estão definidas."""
        from make_dataset import ALLOWED_FEATURE_COLUMNS
        
        assert 'ra' in ALLOWED_FEATURE_COLUMNS
        assert 'inde' in ALLOWED_FEATURE_COLUMNS
        assert 'fase' in ALLOWED_FEATURE_COLUMNS
        
        # Verifica que bloqueadas não estão em permitidas
        assert 'defasagem' not in ALLOWED_FEATURE_COLUMNS
        assert 'ponto_virada' not in ALLOWED_FEATURE_COLUMNS


class TestIntegration:
    """Testes de integração (requerem arquivo PEDE2024.xlsx)."""
    
    @pytest.fixture
    def source_file(self):
        """Caminho do arquivo fonte."""
        return Path(__file__).parent.parent / "PEDE2024.xlsx"
    
    @pytest.mark.skipif(
        not (Path(__file__).parent.parent / "PEDE2024.xlsx").exists(),
        reason="Arquivo PEDE2024.xlsx não disponível"
    )
    def test_load_sheet(self, source_file):
        """Testa carregamento de aba do Excel."""
        from make_dataset import load_and_normalize_sheet
        
        df, schema = load_and_normalize_sheet(source_file, "PEDE2024", 2024)
        
        assert len(df) > 0
        assert 'ra' in df.columns
        assert 'ano' in df.columns
        assert df['ano'].iloc[0] == 2024
    
    @pytest.mark.skipif(
        not (Path(__file__).parent.parent / "PEDE2024.xlsx").exists(),
        reason="Arquivo PEDE2024.xlsx não disponível"
    )
    def test_pipeline_creates_outputs(self, source_file, tmp_path):
        """Testa que pipeline cria outputs esperados."""
        from make_dataset import run_pipeline
        
        interim_dir = tmp_path / "interim"
        processed_dir = tmp_path / "processed"
        
        success, df = run_pipeline(
            source_file=source_file,
            output_interim=interim_dir,
            output_processed=processed_dir,
            feature_year=2023,
            label_year=2024,
            validate=True
        )
        
        assert success is True
        assert df is not None
        assert len(df) > 0
        
        # Verifica arquivos criados
        assert (interim_dir / "2023_normalized.parquet").exists()
        assert (interim_dir / "2024_normalized.parquet").exists()
        assert (processed_dir / "modeling_dataset.parquet").exists()
        assert (processed_dir / "data_card.json").exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
