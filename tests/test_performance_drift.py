"""
Testes para monitoring/performance_drift.py.
"""

import json
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta, timezone
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestPerformanceDriftFunctions:
    """Testes para funções de performance drift."""
    
    def test_compute_metrics_perfect(self):
        """Testa cálculo de métricas com predições perfeitas."""
        from monitoring.performance_drift import compute_metrics
        
        y_true = np.array([1, 0, 1, 0, 1])
        y_pred = np.array([1, 0, 1, 0, 1])
        y_proba = np.array([0.9, 0.1, 0.8, 0.2, 0.9])
        
        metrics = compute_metrics(y_true, y_pred, y_proba)
        
        assert metrics["recall"] == 1.0
        assert metrics["precision"] == 1.0
    
    def test_compute_metrics_with_errors(self):
        """Testa cálculo de métricas com erros."""
        from monitoring.performance_drift import compute_metrics
        
        y_true = np.array([1, 0, 0, 1, 1])
        y_pred = np.array([1, 1, 1, 1, 0])  # Alguns erros
        y_proba = np.array([0.9, 0.6, 0.6, 0.8, 0.3])
        
        metrics = compute_metrics(y_true, y_pred, y_proba)
        
        assert metrics["recall"] < 1.0  # Perdeu o último
        assert metrics["precision"] < 1.0  # FPs
        assert 0 <= metrics["f1"] <= 1.0
    
    def test_analyze_performance_no_data(self):
        """Testa análise sem dados."""
        from monitoring.performance_drift import analyze_performance
        
        inference_df = pd.DataFrame()
        labels_df = pd.DataFrame()
        
        result = analyze_performance(inference_df, labels_df)
        
        assert result["status"] == "no_data"
    
    def test_analyze_performance_insufficient_data(self):
        """Testa análise com dados insuficientes."""
        from monitoring.performance_drift import analyze_performance
        
        inference_df = pd.DataFrame({
            "request_id": ["r1", "r2", "r3"],
            "risk_score": [0.8, 0.3, 0.6],
            "risk_label": [1, 0, 1]
        })
        
        labels_df = pd.DataFrame({
            "request_id": ["r1", "r2"],
            "label": [1, 0]
        })
        
        result = analyze_performance(inference_df, labels_df)
        
        assert result["status"] == "insufficient_data"
        assert result["n_samples"] == 2


class TestPerformanceDriftReport:
    """Testes para geração de relatório."""
    
    def test_generate_html_report(self, tmp_path):
        """Testa geração de relatório HTML."""
        from monitoring.performance_drift import generate_html_report
        
        results = {
            "status": "green",
            "window_days": 30,
            "n_samples": 100,
            "positive_rate": 0.3,
            "metrics": {
                "recall": 0.75,
                "precision": 0.40,
                "f1": 0.52,
                "roc_auc": 0.80,
                "pr_auc": 0.60,
                "brier_score": 0.15
            },
            "alerts": [],
            "computed_at": datetime.now(timezone.utc).isoformat()
        }
        
        output_path = tmp_path / "report.html"
        
        generate_html_report(results, output_path)
        
        assert output_path.exists()
        content = output_path.read_text()
        assert "recall" in content.lower()
        assert "0.75" in content or "75" in content
    
    def test_report_includes_alerts(self, tmp_path):
        """Testa que relatório inclui alertas."""
        from monitoring.performance_drift import generate_html_report
        
        results = {
            "status": "red",
            "window_days": 30,
            "n_samples": 50,
            "positive_rate": 0.2,
            "metrics": {"recall": 0.65},
            "alerts": ["Recall baixo: 0.650 < 0.70"],
            "computed_at": datetime.now(timezone.utc).isoformat()
        }
        
        output_path = tmp_path / "report_with_alerts.html"
        
        generate_html_report(results, output_path)
        
        content = output_path.read_text()
        assert "alert" in content.lower() or "Recall baixo" in content


class TestPerformanceDriftCLI:
    """Testes para CLI do performance drift."""
    
    def test_cli_help(self):
        """Testa help do CLI."""
        from monitoring.performance_drift import main
        import sys
        from unittest.mock import patch
        
        with patch.object(sys, 'argv', ['performance_drift', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0


class TestLabelsLoading:
    """Testes para carregamento de labels."""
    
    def test_load_labels_parquet(self, tmp_path):
        """Testa carregamento de labels em parquet."""
        from monitoring.performance_drift import load_labels_store
        
        labels = pd.DataFrame({
            "request_id": ["a", "b", "c"],
            "timestamp": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]),
            "label": [1, 0, 1]
        })
        
        labels_path = tmp_path / "labels.parquet"
        labels.to_parquet(labels_path)
        
        loaded = load_labels_store(labels_path)
        
        assert len(loaded) == 3
        assert "label" in loaded.columns
    
    def test_load_labels_csv(self, tmp_path):
        """Testa carregamento de labels em CSV."""
        from monitoring.performance_drift import load_labels_store
        
        labels = pd.DataFrame({
            "request_id": ["a", "b", "c"],
            "label": [1, 0, 1]
        })
        
        labels_path = tmp_path / "labels.csv"
        labels.to_csv(labels_path, index=False)
        
        loaded = load_labels_store(labels_path)
        
        assert len(loaded) == 3
    
    def test_load_labels_not_found(self, tmp_path):
        """Testa quando arquivo de labels não existe."""
        from monitoring.performance_drift import load_labels_store
        
        labels_path = tmp_path / "nonexistent.parquet"
        
        loaded = load_labels_store(labels_path)
        
        assert loaded.empty
