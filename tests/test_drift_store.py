"""
Testes unitários para módulo drift_store.
"""

import json
import tempfile
from pathlib import Path

import numpy as np
import pytest

from app.drift_store import (
    DriftStore,
    aggregate_batch_stats,
    compute_feature_stats,
)


class TestComputeFeatureStats:
    """Testes para função compute_feature_stats."""
    
    def test_basic_stats(self):
        """Deve computar estatísticas básicas."""
        features = {
            "feat1": 5.0,
            "feat2": 2.0,
            "feat3": 8.0,
        }
        
        stats = compute_feature_stats(features)
        
        assert stats["n_features"] == 3
        assert stats["missing_features"] == []
        assert "numeric_summary" in stats
    
    def test_detect_missing_none(self):
        """Deve detectar valores None como missing."""
        features = {"feat1": 5.0, "feat2": None, "feat3": 3.0}
        
        stats = compute_feature_stats(features)
        
        assert "feat2" in stats["missing_features"]
    
    def test_detect_missing_nan(self):
        """Deve detectar NaN como missing."""
        features = {"feat1": 5.0, "feat2": np.nan}
        
        stats = compute_feature_stats(features)
        
        assert "feat2" in stats["missing_features"]
    
    def test_numeric_bins(self):
        """Deve categorizar valores numéricos em bins."""
        features = {
            "low": 2.0,
            "medium": 5.5,
            "high": 9.0,
        }
        
        stats = compute_feature_stats(features)
        
        assert stats["numeric_summary"]["low"] == "low"
        assert stats["numeric_summary"]["medium"] == "medium"
        assert stats["numeric_summary"]["high"] == "high"
    
    def test_handles_string_values(self):
        """Deve lidar com valores string."""
        features = {"name": "test", "value": 5.0}
        
        stats = compute_feature_stats(features)
        
        # String não deve aparecer no numeric_summary
        assert "name" not in stats["numeric_summary"]
        assert "value" in stats["numeric_summary"]


class TestAggregateBatchStats:
    """Testes para função aggregate_batch_stats."""
    
    def test_empty_batch(self):
        """Deve retornar n_instances=0 para batch vazio."""
        stats = aggregate_batch_stats([])
        
        assert stats["n_instances"] == 0
    
    def test_basic_aggregation(self):
        """Deve agregar estatísticas de múltiplas instâncias."""
        instances = [
            {"feat1": 5.0, "feat2": 3.0},
            {"feat1": 6.0, "feat2": None},
            {"feat1": 7.0, "feat2": 8.0},
        ]
        
        stats = aggregate_batch_stats(instances)
        
        assert stats["n_instances"] == 3
        assert "missing_summary" in stats
        assert "feature_distribution" in stats
    
    def test_missing_summary(self):
        """Deve contar missing por feature."""
        instances = [
            {"feat1": None, "feat2": 3.0},
            {"feat1": None, "feat2": None},
            {"feat1": 5.0, "feat2": None},
        ]
        
        stats = aggregate_batch_stats(instances)
        
        # feat1 tem 2 missing, feat2 tem 2 missing
        assert stats["missing_summary"].get("feat1", 0) == 2
        assert stats["missing_summary"].get("feat2", 0) == 2
    
    def test_feature_distribution(self):
        """Deve agregar distribuição de features."""
        instances = [
            {"score": 2.0},  # low
            {"score": 5.0},  # medium
            {"score": 8.0},  # high
        ]
        
        stats = aggregate_batch_stats(instances)
        
        dist = stats["feature_distribution"]["score"]
        assert dist["low"] == 1
        assert dist["medium"] == 1
        assert dist["high"] == 1


class TestDriftStore:
    """Testes para classe DriftStore."""
    
    @pytest.fixture
    def drift_store(self, tmp_path):
        """Cria DriftStore com path temporário."""
        log_path = tmp_path / "drift_events.jsonl"
        return DriftStore(log_path)
    
    def test_log_event(self, drift_store):
        """Deve logar evento."""
        instances = [{"feat1": 5.0, "feat2": 3.0}]
        predictions = [{"risk_score": 0.6, "risk_label": 1}]
        
        drift_store.log_event(
            request_id="test-123",
            model_version="v1.0.0",
            instances=instances,
            predictions=predictions,
        )
        
        events = drift_store.read_events()
        
        assert len(events) == 1
        assert events[0]["request_id"] == "test-123"
        assert events[0]["model_version"] == "v1.0.0"
    
    def test_no_raw_ids_stored(self, drift_store):
        """NÃO deve armazenar IDs sensíveis."""
        instances = [
            {"ra": "12345", "id": "abc", "nome": "João", "feat1": 5.0}
        ]
        predictions = [{"risk_score": 0.5, "risk_label": 0}]
        
        drift_store.log_event(
            request_id="test-123",
            model_version="v1.0.0",
            instances=instances,
            predictions=predictions,
        )
        
        events = drift_store.read_events()
        event_str = json.dumps(events[0])
        
        # IDs sensíveis não devem aparecer
        assert "12345" not in event_str
        assert "abc" not in event_str
        assert "João" not in event_str
    
    def test_no_student_id_stored(self, drift_store):
        """NÃO deve armazenar student_id ou estudante_id."""
        instances = [
            {"student_id": "STU001", "estudante_id": "EST001", "feat1": 5.0}
        ]
        predictions = [{"risk_score": 0.5, "risk_label": 0}]
        
        drift_store.log_event(
            request_id="test-123",
            model_version="v1.0.0",
            instances=instances,
            predictions=predictions,
        )
        
        events = drift_store.read_events()
        event_str = json.dumps(events[0])
        
        assert "STU001" not in event_str
        assert "EST001" not in event_str
    
    def test_prediction_summary(self, drift_store):
        """Deve incluir resumo de predições."""
        instances = [
            {"feat1": 2.0},
            {"feat1": 5.0},
            {"feat1": 8.0},
        ]
        predictions = [
            {"risk_score": 0.2, "risk_label": 0},
            {"risk_score": 0.5, "risk_label": 1},
            {"risk_score": 0.8, "risk_label": 1},
        ]
        
        drift_store.log_event(
            request_id="test-123",
            model_version="v1.0.0",
            instances=instances,
            predictions=predictions,
        )
        
        events = drift_store.read_events()
        summary = events[0]["prediction_summary"]
        
        assert summary["n_predictions"] == 3
        assert summary["n_high_risk"] == 2
        assert "mean_score" in summary
        assert "score_bins" in summary
    
    def test_read_events_limit(self, drift_store):
        """Deve respeitar limite de eventos lidos."""
        for i in range(10):
            drift_store.log_event(
                request_id=f"test-{i}",
                model_version="v1.0.0",
                instances=[{"feat1": 1.0}],
                predictions=[{"risk_score": 0.5, "risk_label": 0}],
            )
        
        events = drift_store.read_events(limit=5)
        
        assert len(events) == 5
    
    def test_read_empty_log(self, drift_store):
        """Deve retornar lista vazia se log não existe."""
        events = drift_store.read_events()
        
        assert events == []
    
    def test_timestamp_included(self, drift_store):
        """Deve incluir timestamp no evento."""
        drift_store.log_event(
            request_id="test-123",
            model_version="v1.0.0",
            instances=[{"feat1": 1.0}],
            predictions=[{"risk_score": 0.5, "risk_label": 0}],
        )
        
        events = drift_store.read_events()
        
        assert "timestamp" in events[0]
        assert events[0]["timestamp"].endswith("Z")
    
    def test_batch_stats_included(self, drift_store):
        """Deve incluir estatísticas do batch."""
        instances = [{"feat1": 5.0, "feat2": None}]
        predictions = [{"risk_score": 0.5, "risk_label": 0}]
        
        drift_store.log_event(
            request_id="test-123",
            model_version="v1.0.0",
            instances=instances,
            predictions=predictions,
        )
        
        events = drift_store.read_events()
        
        assert "batch_stats" in events[0]
        assert events[0]["batch_stats"]["n_instances"] == 1
