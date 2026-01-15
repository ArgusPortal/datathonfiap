"""Tests for build_baseline module."""

import json
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


class TestComputeNumericProfile:
    """Tests for numeric profile computation."""
    
    def test_basic_profile(self):
        """Test basic numeric profile."""
        from monitoring.build_baseline import compute_numeric_profile
        
        series = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        profile = compute_numeric_profile(series)
        
        assert profile["type"] == "numeric"
        assert profile["count"] == 10
        assert profile["missing_rate"] == 0.0
        assert profile["mean"] == 5.5
        assert "quantiles" in profile
        assert "p50" in profile["quantiles"]
    
    def test_profile_with_missing(self):
        """Test profile with missing values."""
        from monitoring.build_baseline import compute_numeric_profile
        
        series = pd.Series([1, 2, None, 4, 5, None, 7, 8, 9, 10])
        profile = compute_numeric_profile(series)
        
        assert profile["missing_rate"] == 0.2
        assert profile["count"] == 10
    
    def test_empty_series(self):
        """Test profile with empty series."""
        from monitoring.build_baseline import compute_numeric_profile
        
        series = pd.Series([], dtype=float)
        profile = compute_numeric_profile(series)
        
        assert profile["count"] == 0
        assert profile["missing_rate"] == 1.0


class TestComputeCategoricalProfile:
    """Tests for categorical profile computation."""
    
    def test_basic_profile(self):
        """Test basic categorical profile."""
        from monitoring.build_baseline import compute_categorical_profile
        
        series = pd.Series(["A", "B", "A", "C", "A", "B"])
        profile = compute_categorical_profile(series)
        
        assert profile["type"] == "categorical"
        assert profile["count"] == 6
        assert profile["n_unique"] == 3
        assert "top_values" in profile
        assert "A" in profile["top_values"]
        assert profile["top_values"]["A"]["count"] == 3
    
    def test_profile_top_k(self):
        """Test top-k limitation."""
        from monitoring.build_baseline import compute_categorical_profile
        
        # Create series with more than 10 unique values
        values = [f"cat_{i}" for i in range(15)] * 2
        series = pd.Series(values)
        profile = compute_categorical_profile(series, top_k=10)
        
        assert len(profile["top_values"]) <= 11  # top 10 + possible __other__


class TestComputeScoreProfile:
    """Tests for score profile computation."""
    
    def test_basic_profile(self):
        """Test basic score profile."""
        from monitoring.build_baseline import compute_score_profile
        
        scores = np.array([0.1, 0.2, 0.3, 0.5, 0.7, 0.8, 0.9])
        profile = compute_score_profile(scores)
        
        assert profile["count"] == 7
        assert "mean" in profile
        assert "quantiles" in profile
        assert "histogram" in profile
        assert len(profile["histogram"]["bin_edges"]) == 21  # 20 bins
    
    def test_profile_with_nan(self):
        """Test score profile with NaN values."""
        from monitoring.build_baseline import compute_score_profile
        
        scores = np.array([0.1, np.nan, 0.3, 0.5, np.nan])
        profile = compute_score_profile(scores)
        
        assert profile["count"] == 3  # Only non-NaN


class TestBuildFeatureProfile:
    """Tests for full feature profile building."""
    
    def test_build_profile(self):
        """Test building profiles for multiple features."""
        from monitoring.build_baseline import build_feature_profile
        
        df = pd.DataFrame({
            "numeric_feat": [1, 2, 3, 4, 5],
            "categorical_feat": ["A", "B", "A", "C", "B"],
        })
        
        feature_list = ["numeric_feat", "categorical_feat"]
        signature = {
            "numeric_feat": "float64",
            "categorical_feat": "object",
        }
        
        profiles = build_feature_profile(df, feature_list, signature)
        
        assert "numeric_feat" in profiles
        assert "categorical_feat" in profiles
        assert profiles["numeric_feat"]["type"] == "numeric"
        assert profiles["categorical_feat"]["type"] == "categorical"
    
    def test_missing_feature(self):
        """Test handling of missing features."""
        from monitoring.build_baseline import build_feature_profile
        
        df = pd.DataFrame({"existing_feat": [1, 2, 3]})
        feature_list = ["existing_feat", "missing_feat"]
        signature = {"existing_feat": "float64", "missing_feat": "float64"}
        
        profiles = build_feature_profile(df, feature_list, signature)
        
        assert "missing_feat" in profiles
        assert profiles["missing_feat"]["missing_rate"] == 1.0


class TestBuildBaseline:
    """Tests for full baseline building."""
    
    def test_build_baseline_parquet(self):
        """Test building baseline from parquet file."""
        from monitoring.build_baseline import build_baseline
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create test data
            df = pd.DataFrame({
                "idade_2023": [10, 15, 20, 25, 30],
                "fase_2023": [1, 2, 3, 4, 5],
                "em_risco": [0, 0, 1, 1, 1],
            })
            data_path = tmpdir / "test_data.parquet"
            df.to_parquet(data_path)
            
            # Create signature
            signature = {
                "input_schema": {
                    "idade_2023": "float64",
                    "fase_2023": "float64",
                }
            }
            signature_path = tmpdir / "signature.json"
            with open(signature_path, "w") as f:
                json.dump(signature, f)
            
            # Create metadata
            metadata = {
                "threshold_policy": {"threshold_value": 0.5}
            }
            metadata_path = tmpdir / "metadata.json"
            with open(metadata_path, "w") as f:
                json.dump(metadata, f)
            
            # Build baseline
            output_dir = tmpdir / "baseline"
            feat_path, score_path, meta_path = build_baseline(
                data_path=data_path,
                signature_path=signature_path,
                metadata_path=metadata_path,
                output_dir=output_dir,
                model_version="v1.0.0-test",
            )
            
            # Verify outputs
            assert feat_path.exists()
            assert score_path.exists()
            assert meta_path.exists()
            
            # Load and verify content
            with open(feat_path) as f:
                feature_profile = json.load(f)
            
            assert "idade_2023" in feature_profile
            assert "fase_2023" in feature_profile
            
            with open(meta_path) as f:
                baseline_meta = json.load(f)
            
            assert baseline_meta["model_version"] == "v1.0.0-test"
            assert baseline_meta["n_samples"] == 5
