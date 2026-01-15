"""
Testes de smoke para pipeline de treino.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import tempfile
import shutil

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestTrainSmoke:
    """Testes de smoke para src.train."""
    
    @pytest.fixture
    def synthetic_dataset(self, tmp_path):
        """Cria dataset sintético para teste."""
        np.random.seed(42)
        n_samples = 100
        
        df = pd.DataFrame({
            'ra': range(n_samples),
            'instituicao_2023': np.random.choice(['A', 'B', 'C'], n_samples),
            'idade_2023': np.random.randint(8, 15, n_samples).astype(float),
            'fase_2023': np.random.choice(['ALFA', 'F1', 'F2', 'F3'], n_samples),
            'ian_2023': np.random.uniform(4, 10, n_samples),
            'ida_2023': np.random.uniform(4, 10, n_samples),
            'ieg_2023': np.random.uniform(4, 10, n_samples),
            'iaa_2023': np.random.uniform(4, 10, n_samples),
            'ips_2023': np.random.uniform(4, 10, n_samples),
            'ipp_2023': np.random.uniform(4, 10, n_samples),
            'ipv_2023': np.random.uniform(4, 10, n_samples),
            'em_risco_2024': np.random.choice([0, 1], n_samples, p=[0.6, 0.4]),
        })
        
        # Adiciona alguns missing
        df.loc[0:5, 'ida_2023'] = np.nan
        df.loc[10:15, 'ieg_2023'] = np.nan
        
        data_path = tmp_path / "test_dataset.parquet"
        df.to_parquet(data_path)
        
        return data_path, tmp_path
    
    def test_train_imports(self):
        """Verifica que módulo train importa corretamente."""
        from train import (
            load_and_prepare_data,
            create_baselines,
            train_and_evaluate,
            save_artifacts
        )
        
        assert callable(load_and_prepare_data)
        assert callable(create_baselines)
        assert callable(train_and_evaluate)
        assert callable(save_artifacts)
    
    def test_train_generates_artifacts(self, synthetic_dataset):
        """Verifica que treino gera artefatos esperados."""
        data_path, tmp_path = synthetic_dataset
        artifacts_dir = tmp_path / "artifacts"
        
        from train import (
            load_and_prepare_data,
            train_and_evaluate,
            save_artifacts
        )
        from sklearn.model_selection import train_test_split
        from utils import set_seed
        
        set_seed(42)
        
        # Carrega dados
        df, X, y = load_and_prepare_data(str(data_path))
        
        # Split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Treina
        results, best_pipeline, best_threshold = train_and_evaluate(
            X_train, y_train, X_test, y_test, seed=42
        )
        
        # Salva
        save_artifacts(
            artifacts_dir,
            best_pipeline,
            results,
            best_threshold,
            X.columns.tolist(),
            42
        )
        
        # Verifica arquivos
        assert (artifacts_dir / "model.joblib").exists()
        assert (artifacts_dir / "metrics.json").exists()
        assert (artifacts_dir / "model_metadata.json").exists()
        assert (artifacts_dir / "model_signature.json").exists()
    
    def test_train_baselines_comparable(self, synthetic_dataset):
        """Verifica que baselines retornam métricas comparáveis."""
        data_path, tmp_path = synthetic_dataset
        
        from train import load_and_prepare_data, train_and_evaluate
        from sklearn.model_selection import train_test_split
        from utils import set_seed
        
        set_seed(42)
        
        df, X, y = load_and_prepare_data(str(data_path))
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        results, _, _ = train_and_evaluate(X_train, y_train, X_test, y_test, seed=42)
        
        # Verifica que todos os baselines têm métricas
        assert "baseline0_naive" in results
        assert "baseline1_logistic" in results
        assert "baseline2_rf" in results
        
        # Verifica que métricas existem
        for name, metrics in results.items():
            assert "recall" in metrics
            assert "precision" in metrics
            assert "f1" in metrics
            assert 0 <= metrics["recall"] <= 1
            assert 0 <= metrics["precision"] <= 1


class TestEvaluateSmoke:
    """Testes de smoke para evaluate."""
    
    def test_calculate_metrics(self):
        """Verifica cálculo de métricas."""
        from evaluate import calculate_metrics
        
        y_true = np.array([0, 0, 1, 1, 1])
        y_pred = np.array([0, 1, 1, 1, 0])
        y_proba = np.array([0.1, 0.6, 0.8, 0.9, 0.3])
        
        metrics = calculate_metrics(y_true, y_pred, y_proba)
        
        assert "recall" in metrics
        assert "precision" in metrics
        assert "f1" in metrics
        assert "pr_auc" in metrics
        assert "confusion_matrix" in metrics
    
    def test_select_threshold(self):
        """Verifica seleção de threshold."""
        from evaluate import select_threshold
        
        y_true = np.array([0, 0, 0, 1, 1, 1, 1, 1])
        y_proba = np.array([0.1, 0.2, 0.3, 0.4, 0.6, 0.7, 0.8, 0.9])
        
        threshold, metrics = select_threshold(
            y_true, y_proba, 
            objective="max_recall",
            min_recall=0.5
        )
        
        assert 0 <= threshold <= 1
        assert "recall" in metrics
        assert metrics["recall"] >= 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
