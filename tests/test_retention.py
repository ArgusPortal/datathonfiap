"""
Tests for Phase 8 Retention Script.
"""

import json
import os
import pytest
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from monitoring.retention import (
    get_cutoff_date,
    filter_jsonl_file,
    cleanup_old_logs,
)


class TestGetCutoffDate:
    """Tests for cutoff date calculation."""
    
    def test_returns_datetime(self):
        """Should return datetime object."""
        result = get_cutoff_date(30)
        assert isinstance(result, datetime)
    
    def test_cutoff_in_past(self):
        """Cutoff should be in the past."""
        result = get_cutoff_date(30)
        assert result < datetime.now(timezone.utc)
    
    def test_cutoff_days_correct(self):
        """Cutoff should be approximately N days ago."""
        result = get_cutoff_date(7)
        expected = datetime.now(timezone.utc) - timedelta(days=7)
        
        # Allow 1 minute tolerance
        diff = abs((result - expected).total_seconds())
        assert diff < 60


class TestFilterJsonlFile:
    """Tests for JSONL file filtering."""
    
    def test_filter_old_records(self):
        """Should filter records older than cutoff."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            # Old record
            old_time = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
            f.write(json.dumps({"timestamp": old_time, "data": "old"}) + "\n")
            
            # New record
            new_time = datetime.now(timezone.utc).isoformat()
            f.write(json.dumps({"timestamp": new_time, "data": "new"}) + "\n")
            
            temp_path = Path(f.name)
        
        try:
            cutoff = get_cutoff_date(30)
            result = filter_jsonl_file(temp_path, cutoff, dry_run=False)
            
            assert result["total"] == 2
            assert result["removed"] == 1
            assert result["retained"] == 1
            
            # Verify file content
            with open(temp_path) as f:
                lines = f.readlines()
                assert len(lines) == 1
                assert "new" in lines[0]
        finally:
            temp_path.unlink()
    
    def test_dry_run_no_changes(self):
        """Dry run should not modify file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            old_time = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
            f.write(json.dumps({"timestamp": old_time, "data": "old"}) + "\n")
            temp_path = Path(f.name)
        
        try:
            cutoff = get_cutoff_date(30)
            result = filter_jsonl_file(temp_path, cutoff, dry_run=True)
            
            assert result["removed"] == 1
            
            # File should be unchanged
            with open(temp_path) as f:
                lines = f.readlines()
                assert len(lines) == 1
        finally:
            temp_path.unlink()
    
    def test_nonexistent_file(self):
        """Should handle nonexistent file gracefully."""
        cutoff = get_cutoff_date(30)
        result = filter_jsonl_file(Path("/nonexistent/file.jsonl"), cutoff)
        
        assert result["skipped"] is True
        assert result["total"] == 0
    
    def test_empty_file(self):
        """Should handle empty file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            cutoff = get_cutoff_date(30)
            result = filter_jsonl_file(temp_path, cutoff)
            
            assert result["total"] == 0
            assert result["removed"] == 0
        finally:
            temp_path.unlink()
    
    def test_keep_recent_records(self):
        """Should keep all recent records."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            # All recent records
            for i in range(5):
                new_time = (datetime.now(timezone.utc) - timedelta(days=i)).isoformat()
                f.write(json.dumps({"timestamp": new_time, "id": i}) + "\n")
            
            temp_path = Path(f.name)
        
        try:
            cutoff = get_cutoff_date(30)
            result = filter_jsonl_file(temp_path, cutoff, dry_run=False)
            
            assert result["total"] == 5
            assert result["removed"] == 0
            assert result["retained"] == 5
        finally:
            temp_path.unlink()


class TestCleanupOldLogs:
    """Tests for cleanup_old_logs function."""
    
    def test_cleanup_multiple_files(self):
        """Should clean up multiple target files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            logs_dir = base_dir / "logs"
            logs_dir.mkdir()
            
            # Create test file
            test_file = logs_dir / "inference_store.jsonl"
            old_time = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
            new_time = datetime.now(timezone.utc).isoformat()
            
            with open(test_file, 'w') as f:
                f.write(json.dumps({"timestamp": old_time}) + "\n")
                f.write(json.dumps({"timestamp": new_time}) + "\n")
            
            # Run cleanup (with custom targets since defaults won't exist)
            import monitoring.retention as retention
            original_targets = retention.RETENTION_TARGETS
            retention.RETENTION_TARGETS = ["logs/inference_store.jsonl"]
            
            try:
                summary = cleanup_old_logs(base_dir, 30, dry_run=False)
                
                assert "files" in summary
                assert summary["totals"]["removed"] >= 1
            finally:
                retention.RETENTION_TARGETS = original_targets
    
    def test_dry_run_summary(self):
        """Dry run should return summary without changes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            summary = cleanup_old_logs(Path(tmpdir), 30, dry_run=True)
            
            assert summary["dry_run"] is True
            assert "cutoff_date" in summary
            assert "retention_days" in summary


class TestRetentionIntegration:
    """Integration tests for retention functionality."""
    
    def test_full_retention_cycle(self):
        """Test complete retention cycle."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            logs_dir = base_dir / "logs"
            logs_dir.mkdir()
            
            # Create file with mixed old/new records
            test_file = logs_dir / "test_store.jsonl"
            
            records = [
                # Old records (should be removed)
                {"timestamp": (datetime.now(timezone.utc) - timedelta(days=40)).isoformat(), "id": 1},
                {"timestamp": (datetime.now(timezone.utc) - timedelta(days=35)).isoformat(), "id": 2},
                # New records (should be kept)
                {"timestamp": (datetime.now(timezone.utc) - timedelta(days=20)).isoformat(), "id": 3},
                {"timestamp": (datetime.now(timezone.utc) - timedelta(days=5)).isoformat(), "id": 4},
                {"timestamp": datetime.now(timezone.utc).isoformat(), "id": 5},
            ]
            
            with open(test_file, 'w') as f:
                for record in records:
                    f.write(json.dumps(record) + "\n")
            
            # Apply retention
            cutoff = get_cutoff_date(30)
            result = filter_jsonl_file(test_file, cutoff, dry_run=False)
            
            # Verify results
            assert result["total"] == 5
            assert result["removed"] == 2
            assert result["retained"] == 3
            
            # Verify file content
            with open(test_file) as f:
                remaining = [json.loads(line) for line in f]
                assert len(remaining) == 3
                assert all(r["id"] in [3, 4, 5] for r in remaining)
