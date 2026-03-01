"""
Testes unitários para módulo drift_store.
"""

import json

import numpy as np
import pytest

from app.drift_store import (
    DriftStore,
    aggregate_batch_stats,
    compute_feature_stats,
    normalize_bins,
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
        """Deve categorizar valores numéricos em 7 bins."""
        features = {
            "very_low": 1.0,
            "low": 3.0,
            "medium_low": 5.0,
            "medium": 6.5,
            "medium_high": 7.5,
            "high": 9.0,
        }

        stats = compute_feature_stats(features)

        assert stats["numeric_summary"]["very_low"] == "very_low"
        assert stats["numeric_summary"]["low"] == "low"
        assert stats["numeric_summary"]["medium_low"] == "medium_low"
        assert stats["numeric_summary"]["medium"] == "medium"
        assert stats["numeric_summary"]["medium_high"] == "medium_high"
        assert stats["numeric_summary"]["high"] == "high"

    def test_binary_bins(self):
        """Deve categorizar features binárias _missing como zero/one."""
        features = {
            "iaa_2023_missing": 0,
            "ian_2023_missing": 1,
        }

        stats = compute_feature_stats(features)

        assert stats["numeric_summary"]["iaa_2023_missing"] == "zero"
        assert stats["numeric_summary"]["ian_2023_missing"] == "one"

    def test_handles_string_values(self):
        """Deve lidar com valores string como cat_ prefix."""
        features = {"name": "test", "value": 5.0}

        stats = compute_feature_stats(features)

        assert stats["numeric_summary"]["name"] == "cat_test"
        assert "value" in stats["numeric_summary"]


class TestNormalizeBins:
    """Testes para função normalize_bins."""

    def test_collapse_fine_to_canonical(self):
        """Deve colapsar bins granulares em 3 bins canônicos."""
        dist = {
            "very_low": 10,
            "low": 5,
            "medium_low": 8,
            "medium": 3,
            "medium_high": 4,
            "high": 2,
        }

        result = normalize_bins(dist)

        assert result["low"] == 15  # very_low + low
        assert result["medium"] == 11  # medium_low + medium
        assert result["high"] == 6  # medium_high + high

    def test_collapse_binary_bins(self):
        """Deve colapsar zero/one em binary."""
        dist = {"zero": 7, "one": 3}

        result = normalize_bins(dist)

        assert result["binary"] == 10

    def test_preserve_categorical(self):
        """Deve preservar bins categóricos (cat_ prefix)."""
        dist = {"cat_A": 5, "cat_B": 3, "low": 2}

        result = normalize_bins(dist)

        assert result["cat_A"] == 5
        assert result["cat_B"] == 3
        assert result["low"] == 2

    def test_already_canonical(self):
        """Deve manter bins já canônicos."""
        dist = {"low": 10, "medium": 5, "high": 3}

        result = normalize_bins(dist)

        assert result == dist

    def test_empty(self):
        """Deve retornar vazio para distribuição vazia."""
        assert normalize_bins({}) == {}

    def test_mixed_old_new_bins(self):
        """Deve colapsar corretamente mix de bins antigos e novos."""
        dist = {"low": 10, "very_low": 5, "medium": 3}

        result = normalize_bins(dist)

        assert result["low"] == 15  # low + very_low
        assert result["medium"] == 3


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
        """Deve agregar distribuição de features com 7 bins."""
        instances = [
            {"score": 1.0},  # very_low
            {"score": 3.0},  # low
            {"score": 5.0},  # medium_low
            {"score": 6.5},  # medium
            {"score": 7.5},  # medium_high
            {"score": 9.0},  # high
        ]

        stats = aggregate_batch_stats(instances)

        dist = stats["feature_distribution"]["score"]
        assert dist.get("very_low", 0) == 1
        assert dist.get("low", 0) == 1
        assert dist.get("medium_low", 0) == 1
        assert dist.get("medium", 0) == 1
        assert dist.get("medium_high", 0) == 1
        assert dist.get("high", 0) == 1


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
        instances = [{"ra": "12345", "id": "abc", "nome": "João", "feat1": 5.0}]
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
        instances = [{"student_id": "STU001", "estudante_id": "EST001", "feat1": 5.0}]
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

    def test_bin_schema_version(self, drift_store):
        """Deve incluir bin_schema_version=2 nos eventos."""
        drift_store.log_event(
            request_id="test-123",
            model_version="v1.0.0",
            instances=[{"feat1": 5.0}],
            predictions=[{"risk_score": 0.5, "risk_label": 0}],
        )

        events = drift_store.read_events()

        assert events[0]["bin_schema_version"] == 2

    def test_clear_events(self, drift_store):
        """Deve limpar todos os eventos."""
        for i in range(5):
            drift_store.log_event(
                request_id=f"test-{i}",
                model_version="v1.0.0",
                instances=[{"feat1": 1.0}],
                predictions=[{"risk_score": 0.5, "risk_label": 0}],
            )

        count = drift_store.clear_events()

        assert count == 5
        assert drift_store.read_events() == []
        assert drift_store.event_count() == 0

    def test_clear_empty_log(self, drift_store):
        """Deve retornar 0 se log já está vazio."""
        count = drift_store.clear_events()

        assert count == 0

    def test_event_count(self, drift_store):
        """Deve contar eventos corretamente."""
        assert drift_store.event_count() == 0

        for i in range(3):
            drift_store.log_event(
                request_id=f"test-{i}",
                model_version="v1.0.0",
                instances=[{"feat1": 1.0}],
                predictions=[{"risk_score": 0.5, "risk_label": 0}],
            )

        assert drift_store.event_count() == 3
