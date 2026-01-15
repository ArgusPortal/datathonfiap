"""Tests for drift_report module."""

import json
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


class TestComputePSI:
    """Tests for PSI computation."""
    
    def test_identical_distributions(self):
        """Test PSI for identical distributions."""
        from monitoring.drift_report import compute_psi
        
        baseline = [0.25, 0.25, 0.25, 0.25]
        current = [0.25, 0.25, 0.25, 0.25]
        
        psi = compute_psi(baseline, current)
        assert psi < 0.01  # Should be very close to 0
    
    def test_different_distributions(self):
        """Test PSI for different distributions."""
        from monitoring.drift_report import compute_psi
        
        baseline = [0.25, 0.25, 0.25, 0.25]
        current = [0.50, 0.20, 0.20, 0.10]
        
        psi = compute_psi(baseline, current)
        assert psi > 0.05  # Should show some drift
    
    def test_handles_zeros(self):
        """Test PSI handles zero frequencies."""
        from monitoring.drift_report import compute_psi
        
        baseline = [0.5, 0.5, 0.0, 0.0]
        current = [0.3, 0.3, 0.2, 0.2]
        
        # Should not raise error due to epsilon smoothing
        psi = compute_psi(baseline, current)
        assert psi > 0


class TestComputeNumericPSI:
    """Tests for numeric feature PSI."""
    
    def test_numeric_psi(self):
        """Test numeric PSI computation."""
        from monitoring.drift_report import compute_numeric_psi
        
        baseline_profile = {
            "quantiles": {"p05": 1, "p25": 3, "p50": 5, "p75": 7, "p95": 9},
            "min": 0,
            "max": 10,
        }
        
        # Values similar to baseline
        current_values = [2, 3, 4, 5, 6, 7, 8]
        
        psi, details = compute_numeric_psi(baseline_profile, current_values)
        
        assert psi >= 0
        assert "bin_edges" in details
    
    def test_empty_current(self):
        """Test handling of empty current values."""
        from monitoring.drift_report import compute_numeric_psi
        
        baseline_profile = {"quantiles": {"p50": 5}}
        psi, details = compute_numeric_psi(baseline_profile, [])
        
        assert psi == 0.0
        assert "error" in details


class TestComputeCategoricalPSI:
    """Tests for categorical feature PSI."""
    
    def test_categorical_psi(self):
        """Test categorical PSI computation."""
        from monitoring.drift_report import compute_categorical_psi
        
        baseline_profile = {
            "top_values": {
                "A": {"freq": 0.5},
                "B": {"freq": 0.3},
                "C": {"freq": 0.2},
            }
        }
        
        current_values = ["A", "A", "A", "B", "B", "C"]
        
        psi, details = compute_categorical_psi(baseline_profile, current_values)
        
        assert psi >= 0
        assert "categories" in details


class TestGetStatus:
    """Tests for status determination."""
    
    def test_green_status(self):
        """Test green status."""
        from monitoring.drift_report import get_status
        
        status = get_status(0.05, 0.1, 0.25)
        assert status == "green"
    
    def test_yellow_status(self):
        """Test yellow status."""
        from monitoring.drift_report import get_status
        
        status = get_status(0.15, 0.1, 0.25)
        assert status == "yellow"
    
    def test_red_status(self):
        """Test red status."""
        from monitoring.drift_report import get_status
        
        status = get_status(0.30, 0.1, 0.25)
        assert status == "red"


class TestAnalyzeDrift:
    """Tests for drift analysis."""
    
    def test_no_data_status(self):
        """Test status when no inference data."""
        from monitoring.drift_report import analyze_drift
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create baseline
            baseline_dir = tmpdir / "baseline"
            version_dir = baseline_dir / "v1.0.0"
            version_dir.mkdir(parents=True)
            
            # Feature profile
            with open(version_dir / "feature_profile.json", "w") as f:
                json.dump({"idade_2023": {"type": "numeric", "quantiles": {"p50": 15}}}, f)
            
            with open(version_dir / "score_profile.json", "w") as f:
                json.dump({"mean": 0.5, "histogram": {"frequencies": [0.05] * 20}}, f)
            
            with open(version_dir / "baseline_metadata.json", "w") as f:
                json.dump({"model_version": "v1.0.0", "created_at": "2024-01-01"}, f)
            
            # Empty inference store
            inference_dir = tmpdir / "inference_store"
            inference_dir.mkdir()
            
            result = analyze_drift(
                baseline_dir=baseline_dir,
                inference_store_dir=inference_dir,
                model_version="v1.0.0",
                last_n_days=7
            )
            
            assert result["status"] == "no_data"
    
    def test_analyze_with_data(self):
        """Test drift analysis with inference data."""
        from monitoring.drift_report import analyze_drift
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create baseline
            baseline_dir = tmpdir / "baseline"
            version_dir = baseline_dir / "v1.0.0"
            version_dir.mkdir(parents=True)
            
            with open(version_dir / "feature_profile.json", "w") as f:
                json.dump({
                    "idade_2023": {
                        "type": "numeric",
                        "quantiles": {"p05": 10, "p25": 12, "p50": 15, "p75": 18, "p95": 20},
                        "missing_rate": 0.0,
                        "min": 8,
                        "max": 22,
                    }
                }, f)
            
            with open(version_dir / "score_profile.json", "w") as f:
                json.dump({
                    "mean": 0.5,
                    "histogram": {
                        "bin_edges": [i/20 for i in range(21)],
                        "frequencies": [0.05] * 20,
                    }
                }, f)
            
            with open(version_dir / "baseline_metadata.json", "w") as f:
                json.dump({
                    "model_version": "v1.0.0",
                    "created_at": "2024-01-01",
                    "feature_list": ["idade_2023"],
                }, f)
            
            # Create inference data
            inference_dir = tmpdir / "inference_store"
            inference_dir.mkdir()
            
            today = datetime.now().strftime("%Y-%m-%d")
            df = pd.DataFrame({
                "timestamp": [datetime.now(timezone.utc).isoformat()],
                "request_id": ["test123"],
                "model_version": ["v1.0.0"],
                "n_instances": [1],
                "risk_score_mean": [0.6],
                "numeric_means": [json.dumps({"idade_2023": 16.0})],
            })
            df.to_parquet(inference_dir / f"inferences_{today}.parquet")
            
            result = analyze_drift(
                baseline_dir=baseline_dir,
                inference_store_dir=inference_dir,
                model_version="v1.0.0",
                last_n_days=7
            )
            
            assert "global_status" in result
            assert "feature_drift" in result
            assert "score_drift" in result


class TestGenerateHTMLReport:
    """Tests for HTML report generation."""
    
    def test_generate_html(self):
        """Test HTML report generation."""
        from monitoring.drift_report import generate_html_report
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report.html"
            
            drift_metrics = {
                "model_version": "v1.0.0",
                "window_start": "2024-01-01T00:00:00",
                "window_end": "2024-01-07T00:00:00",
                "n_requests": 100,
                "n_instances": 500,
                "global_status": "green",
                "feature_drift": {
                    "idade_2023": {
                        "psi": 0.05,
                        "missing_delta": 0.0,
                        "status": "green",
                        "type": "numeric",
                    }
                },
                "score_drift": {
                    "psi": 0.03,
                    "baseline_mean": 0.5,
                    "current_mean": 0.52,
                    "delta_mean": 0.02,
                    "status": "green",
                },
                "summary": {
                    "n_features": 1,
                    "n_red": 0,
                    "n_yellow": 0,
                    "n_green": 1,
                },
                "thresholds_used": {
                    "feature_psi_warn": 0.1,
                    "feature_psi_alert": 0.25,
                },
            }
            
            generate_html_report(drift_metrics, output_path)
            
            assert output_path.exists()
            
            # Check content
            content = output_path.read_text(encoding="utf-8")
            assert "v1.0.0" in content
            assert "Drift Report" in content
            assert "idade_2023" in content
    
    def test_html_status_colors(self):
        """Test HTML report shows correct status colors."""
        from monitoring.drift_report import generate_html_report
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report.html"
            
            drift_metrics = {
                "model_version": "v1.0.0",
                "window_start": "2024-01-01",
                "window_end": "2024-01-07",
                "n_requests": 10,
                "n_instances": 10,
                "global_status": "red",
                "feature_drift": {
                    "feat1": {"psi": 0.3, "missing_delta": 0.0, "status": "red", "type": "numeric"},
                },
                "score_drift": {"psi": 0.3, "baseline_mean": 0.5, "current_mean": 0.8, "delta_mean": 0.3, "status": "red"},
                "summary": {"n_features": 1, "n_red": 1, "n_yellow": 0, "n_green": 0},
                "thresholds_used": {"feature_psi_warn": 0.1, "feature_psi_alert": 0.25},
            }
            
            generate_html_report(drift_metrics, output_path)
            
            content = output_path.read_text(encoding="utf-8")
            assert "#dc3545" in content  # Red color
            assert "CRÍTICO" in content
