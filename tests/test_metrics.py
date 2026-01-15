"""
Tests for Phase 8 Metrics Module.
"""

import pytest
import time

from app.metrics import (
    MetricBucket,
    Counter,
    MetricsStore,
    metrics,
    SLO_P95_MS,
    SLO_ERROR_RATE,
)


class TestMetricBucket:
    """Tests for MetricBucket."""
    
    def setup_method(self):
        """Create fresh bucket for each test."""
        self.bucket = MetricBucket(window_seconds=60)
    
    def test_add_value(self):
        """Should add values to bucket."""
        self.bucket.add(100)
        assert self.bucket.count() == 1
    
    def test_count(self):
        """Should count values correctly."""
        for i in range(5):
            self.bucket.add(i)
        assert self.bucket.count() == 5
    
    def test_sum(self):
        """Should sum values correctly."""
        self.bucket.add(10)
        self.bucket.add(20)
        self.bucket.add(30)
        assert self.bucket.sum() == 60
    
    def test_mean(self):
        """Should calculate mean correctly."""
        self.bucket.add(10)
        self.bucket.add(20)
        self.bucket.add(30)
        assert self.bucket.mean() == 20
    
    def test_mean_empty(self):
        """Mean of empty bucket should be None."""
        assert self.bucket.mean() is None
    
    def test_percentile_p50(self):
        """Should calculate P50 correctly."""
        for i in range(1, 101):
            self.bucket.add(i)
        p50 = self.bucket.percentile(50)
        assert 49 <= p50 <= 51
    
    def test_percentile_p95(self):
        """Should calculate P95 correctly."""
        for i in range(1, 101):
            self.bucket.add(i)
        p95 = self.bucket.percentile(95)
        assert 94 <= p95 <= 96
    
    def test_percentile_empty(self):
        """Percentile of empty bucket should be None."""
        assert self.bucket.percentile(50) is None
    
    def test_reset(self):
        """Reset should clear bucket."""
        self.bucket.add(100)
        self.bucket.reset()
        assert self.bucket.count() == 0


class TestCounter:
    """Tests for Counter."""
    
    def setup_method(self):
        """Create fresh counter for each test."""
        self.counter = Counter()
    
    def test_initial_value(self):
        """Initial value should be 0."""
        assert self.counter.get() == 0
    
    def test_increment(self):
        """Should increment by 1 by default."""
        self.counter.inc()
        assert self.counter.get() == 1
    
    def test_increment_custom_amount(self):
        """Should increment by custom amount."""
        self.counter.inc(5)
        assert self.counter.get() == 5
    
    def test_multiple_increments(self):
        """Multiple increments should accumulate."""
        self.counter.inc()
        self.counter.inc()
        self.counter.inc()
        assert self.counter.get() == 3
    
    def test_reset(self):
        """Reset should set counter to 0."""
        self.counter.inc(10)
        self.counter.reset()
        assert self.counter.get() == 0


class TestMetricsStore:
    """Tests for MetricsStore."""
    
    def setup_method(self):
        """Create fresh metrics store for each test."""
        self.store = MetricsStore()
    
    def test_record_request_success(self):
        """Should record successful request."""
        self.store.record_request(50.0, success=True)
        
        assert self.store.requests_total.get() == 1
        assert self.store.requests_success.get() == 1
        assert self.store.requests_error.get() == 0
    
    def test_record_request_error(self):
        """Should record failed request."""
        self.store.record_request(50.0, success=False)
        
        assert self.store.requests_total.get() == 1
        assert self.store.requests_success.get() == 0
        assert self.store.requests_error.get() == 1
    
    def test_record_prediction_positive(self):
        """Should record positive prediction."""
        self.store.record_prediction(0.5, threshold=0.04)
        
        assert self.store.predictions_total.get() == 1
        assert self.store.predictions_positive.get() == 1
        assert self.store.predictions_negative.get() == 0
    
    def test_record_prediction_negative(self):
        """Should record negative prediction."""
        self.store.record_prediction(0.01, threshold=0.04)
        
        assert self.store.predictions_total.get() == 1
        assert self.store.predictions_positive.get() == 0
        assert self.store.predictions_negative.get() == 1
    
    def test_set_model_info(self):
        """Should set model information."""
        self.store.set_model_info("v1.1.0")
        
        assert self.store.model_version == "v1.1.0"
        assert self.store.model_loaded_at > 0
    
    def test_get_slo_status_healthy(self):
        """Should return healthy SLO status."""
        # Record some good requests
        for _ in range(100):
            self.store.record_request(50.0, success=True)
        
        status = self.store.get_slo_status()
        
        assert status["overall_healthy"] is True
        assert status["latency_slo_met"] is True
        assert status["error_rate_slo_met"] is True
    
    def test_get_slo_status_latency_breach(self):
        """Should detect latency SLO breach."""
        # Record requests with high latency
        for _ in range(100):
            self.store.record_request(500.0, success=True)
        
        status = self.store.get_slo_status()
        
        assert status["latency_slo_met"] is False
    
    def test_get_slo_status_error_breach(self):
        """Should detect error rate SLO breach."""
        # Record mostly errors
        for _ in range(90):
            self.store.record_request(50.0, success=False)
        for _ in range(10):
            self.store.record_request(50.0, success=True)
        
        status = self.store.get_slo_status()
        
        assert status["error_rate_slo_met"] is False
    
    def test_get_summary(self):
        """Should return complete summary."""
        self.store.set_model_info("v1.0.0")
        self.store.record_request(50.0, success=True)
        self.store.record_prediction(0.5, threshold=0.04)
        
        summary = self.store.get_summary()
        
        assert "uptime_seconds" in summary
        assert "requests" in summary
        assert "latency_ms" in summary
        assert "predictions" in summary
        assert "model" in summary
        assert "slo" in summary
    
    def test_to_prometheus_format(self):
        """Should export in Prometheus format."""
        self.store.set_model_info("v1.0.0")
        self.store.record_request(50.0, success=True)
        
        output = self.store.to_prometheus_format()
        
        assert "api_requests_total 1" in output
        assert "api_model_info" in output
        assert "api_uptime_seconds" in output
    
    def test_reset(self):
        """Reset should clear all metrics."""
        self.store.record_request(50.0, success=True)
        self.store.record_prediction(0.5, threshold=0.04)
        self.store.reset()
        
        assert self.store.requests_total.get() == 0
        assert self.store.predictions_total.get() == 0


class TestGlobalMetrics:
    """Tests for global metrics instance."""
    
    def setup_method(self):
        """Reset global metrics before each test."""
        metrics.reset()
    
    def test_global_instance_exists(self):
        """Global metrics instance should exist."""
        assert metrics is not None
        assert isinstance(metrics, MetricsStore)
    
    def test_global_record_request(self):
        """Should be able to record on global instance."""
        metrics.record_request(50.0, success=True)
        assert metrics.requests_total.get() == 1


class TestSloConfiguration:
    """Tests for SLO configuration."""
    
    def test_slo_p95_default(self):
        """SLO_P95_MS should have default value."""
        assert SLO_P95_MS > 0
    
    def test_slo_error_rate_default(self):
        """SLO_ERROR_RATE should have default value."""
        assert 0 < SLO_ERROR_RATE < 1
