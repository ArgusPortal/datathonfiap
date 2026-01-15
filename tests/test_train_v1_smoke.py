"""
Testes de smoke para pipeline v1.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestTrainV1Smoke:
    """Testes de smoke para treino v1."""
    
    @pytest.fixture
    def synthetic_dataset(self, tmp_path):
        """Cria dataset sintético para teste."""
        np.random.seed(42)
        n = 150
        
        df = pd.DataFrame({
            'ra': range(n),
            'instituicao_2023': np.random.choice(['A', 'B', 'C'], n),
            'idade_2023': np.random.uniform(8, 15, n),
            'fase_2023': np.random.choice(['ALFA', 'F1', 'F2', 'F3'], n),
            'ian_2023': np.random.uniform(4, 10, n),
            'ida_2023': np.random.uniform(4, 10, n),
            'ieg_2023': np.random.uniform(4, 10, n),
            'iaa_2023': np.random.uniform(4, 10, n),
            'ips_2023': np.random.uniform(4, 10, n),
            'ipp_2023': np.random.uniform(4, 10, n),
            'ipv_2023': np.random.uniform(4, 10, n),
            'em_risco_2024': np.random.choice([0, 1], n, p=[0.6, 0.4]),
        })
        
        # Missing values
        df.loc[0:5, 'ida_2023'] = np.nan
        
        data_path = tmp_path / "test_data.parquet"
        df.to_parquet(data_path)
        
        return data_path, tmp_path
    
    def test_train_v1_imports(self):
        """Verifica imports do módulo train."""
        from train import (
            load_and_prepare_data,
            create_candidate_models,
            train_and_evaluate_v1,
            save_artifacts_v1,
        )
        
        assert callable(load_and_prepare_data)
        assert callable(create_candidate_models)
        assert callable(train_and_evaluate_v1)
        assert callable(save_artifacts_v1)
    
    def test_train_v1_creates_artifacts(self, synthetic_dataset):
        """Verifica que treino v1 cria todos artefatos."""
        data_path, tmp_path = synthetic_dataset
        artifacts_dir = tmp_path / "artifacts"
        
        from train import (
            load_and_prepare_data,
            train_and_evaluate_v1,
            save_artifacts_v1,
        )
        from sklearn.model_selection import train_test_split
        from utils import set_seed
        
        set_seed(42)
        
        df, X, y = load_and_prepare_data(str(data_path))
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        all_results, best_pipeline, best_threshold, best_name = train_and_evaluate_v1(
            X_train, y_train, X_test, y_test,
            seed=42,
            calibration="sigmoid",
        )
        
        save_artifacts_v1(
            artifacts_dir,
            best_pipeline,
            all_results,
            best_threshold,
            best_name,
            X.columns.tolist(),
            seed=42,
            calibration="sigmoid",
        )
        
        # Verifica artefatos obrigatórios
        assert (artifacts_dir / "model_v1.joblib").exists()
        assert (artifacts_dir / "metrics_v1.json").exists()
        assert (artifacts_dir / "model_metadata_v1.json").exists()
        assert (artifacts_dir / "model_signature_v1.json").exists()
        assert (artifacts_dir / "model_comparison.json").exists()
        assert (artifacts_dir / "model_report.md").exists()
    
    def test_train_v1_candidates_evaluated(self, synthetic_dataset):
        """Verifica que todos candidatos são avaliados."""
        data_path, tmp_path = synthetic_dataset
        
        from train import load_and_prepare_data, train_and_evaluate_v1
        from sklearn.model_selection import train_test_split
        from utils import set_seed
        
        set_seed(42)
        
        df, X, y = load_and_prepare_data(str(data_path))
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        all_results, _, _, _ = train_and_evaluate_v1(
            X_train, y_train, X_test, y_test, seed=42
        )
        
        # Verifica candidatos avaliados
        assert 'logreg' in all_results['test']
        assert 'hist_gb' in all_results['test']
        assert 'rf' in all_results['test']
        
        # Verifica métricas
        for model in ['logreg', 'hist_gb', 'rf']:
            assert 'recall' in all_results['test'][model]
            assert 'precision' in all_results['test'][model]
            assert 'pr_auc' in all_results['test'][model]
    
    def test_model_card_generation(self):
        """Testa geração do model card."""
        from model_card import build_model_card
        
        metadata = {
            'model_version': 'v1.1.0',
            'target_definition': 'em_risco=1 se defasagem<0',
            'training_periods': ['2023->2024'],
            'population_filter': 'all_phases',
            'model_family': 'logreg',
            'calibration': 'sigmoid',
            'threshold_policy': {'threshold_value': 0.3},
        }
        
        test_metrics = {
            'recall': 0.85,
            'precision': 0.45,
            'f1': 0.59,
            'f2': 0.73,
            'pr_auc': 0.78,
            'brier_score': 0.18,
            'n_samples': 100,
            'n_positive': 40,
            'confusion_matrix': [[45, 15], [6, 34]],
        }
        
        comparison = {
            'ranking': [
                {'rank': 1, 'model': 'logreg', 'recall': 0.85, 'precision': 0.45, 'pr_auc': 0.78},
                {'rank': 2, 'model': 'hist_gb', 'recall': 0.82, 'precision': 0.48, 'pr_auc': 0.80},
            ]
        }
        
        report = build_model_card(metadata, test_metrics, comparison)
        
        assert '# Model Report' in report
        assert 'v1.1.0' in report
        assert 'Recall' in report
        assert '0.85' in report


class TestEvaluateV1:
    """Testes para funções de evaluate v1."""
    
    def test_calibration_metrics(self):
        """Testa cálculo de métricas de calibração."""
        from evaluate import calculate_calibration_metrics
        
        np.random.seed(42)
        y_true = np.array([0, 0, 0, 1, 1, 1, 1, 1, 0, 0])
        y_proba = np.array([0.1, 0.2, 0.3, 0.7, 0.8, 0.9, 0.6, 0.75, 0.4, 0.25])
        
        metrics = calculate_calibration_metrics(y_true, y_proba)
        
        assert 'brier_score' in metrics
        assert 0 <= metrics['brier_score'] <= 1
        assert 'calibration_curve' in metrics
    
    def test_threshold_with_constraints(self):
        """Testa seleção de threshold com constraints."""
        from evaluate import select_threshold_with_constraints
        
        y_true = np.array([0, 0, 0, 0, 1, 1, 1, 1, 1, 1])
        y_proba = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.85, 0.9])
        
        threshold, metrics = select_threshold_with_constraints(
            y_true, y_proba,
            objective="max_recall",
            min_recall=0.8,
        )
        
        assert 0 <= threshold <= 1
        assert metrics['recall'] >= 0.8
    
    def test_model_comparison_report(self):
        """Testa geração de relatório de comparação."""
        from evaluate import generate_model_comparison_report
        
        results = {
            'model_a': {'recall': 0.9, 'precision': 0.4, 'pr_auc': 0.75},
            'model_b': {'recall': 0.8, 'precision': 0.5, 'pr_auc': 0.78},
        }
        
        report = generate_model_comparison_report(results, primary_metric='recall')
        
        assert report['best_model'] == 'model_a'
        assert len(report['ranking']) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
