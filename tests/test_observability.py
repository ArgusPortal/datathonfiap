"""Tests for observability module."""

import pytest
from datetime import datetime, timezone


class TestSafeSummarizeInputs:
    """Tests for input summarization."""
    
    def test_basic_summary(self):
        """Test basic input summary."""
        from app.observability import safe_summarize_inputs
        
        instances = [
            {"idade_2023": 15, "fase_2023": 3},
            {"idade_2023": 16, "fase_2023": 4},
        ]
        expected_features = ["idade_2023", "fase_2023"]
        
        summary = safe_summarize_inputs(instances, expected_features)
        
        assert summary["n_instances"] == 2
        assert summary["n_features_expected"] == 2
        assert summary["n_features_received"] == 2
    
    def test_pii_excluded(self):
        """Test PII is excluded from summary."""
        from app.observability import safe_summarize_inputs
        
        instances = [
            {"ra": "12345", "nome": "Test", "idade_2023": 15},
        ]
        expected_features = ["idade_2023"]
        
        summary = safe_summarize_inputs(instances, expected_features)
        
        # PII should not affect received count
        assert summary["n_features_received"] == 1
        # PII fields should not appear in numeric_summary or as explicit keys
        assert "12345" not in str(summary)  # ra value
        assert "Test" not in str(summary)   # nome value
    
    def test_missing_features_count(self):
        """Test missing features are counted."""
        from app.observability import safe_summarize_inputs
        
        instances = [
            {"idade_2023": 15},
            {"idade_2023": None, "fase_2023": 3},
        ]
        expected_features = ["idade_2023", "fase_2023"]
        
        summary = safe_summarize_inputs(instances, expected_features)
        
        assert summary["missing_features_count"] >= 1
    
    def test_extra_features_count(self):
        """Test extra features are counted."""
        from app.observability import safe_summarize_inputs
        
        instances = [
            {"idade_2023": 15, "extra_feat": 100},
        ]
        expected_features = ["idade_2023"]
        
        summary = safe_summarize_inputs(instances, expected_features)
        
        assert summary["extra_features_count"] == 1
    
    def test_empty_instances(self):
        """Test empty instances list."""
        from app.observability import safe_summarize_inputs
        
        summary = safe_summarize_inputs([], ["feat1", "feat2"])
        
        assert summary["n_instances"] == 0
    
    def test_numeric_summary_top_n(self):
        """Test numeric summary respects top_n."""
        from app.observability import safe_summarize_inputs
        
        instances = [
            {f"feat_{i}": float(i) for i in range(20)}
        ]
        expected_features = [f"feat_{i}" for i in range(20)]
        
        summary = safe_summarize_inputs(instances, expected_features, top_n=5)
        
        assert len(summary.get("numeric_summary", {})) <= 5


class TestSafeSummarizeOutputs:
    """Tests for output summarization."""
    
    def test_basic_summary(self):
        """Test basic output summary."""
        from app.observability import safe_summarize_outputs
        
        predictions = [
            {"risk_score": 0.3, "risk_label": 0},
            {"risk_score": 0.7, "risk_label": 1},
        ]
        
        summary = safe_summarize_outputs(predictions)
        
        assert summary["n_predictions"] == 2
        assert summary["score_min"] == 0.3
        assert summary["score_max"] == 0.7
        assert summary["positive_count"] == 1
        assert summary["positive_rate"] == 0.5
    
    def test_empty_predictions(self):
        """Test empty predictions list."""
        from app.observability import safe_summarize_outputs
        
        summary = safe_summarize_outputs([])
        
        assert summary["n_predictions"] == 0


class TestLogInferenceRequest:
    """Tests for inference request logging."""
    
    def test_log_entry_fields(self):
        """Test log entry has required fields."""
        from app.observability import log_inference_request
        
        log_entry = log_inference_request(
            request_id="test123",
            model_version="v1.0.0",
            instances=[{"idade_2023": 15}],
            predictions=[{"risk_score": 0.5, "risk_label": 0}],
            expected_features=["idade_2023"],
            latency_ms=10.5,
        )
        
        assert "timestamp" in log_entry
        assert log_entry["request_id"] == "test123"
        assert log_entry["model_version"] == "v1.0.0"
        assert log_entry["endpoint"] == "/predict"
        assert log_entry["latency_ms"] == 10.5
        assert log_entry["n_instances"] == 1
    
    def test_log_entry_no_pii(self):
        """Test log entry doesn't contain PII."""
        from app.observability import log_inference_request
        
        log_entry = log_inference_request(
            request_id="test123",
            model_version="v1.0.0",
            instances=[{"ra": "secret", "nome": "John", "idade_2023": 15}],
            predictions=[{"risk_score": 0.5, "risk_label": 0}],
            expected_features=["idade_2023"],
            latency_ms=10.5,
        )
        
        log_str = str(log_entry)
        assert "secret" not in log_str
        assert "John" not in log_str


class TestTimer:
    """Tests for Timer context manager."""
    
    def test_timer_measures_time(self):
        """Test timer measures elapsed time."""
        from app.observability import Timer
        import time
        
        with Timer() as timer:
            time.sleep(0.01)  # Sleep 10ms
        
        assert timer.elapsed_ms >= 10
        assert timer.elapsed_ms < 100  # Should be much less than 100ms
    
    def test_timer_returns_self(self):
        """Test timer returns self from __enter__."""
        from app.observability import Timer
        
        with Timer() as timer:
            assert isinstance(timer, Timer)
