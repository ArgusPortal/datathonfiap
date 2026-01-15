"""
Tests for Phase 8 Audit Module.
"""

import os
import pytest
import tempfile
from pathlib import Path

from app.audit import (
    get_git_sha,
    get_git_branch,
    hash_file,
    hash_dict,
    hash_model_artifact,
    AuditTrail,
    ModelLineage,
    create_inference_audit_record,
    audit_trail,
    init_model_lineage,
    get_model_lineage,
)


class TestGitHelpers:
    """Tests for git helper functions."""
    
    def test_get_git_sha_returns_string(self):
        """Should return a string."""
        result = get_git_sha()
        assert isinstance(result, str)
    
    def test_get_git_sha_length(self):
        """Should return truncated SHA or 'unknown'."""
        result = get_git_sha()
        assert len(result) <= 12 or result == "unknown"
    
    def test_get_git_branch_returns_string(self):
        """Should return a string."""
        result = get_git_branch()
        assert isinstance(result, str)


class TestHashFile:
    """Tests for file hashing."""
    
    def test_hash_existing_file(self):
        """Should hash existing file."""
        with tempfile.NamedTemporaryFile(delete=False, mode='w') as f:
            f.write("test content")
            temp_path = f.name
        
        try:
            result = hash_file(temp_path)
            assert isinstance(result, str)
            assert len(result) == 64  # SHA-256 hex length
        finally:
            os.unlink(temp_path)
    
    def test_hash_nonexistent_file(self):
        """Should return 'error' for nonexistent file."""
        result = hash_file("/nonexistent/path/file.txt")
        assert result == "error"
    
    def test_hash_deterministic(self):
        """Same content should produce same hash."""
        with tempfile.NamedTemporaryFile(delete=False, mode='w') as f:
            f.write("test content")
            temp_path = f.name
        
        try:
            hash1 = hash_file(temp_path)
            hash2 = hash_file(temp_path)
            assert hash1 == hash2
        finally:
            os.unlink(temp_path)


class TestHashDict:
    """Tests for dictionary hashing."""
    
    def test_hash_dict_returns_string(self):
        """Should return a string."""
        result = hash_dict({"key": "value"})
        assert isinstance(result, str)
    
    def test_hash_dict_truncated(self):
        """Hash should be truncated to 16 chars."""
        result = hash_dict({"key": "value"})
        assert len(result) == 16
    
    def test_hash_dict_deterministic(self):
        """Same dict should produce same hash."""
        data = {"a": 1, "b": 2}
        hash1 = hash_dict(data)
        hash2 = hash_dict(data)
        assert hash1 == hash2
    
    def test_hash_dict_order_independent(self):
        """Dict order should not affect hash."""
        hash1 = hash_dict({"a": 1, "b": 2})
        hash2 = hash_dict({"b": 2, "a": 1})
        assert hash1 == hash2


class TestHashModelArtifact:
    """Tests for model artifact hashing."""
    
    def test_hash_directory(self):
        """Should hash all files in directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            Path(tmpdir, "file1.txt").write_text("content1")
            Path(tmpdir, "file2.txt").write_text("content2")
            
            result = hash_model_artifact(tmpdir)
            
            assert "file1.txt" in result
            assert "file2.txt" in result
    
    def test_hash_single_file(self):
        """Should hash single file."""
        with tempfile.NamedTemporaryFile(delete=False, mode='w') as f:
            f.write("test content")
            temp_path = f.name
        
        try:
            result = hash_model_artifact(temp_path)
            assert Path(temp_path).name in result
        finally:
            os.unlink(temp_path)


class TestAuditTrail:
    """Tests for AuditTrail."""
    
    def setup_method(self):
        """Create fresh audit trail for each test."""
        self.trail = AuditTrail()
    
    def test_add_record(self):
        """Should add record to trail."""
        record = self.trail.add_record("test_action", request_id="req-123")
        
        assert record["action"] == "test_action"
        assert record["request_id"] == "req-123"
        assert "timestamp" in record
        assert "git_sha" in record
    
    def test_add_record_with_details(self):
        """Should include details in record."""
        details = {"key": "value"}
        record = self.trail.add_record("test_action", details=details)
        
        assert record["details"] == details
    
    def test_get_records(self):
        """Should retrieve records."""
        self.trail.add_record("action1")
        self.trail.add_record("action2")
        
        records = self.trail.get_records()
        
        assert len(records) == 2
    
    def test_get_records_filter_by_action(self):
        """Should filter records by action."""
        self.trail.add_record("action1")
        self.trail.add_record("action2")
        self.trail.add_record("action1")
        
        records = self.trail.get_records(action="action1")
        
        assert len(records) == 2
        assert all(r["action"] == "action1" for r in records)
    
    def test_get_records_limit(self):
        """Should respect limit parameter."""
        for i in range(10):
            self.trail.add_record("action")
        
        records = self.trail.get_records(limit=5)
        
        assert len(records) == 5
    
    def test_get_summary(self):
        """Should return summary."""
        self.trail.add_record("action1")
        self.trail.add_record("action2")
        self.trail.add_record("action1")
        
        summary = self.trail.get_summary()
        
        assert "startup_time" in summary
        assert "git_sha" in summary
        assert "total_records" in summary
        assert summary["actions"]["action1"] == 2
        assert summary["actions"]["action2"] == 1
    
    def test_clear(self):
        """Clear should remove all records."""
        self.trail.add_record("action")
        self.trail.clear()
        
        assert len(self.trail.get_records()) == 0


class TestModelLineage:
    """Tests for ModelLineage."""
    
    def test_init_without_path(self):
        """Should initialize without model path."""
        lineage = ModelLineage()
        
        assert lineage.model_path is None
        assert lineage.artifact_hashes == {}
    
    def test_init_with_path(self):
        """Should initialize with model path and hash artifacts."""
        with tempfile.NamedTemporaryFile(delete=False, mode='w') as f:
            f.write("model content")
            temp_path = f.name
        
        try:
            lineage = ModelLineage(model_path=temp_path, version="v1.0.0")
            
            assert lineage.model_path == temp_path
            assert lineage.version == "v1.0.0"
            assert len(lineage.artifact_hashes) > 0
        finally:
            os.unlink(temp_path)
    
    def test_set_training_info(self):
        """Should set training information."""
        lineage = ModelLineage()
        config = {"learning_rate": 0.01}
        sources = ["data/train.csv"]
        
        lineage.set_training_info(config=config, data_sources=sources)
        
        assert lineage.training_config == config
        assert lineage.data_sources == sources
    
    def test_get_lineage(self):
        """Should return complete lineage info."""
        lineage = ModelLineage(version="v1.0.0")
        
        info = lineage.get_lineage()
        
        assert "model_path" in info
        assert "version" in info
        assert "loaded_at" in info
        assert "code" in info
        assert "git_sha" in info["code"]


class TestCreateInferenceAuditRecord:
    """Tests for create_inference_audit_record."""
    
    def test_creates_complete_record(self):
        """Should create complete audit record."""
        record = create_inference_audit_record(
            request_id="req-123",
            input_hash="abc123",
            output_probability=0.75,
            model_version="v1.0.0",
            latency_ms=50.0,
            success=True,
        )
        
        assert record["request_id"] == "req-123"
        assert record["input_hash"] == "abc123"
        assert record["output"]["probability"] == 0.75
        assert record["model"]["version"] == "v1.0.0"
        assert record["performance"]["latency_ms"] == 50.0
        assert record["performance"]["success"] is True
        assert "timestamp" in record
        assert "code_sha" in record


class TestGlobalInstances:
    """Tests for global audit instances."""
    
    def test_audit_trail_exists(self):
        """Global audit trail should exist."""
        assert audit_trail is not None
        assert isinstance(audit_trail, AuditTrail)
    
    def test_init_model_lineage(self):
        """Should initialize global model lineage."""
        with tempfile.NamedTemporaryFile(delete=False, mode='w') as f:
            f.write("model")
            temp_path = f.name
        
        try:
            lineage = init_model_lineage(temp_path, "v1.0.0")
            
            assert lineage is not None
            assert get_model_lineage() == lineage
        finally:
            os.unlink(temp_path)
