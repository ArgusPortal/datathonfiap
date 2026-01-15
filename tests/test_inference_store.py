"""Tests for inference store module."""

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest


class TestInferenceStore:
    """Tests for InferenceStore class."""
    
    def test_create_store(self):
        """Test store creation."""
        from monitoring.inference_store import InferenceStore
        
        with tempfile.TemporaryDirectory() as tmpdir:
            store = InferenceStore(Path(tmpdir), "aggregate_only", "parquet")
            assert store.store_dir.exists()
            assert store.privacy_mode == "aggregate_only"
    
    def test_sanitize_features(self):
        """Test PII removal from features."""
        from monitoring.inference_store import InferenceStore
        
        with tempfile.TemporaryDirectory() as tmpdir:
            store = InferenceStore(Path(tmpdir))
            
            features = {
                "ra": "12345",
                "nome": "Test Student",
                "idade_2023": 15,
                "fase_2023": 3,
            }
            
            sanitized = store._sanitize_features(features, ["idade_2023", "fase_2023"])
            
            assert "ra" not in sanitized
            assert "nome" not in sanitized
            assert "idade_2023" in sanitized
            assert sanitized["idade_2023"] == 15
    
    def test_append_event_aggregate_mode(self):
        """Test appending event in aggregate mode."""
        from monitoring.inference_store import InferenceStore
        
        with tempfile.TemporaryDirectory() as tmpdir:
            store = InferenceStore(Path(tmpdir), "aggregate_only", "parquet")
            store._buffer_size = 1  # Flush immediately
            
            store.append_event(
                request_id="test123",
                model_version="v1.0.0",
                timestamp=datetime.now(timezone.utc),
                instances=[{"idade_2023": 15, "fase_2023": 3}],
                predictions=[{"risk_score": 0.7, "risk_label": 1}],
                expected_features=["idade_2023", "fase_2023"],
                latency_ms=10.5,
            )
            
            # Check file was created
            files = list(Path(tmpdir).glob("inferences_*.parquet"))
            assert len(files) == 1
    
    def test_append_event_row_level_mode(self):
        """Test appending event in row-level mode."""
        from monitoring.inference_store import InferenceStore
        
        with tempfile.TemporaryDirectory() as tmpdir:
            store = InferenceStore(Path(tmpdir), "sanitized_row_level", "csv")
            store._buffer_size = 1
            
            store.append_event(
                request_id="test123",
                model_version="v1.0.0",
                timestamp=datetime.now(timezone.utc),
                instances=[{"idade_2023": 15}],
                predictions=[{"risk_score": 0.5, "risk_label": 0}],
                expected_features=["idade_2023"],
            )
            
            files = list(Path(tmpdir).glob("inferences_*.csv"))
            assert len(files) == 1
    
    def test_read_events(self):
        """Test reading events from store."""
        from monitoring.inference_store import InferenceStore
        
        with tempfile.TemporaryDirectory() as tmpdir:
            store = InferenceStore(Path(tmpdir), "aggregate_only", "parquet")
            store._buffer_size = 1
            
            # Add some events
            for i in range(3):
                store.append_event(
                    request_id=f"test{i}",
                    model_version="v1.0.0",
                    timestamp=datetime.now(timezone.utc),
                    instances=[{"idade_2023": 15 + i}],
                    predictions=[{"risk_score": 0.5, "risk_label": 0}],
                    expected_features=["idade_2023"],
                )
            
            events = store.read_events()
            assert len(events) == 3
    
    def test_no_pii_in_stored_events(self):
        """Test that PII is not stored."""
        from monitoring.inference_store import InferenceStore
        import pandas as pd
        
        with tempfile.TemporaryDirectory() as tmpdir:
            store = InferenceStore(Path(tmpdir), "aggregate_only", "parquet")
            store._buffer_size = 1
            
            store.append_event(
                request_id="test123",
                model_version="v1.0.0",
                timestamp=datetime.now(timezone.utc),
                instances=[{
                    "ra": "sensitive_id",
                    "nome": "sensitive_name",
                    "idade_2023": 15,
                }],
                predictions=[{"risk_score": 0.5, "risk_label": 0}],
                expected_features=["idade_2023"],
            )
            
            # Read back and check
            files = list(Path(tmpdir).glob("inferences_*.parquet"))
            df = pd.read_parquet(files[0])
            
            # Convert to string and check for PII
            content = df.to_string()
            assert "sensitive_id" not in content
            assert "sensitive_name" not in content


class TestComputeStats:
    """Tests for statistics computation."""
    
    def test_compute_numeric_stats(self):
        """Test numeric stats computation."""
        from monitoring.inference_store import InferenceStore
        
        with tempfile.TemporaryDirectory() as tmpdir:
            store = InferenceStore(Path(tmpdir))
            
            instances = [
                {"idade_2023": 10, "fase_2023": 3},
                {"idade_2023": 15, "fase_2023": 4},
                {"idade_2023": 20, "fase_2023": 5},
            ]
            
            stats = store._compute_numeric_stats(instances, ["idade_2023", "fase_2023"])
            
            assert "idade_2023" in stats
            assert stats["idade_2023"]["mean"] == 15.0
            assert stats["idade_2023"]["min"] == 10.0
            assert stats["idade_2023"]["max"] == 20.0
    
    def test_count_missing(self):
        """Test missing value counting."""
        from monitoring.inference_store import InferenceStore
        
        with tempfile.TemporaryDirectory() as tmpdir:
            store = InferenceStore(Path(tmpdir))
            
            instances = [
                {"idade_2023": 10, "fase_2023": None},
                {"idade_2023": None, "fase_2023": 4},
                {"idade_2023": 20, "fase_2023": 5},
            ]
            
            missing = store._count_missing(instances, ["idade_2023", "fase_2023"])
            
            assert missing["idade_2023"] == 1
            assert missing["fase_2023"] == 1


class TestGetInferenceStore:
    """Tests for factory function."""
    
    def test_get_inference_store_singleton(self):
        """Test that get_inference_store returns same instance."""
        from monitoring import inference_store as module
        
        # Reset singleton
        module._inference_store = None
        
        with tempfile.TemporaryDirectory() as tmpdir:
            store1 = module.get_inference_store(Path(tmpdir))
            store2 = module.get_inference_store(Path(tmpdir))
            
            assert store1 is store2
