"""
Tests for Phase 8 Security Module.
"""

import os
import pytest
import time
from unittest.mock import MagicMock, patch

from fastapi import Request
from starlette.responses import JSONResponse

from app.security import (
    SecurityMiddleware,
    RateLimiter,
    rate_limiter,
    _parse_api_keys,
    _hash_key,
    validate_api_key,
    get_rate_limit_headers,
    PUBLIC_ENDPOINTS,
    RATE_LIMIT_RPM,
)


class TestApiKeyParsing:
    """Tests for API key parsing."""
    
    def test_parse_empty_keys(self):
        """Empty API_KEYS should return empty set."""
        with patch.dict(os.environ, {"API_KEYS": ""}, clear=False):
            # Re-import to get fresh parse
            keys = _parse_api_keys()
            # In dev mode with empty keys, set is empty
            assert isinstance(keys, set)
    
    def test_parse_single_key(self):
        """Single key should be parsed correctly."""
        with patch.dict(os.environ, {"API_KEYS": "test-key-123"}):
            from app.security import _parse_api_keys
            keys = _parse_api_keys()
            assert "test-key-123" in keys
    
    def test_parse_multiple_keys(self):
        """Multiple comma-separated keys should be parsed."""
        with patch.dict(os.environ, {"API_KEYS": "key1,key2,key3"}):
            from app.security import _parse_api_keys
            keys = _parse_api_keys()
            assert "key1" in keys
            assert "key2" in keys
            assert "key3" in keys
    
    def test_parse_keys_with_whitespace(self):
        """Keys with whitespace should be trimmed."""
        with patch.dict(os.environ, {"API_KEYS": " key1 , key2 "}):
            from app.security import _parse_api_keys
            keys = _parse_api_keys()
            assert "key1" in keys
            assert "key2" in keys


class TestHashKey:
    """Tests for key hashing."""
    
    def test_hash_returns_string(self):
        """Hash should return a string."""
        result = _hash_key("test-key")
        assert isinstance(result, str)
    
    def test_hash_is_truncated(self):
        """Hash should be truncated to 12 chars."""
        result = _hash_key("test-key")
        assert len(result) == 12
    
    def test_hash_is_deterministic(self):
        """Same key should always produce same hash."""
        hash1 = _hash_key("test-key")
        hash2 = _hash_key("test-key")
        assert hash1 == hash2
    
    def test_different_keys_different_hashes(self):
        """Different keys should produce different hashes."""
        hash1 = _hash_key("key1")
        hash2 = _hash_key("key2")
        assert hash1 != hash2


class TestRateLimiter:
    """Tests for RateLimiter."""
    
    def setup_method(self):
        """Reset rate limiter before each test."""
        self.limiter = RateLimiter(rpm=10)
    
    def test_allow_under_limit(self):
        """Requests under limit should be allowed."""
        assert self.limiter.allow("test-key") is True
    
    def test_deny_over_limit(self):
        """Requests over limit should be denied."""
        # Use all tokens
        for _ in range(10):
            self.limiter.allow("test-key")
        
        # Next request should be denied
        assert self.limiter.allow("test-key") is False
    
    def test_separate_buckets_per_key(self):
        """Different keys should have separate buckets."""
        # Use all tokens for key1
        for _ in range(10):
            self.limiter.allow("key1")
        
        # key2 should still have tokens
        assert self.limiter.allow("key2") is True
    
    def test_get_remaining(self):
        """get_remaining should return correct count."""
        # Full bucket
        assert self.limiter.get_remaining("new-key") == 10
        
        # After one request
        self.limiter.allow("new-key")
        assert self.limiter.get_remaining("new-key") == 9
    
    def test_reset(self):
        """Reset should clear bucket."""
        self.limiter.allow("test-key")
        self.limiter.reset("test-key")
        assert self.limiter.get_remaining("test-key") == 10
    
    def test_reset_all(self):
        """Reset without key should clear all buckets."""
        self.limiter.allow("key1")
        self.limiter.allow("key2")
        self.limiter.reset()
        assert self.limiter.get_remaining("key1") == 10
        assert self.limiter.get_remaining("key2") == 10


class TestValidateApiKey:
    """Tests for validate_api_key function."""
    
    def test_valid_key_returns_true(self):
        """Valid key should return True."""
        with patch.dict(os.environ, {"API_KEYS": "valid-key"}):
            assert validate_api_key("valid-key") is True
    
    def test_invalid_key_returns_false(self):
        """Invalid key should return False."""
        with patch.dict(os.environ, {"API_KEYS": "valid-key"}):
            assert validate_api_key("invalid-key") is False
    
    def test_empty_config_allows_all(self):
        """Empty API_KEYS config should allow all (dev mode)."""
        with patch.dict(os.environ, {"API_KEYS": ""}):
            assert validate_api_key("any-key") is True


class TestGetRateLimitHeaders:
    """Tests for get_rate_limit_headers."""
    
    def test_returns_headers_dict(self):
        """Should return headers dictionary."""
        rate_limiter.reset()
        headers = get_rate_limit_headers("test-key")
        
        assert "X-RateLimit-Limit" in headers
        assert "X-RateLimit-Remaining" in headers
    
    def test_limit_matches_config(self):
        """Limit header should match configuration."""
        headers = get_rate_limit_headers("test-key")
        assert headers["X-RateLimit-Limit"] == str(RATE_LIMIT_RPM)


class TestPublicEndpoints:
    """Tests for public endpoints configuration."""
    
    def test_health_is_public(self):
        """Health endpoint should be public."""
        assert "/health" in PUBLIC_ENDPOINTS
    
    def test_docs_is_public(self):
        """Docs endpoint should be public."""
        assert "/docs" in PUBLIC_ENDPOINTS
    
    def test_predict_is_not_public(self):
        """Predict endpoint should NOT be public."""
        assert "/predict" not in PUBLIC_ENDPOINTS
