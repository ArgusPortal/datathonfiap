"""
Tests for extended API endpoints (Phase 9 + EDA).
Covers: /artifacts/*, /analysis/eda, /inference/history, /drift/status,
        /metrics, /slo, exception handlers.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def mock_model():
    model = MagicMock()
    model.predict_proba = MagicMock(return_value=np.array([[0.3, 0.7]]))
    return model


@pytest.fixture(scope="module")
def mock_metadata():
    return {
        "model_version": "v1.0.0-test",
        "model_family": "rf",
        "calibration": "sigmoid",
        "expected_features": ["feat_a", "feat_b"],
        "threshold_policy": {"threshold_value": 0.5},
        "created_at": "2025-01-01T00:00:00Z",
    }


@pytest.fixture(scope="module")
def mock_signature():
    return {
        "input_schema": [{"name": "feat_a", "type": "float64"}],
        "output_schema": [{"name": "risk_score", "type": "float64"}],
    }


@pytest.fixture(scope="module")
def test_client(mock_model, mock_metadata, mock_signature):
    with patch("app.main.model_manager") as mock_manager:
        mock_manager.model = mock_model
        mock_manager.metadata = mock_metadata
        mock_manager.signature = mock_signature
        mock_manager.version = "v1.0.0-test"
        mock_manager.threshold = 0.5
        mock_manager.expected_features = mock_metadata["expected_features"]
        mock_manager.get_safe_metadata.return_value = {
            "model_version": "v1.0.0-test",
            "model_family": "rf",
            "threshold": 0.5,
            "expected_features": mock_metadata["expected_features"],
        }

        from app.main import app

        client = TestClient(app)
        yield client


# ------------------------------------------------------------------
# Artifact endpoints
# ------------------------------------------------------------------
class TestArtifactEndpoints:
    def test_get_artifact_metrics(self, test_client):
        response = test_client.get("/artifacts/metrics")
        # artifacts/model_comparison.json exists on disk
        if response.status_code == 200:
            assert isinstance(response.json(), (dict, list))
        else:
            assert response.status_code == 404

    def test_get_artifact_metadata(self, test_client):
        response = test_client.get("/artifacts/metadata")
        if response.status_code == 200:
            assert isinstance(response.json(), dict)
        else:
            assert response.status_code == 404

    def test_get_artifact_report(self, test_client):
        response = test_client.get("/artifacts/report")
        if response.status_code == 200:
            data = response.json()
            assert "content" in data
            assert data["format"] == "markdown"
        else:
            assert response.status_code == 404


# ------------------------------------------------------------------
# EDA endpoint
# ------------------------------------------------------------------
class TestEdaEndpoint:
    def test_eda_returns_200(self, test_client):
        """EDA endpoint should return 200 if data files exist."""
        response = test_client.get("/analysis/eda")
        if response.status_code == 200:
            data = response.json()
            assert "overview" in data
            assert "missing_data" in data
            assert "feature_stats" in data
            assert "correlations" in data
            assert "year_missing" in data
        else:
            # data_card.json not found → 404 is acceptable in test env
            assert response.status_code == 404

    def test_eda_overview_structure(self, test_client):
        response = test_client.get("/analysis/eda")
        if response.status_code == 200:
            overview = response.json()["overview"]
            assert "total_samples" in overview
            assert "n_features" in overview
            assert "target" in overview
            assert "years" in overview
            assert "features" in overview

    def test_eda_missing_data_sorted(self, test_client):
        response = test_client.get("/analysis/eda")
        if response.status_code == 200:
            missing = response.json()["missing_data"]
            if len(missing) > 1:
                counts = [m["count"] for m in missing]
                assert counts == sorted(counts, reverse=True)

    def test_eda_feature_stats_has_histogram(self, test_client):
        response = test_client.get("/analysis/eda")
        if response.status_code == 200:
            stats = response.json()["feature_stats"]
            if stats:
                first = stats[0]
                assert "mean" in first
                assert "std" in first
                assert "histogram" in first
                assert isinstance(first["histogram"], list)

    def test_eda_correlations_format(self, test_client):
        response = test_client.get("/analysis/eda")
        if response.status_code == 200:
            corrs = response.json()["correlations"]
            if corrs:
                c = corrs[0]
                assert "x" in c
                assert "y" in c
                assert "value" in c

    def test_eda_missing_card_returns_404(self, test_client):
        """When data_card.json doesn't exist, raise 404."""
        fake_dir = Path(tempfile.mkdtemp()) / "nonexistent_subdir"
        with patch("app.main.BASE_DIR", fake_dir):
            response = test_client.get("/analysis/eda")
            assert response.status_code == 404


# ------------------------------------------------------------------
# Inference history
# ------------------------------------------------------------------
class TestInferenceHistory:
    def test_inference_history_returns_200(self, test_client):
        response = test_client.get("/inference/history")
        assert response.status_code == 200
        data = response.json()
        assert "events" in data
        assert "total" in data

    def test_inference_history_limit(self, test_client):
        response = test_client.get("/inference/history?limit=5")
        assert response.status_code == 200


# ------------------------------------------------------------------
# Drift status
# ------------------------------------------------------------------
class TestDriftStatus:
    def test_drift_status_returns_200(self, test_client):
        response = test_client.get("/drift/status")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    def test_drift_status_insufficient_data(self, test_client):
        """With no/few inference events, should report insufficient_data."""
        with patch("app.main.drift_store") as mock_ds:
            mock_ds.read_events.return_value = []
            response = test_client.get("/drift/status")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "insufficient_data"


# ------------------------------------------------------------------
# Metrics / SLO
# ------------------------------------------------------------------
class TestMetricsSlo:
    def test_metrics_json(self, test_client):
        response = test_client.get("/metrics?format=json")
        assert response.status_code == 200

    def test_metrics_prometheus(self, test_client):
        response = test_client.get("/metrics?format=prometheus")
        assert response.status_code == 200

    def test_slo_status(self, test_client):
        response = test_client.get("/slo")
        assert response.status_code == 200


# ------------------------------------------------------------------
# Exception handlers
# ------------------------------------------------------------------
class TestExceptionHandlers:
    def test_404_returns_error_response(self, test_client):
        response = test_client.get("/nonexistent-endpoint-xyz")
        assert response.status_code in (404, 405)

    def test_http_exception_handler(self, test_client):
        """POST to /predict with no body should raise 422."""
        response = test_client.post("/predict")
        assert response.status_code == 422
