"""
Testes para src/retrain.py - Pipeline de Retraining.
"""

import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestRetrainFunctions:
    """Testes para funções de retraining."""
    
    @pytest.fixture
    def mock_registry(self, tmp_path):
        """Cria registry mock com champion."""
        registry = tmp_path / "registry"
        registry.mkdir()
        
        # Champion v1.0.0
        v1_dir = registry / "v1.0.0"
        v1_dir.mkdir()
        
        # Metrics do champion
        metrics = {
            "recall": 0.75,
            "precision": 0.40,
            "f1": 0.52,
            "roc_auc": 0.80,
            "brier_score": 0.15
        }
        (v1_dir / "metrics.json").write_text(json.dumps(metrics))
        
        # Manifest
        manifest = {"version": "v1.0.0", "status": "champion"}
        (v1_dir / "manifest.json").write_text(json.dumps(manifest))
        
        # Champion.json
        champion_info = {
            "version": "v1.0.0",
            "promoted_at": "2024-01-01"
        }
        (registry / "champion.json").write_text(json.dumps(champion_info))
        
        return registry
    
    def test_load_champion_metrics(self, mock_registry):
        """Testa carregamento de métricas do champion."""
        from src.retrain import load_champion_metrics
        
        metrics = load_champion_metrics(mock_registry)
        
        assert metrics is not None
        assert metrics["recall"] == 0.75
        assert metrics["precision"] == 0.40
    
    def test_load_champion_metrics_no_champion(self, tmp_path):
        """Testa quando não há champion."""
        from src.retrain import load_champion_metrics
        
        registry = tmp_path / "empty_registry"
        registry.mkdir()
        
        metrics = load_champion_metrics(registry)
        
        assert metrics is None
    
    def test_compare_metrics_pass(self):
        """Testa comparação de métricas que passa guardrails."""
        from src.retrain import compare_metrics
        
        champion_metrics = {
            "recall": 0.75,
            "precision": 0.40,
            "brier_score": 0.15,
            "roc_auc": 0.80
        }
        
        challenger_metrics = {
            "recall": 0.77,  # Melhor
            "precision": 0.42,  # Melhor
            "brier_score": 0.14,  # Melhor
            "roc_auc": 0.82  # Melhor
        }
        
        approved, reason = compare_metrics(challenger_metrics, champion_metrics)
        
        assert approved is True
        assert "aprovado" in reason.lower()
    
    def test_compare_metrics_fail_recall(self):
        """Testa falha quando recall cai muito."""
        from src.retrain import compare_metrics
        
        champion_metrics = {
            "recall": 0.75,
            "precision": 0.40,
            "brier_score": 0.15,
            "roc_auc": 0.80
        }
        
        challenger_metrics = {
            "recall": 0.70,  # -5% FAIL (limite é -2%)
            "precision": 0.45,
            "brier_score": 0.14,
            "roc_auc": 0.82
        }
        
        approved, reason = compare_metrics(challenger_metrics, champion_metrics)
        
        assert approved is False
        assert "recall" in reason.lower()
    
    def test_compare_metrics_fail_precision(self):
        """Testa falha quando precision cai muito."""
        from src.retrain import compare_metrics
        
        champion_metrics = {
            "recall": 0.75,
            "precision": 0.40,
            "brier_score": 0.15,
            "roc_auc": 0.80
        }
        
        challenger_metrics = {
            "recall": 0.76,
            "precision": 0.30,  # -10% FAIL
            "brier_score": 0.14,
            "roc_auc": 0.82
        }
        
        approved, reason = compare_metrics(challenger_metrics, champion_metrics)
        
        assert approved is False
        assert "precision" in reason.lower()


class TestRetrainCLI:
    """Testes para CLI do retrain."""
    
    def test_cli_help(self):
        """Testa help do CLI."""
        from src.retrain import main
        
        with patch.object(sys, 'argv', ['retrain', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0
    
    def test_cli_requires_version(self):
        """Testa que CLI requer version."""
        from src.retrain import main
        
        with patch.object(sys, 'argv', ['retrain']):
            with pytest.raises(SystemExit):
                main()


class TestRetrainGuardrails:
    """Testes específicos para guardrails."""
    
    def test_recall_delta_calculation(self):
        """Testa cálculo correto do delta de recall."""
        from src.retrain import compare_metrics
        
        # Recall melhorou - deve passar
        champion = {"recall": 0.70, "precision": 0.40, "roc_auc": 0.75, "brier_score": 0.15}
        challenger = {"recall": 0.75, "precision": 0.42, "roc_auc": 0.78, "brier_score": 0.14}
        
        approved, _ = compare_metrics(challenger, champion)
        assert approved is True
        
    def test_recall_small_drop_passes(self):
        """Testa que pequena queda de recall passa."""
        from src.retrain import compare_metrics
        
        # Recall caiu -1% (dentro do limite de 2%)
        champion = {"recall": 0.75, "precision": 0.40, "roc_auc": 0.80, "brier_score": 0.15}
        challenger = {"recall": 0.74, "precision": 0.42, "roc_auc": 0.82, "brier_score": 0.14}
        
        approved, _ = compare_metrics(challenger, champion)
        assert approved is True
    
    def test_recall_large_drop_fails(self):
        """Testa que grande queda de recall falha."""
        from src.retrain import compare_metrics
        
        # Recall caiu -4% (acima do limite de 2%)
        champion = {"recall": 0.75, "precision": 0.40, "roc_auc": 0.80, "brier_score": 0.15}
        challenger = {"recall": 0.70, "precision": 0.42, "roc_auc": 0.82, "brier_score": 0.14}
        
        approved, _ = compare_metrics(challenger, champion)
        assert approved is False
