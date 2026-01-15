"""
Tests for Phase 8 Privacy Module.
"""

import pytest

from app.privacy import (
    hash_identifier,
    detect_pii,
    has_pii,
    redact_pii,
    sanitize_dict_for_logging,
    aggregate_features,
    PrivacyContext,
    PII_FIELDS,
    SAFE_FIELDS,
)


class TestHashIdentifier:
    """Tests for identifier hashing."""
    
    def test_returns_string(self):
        """Hash should return a string."""
        result = hash_identifier("test-value")
        assert isinstance(result, str)
    
    def test_truncated_length(self):
        """Hash should be truncated to 16 chars."""
        result = hash_identifier("test-value")
        assert len(result) == 16
    
    def test_deterministic(self):
        """Same value should produce same hash."""
        hash1 = hash_identifier("test-value")
        hash2 = hash_identifier("test-value")
        assert hash1 == hash2
    
    def test_salt_changes_hash(self):
        """Different salt should produce different hash."""
        hash1 = hash_identifier("test-value", salt="salt1")
        hash2 = hash_identifier("test-value", salt="salt2")
        assert hash1 != hash2


class TestDetectPii:
    """Tests for PII detection."""
    
    def test_detect_cpf(self):
        """Should detect CPF patterns."""
        findings = detect_pii("CPF: 123.456.789-00")
        assert "cpf" in findings
        assert len(findings["cpf"]) > 0
    
    def test_detect_cpf_no_punctuation(self):
        """Should detect CPF without punctuation."""
        findings = detect_pii("CPF: 12345678900")
        assert "cpf" in findings
    
    def test_detect_email(self):
        """Should detect email patterns."""
        findings = detect_pii("Email: test@example.com")
        assert "email" in findings
    
    def test_detect_phone(self):
        """Should detect phone patterns."""
        findings = detect_pii("Tel: (11) 98765-4321")
        assert "phone" in findings
    
    def test_detect_cep(self):
        """Should detect CEP patterns."""
        findings = detect_pii("CEP: 01234-567")
        assert "cep" in findings
    
    def test_no_pii_empty_result(self):
        """Text without PII should return empty dict."""
        findings = detect_pii("Hello world, this is safe text")
        assert len(findings) == 0


class TestHasPii:
    """Tests for has_pii function."""
    
    def test_text_with_pii(self):
        """Should return True for text with PII."""
        assert has_pii("CPF: 123.456.789-00") is True
    
    def test_text_without_pii(self):
        """Should return False for safe text."""
        assert has_pii("This is safe text") is False
    
    def test_empty_string(self):
        """Empty string should return False."""
        assert has_pii("") is False


class TestRedactPii:
    """Tests for PII redaction."""
    
    def test_redact_cpf(self):
        """Should redact CPF."""
        result = redact_pii("CPF: 123.456.789-00")
        assert "123.456.789-00" not in result
        assert "[REDACTED]" in result
    
    def test_redact_email(self):
        """Should redact email."""
        result = redact_pii("Email: user@example.com")
        assert "user@example.com" not in result
    
    def test_custom_replacement(self):
        """Should use custom replacement string."""
        result = redact_pii("CPF: 123.456.789-00", replacement="***")
        assert "***" in result
    
    def test_preserve_safe_text(self):
        """Should preserve text without PII."""
        text = "Hello world"
        result = redact_pii(text)
        assert result == text


class TestSanitizeDictForLogging:
    """Tests for dictionary sanitization."""
    
    def test_redact_pii_fields(self):
        """Should redact known PII fields."""
        data = {"nome": "John Doe", "cpf": "123.456.789-00", "age": 25}
        result = sanitize_dict_for_logging(data)
        
        assert result["nome"] == "[REDACTED]"
        assert result["cpf"] == "[REDACTED]"
        assert result["age"] == 25
    
    def test_safe_only_mode(self):
        """Should only include safe fields when requested."""
        data = {"nome": "John", "nota_exame": 7.5, "turnover": 0.15}
        result = sanitize_dict_for_logging(data, include_safe_only=True)
        
        assert "nome" not in result
        assert result["nota_exame"] == 7.5
        assert result["turnover"] == 0.15
    
    def test_nested_dict(self):
        """Should handle nested dictionaries."""
        data = {"user": {"nome": "John", "score": 10}}
        result = sanitize_dict_for_logging(data)
        
        assert result["user"]["nome"] == "[REDACTED]"
        assert result["user"]["score"] == 10
    
    def test_pii_in_string_value(self):
        """Should detect and redact PII in string values."""
        data = {"message": "Contact: 123.456.789-00"}
        result = sanitize_dict_for_logging(data)
        
        assert "123.456.789-00" not in result["message"]


class TestAggregateFeatures:
    """Tests for feature aggregation."""
    
    def test_only_safe_fields(self):
        """Should only include safe fields."""
        features = {
            "nome": "John",
            "nota_exame": 7.5,
            "turnover": 0.15,
            "email": "test@example.com",
        }
        result = aggregate_features(features)
        
        assert "nome" not in result
        assert "email" not in result
        assert result["nota_exame"] == 7.5
        assert result["turnover"] == 0.15
    
    def test_numeric_values_preserved(self):
        """Numeric values should be preserved."""
        features = {"headcount": 100, "idade": 16}
        result = aggregate_features(features)
        
        assert result["headcount"] == 100
        assert result["idade"] == 16
    
    def test_pii_strings_excluded(self):
        """Strings with PII patterns should be excluded."""
        features = {"area_atuacao": "123.456.789-00"}  # CPF in string
        result = aggregate_features(features)
        
        assert "area_atuacao" not in result


class TestPrivacyContext:
    """Tests for PrivacyContext class."""
    
    def test_sanitize_request(self):
        """Should sanitize request data."""
        ctx = PrivacyContext("test")
        data = {"nome": "John", "score": 10}
        result = ctx.sanitize_request(data)
        
        assert result["nome"] == "[REDACTED]"
        assert result["score"] == 10
    
    def test_get_loggable(self):
        """Should return loggable version."""
        ctx = PrivacyContext("test")
        data = {"nome": "John", "nota_exame": 7.5}
        ctx.sanitize_request(data)
        result = ctx.get_loggable()
        
        assert "nome" not in result
        assert "nota_exame" in result
    
    def test_create_audit_record(self):
        """Should create audit record with sanitized data."""
        ctx = PrivacyContext("api")
        data = {"nome": "John", "score": 10}
        record = ctx.create_audit_record("test_action", data, "success")
        
        assert record["context"] == "api"
        assert record["action"] == "test_action"
        assert "data_hash" in record
        assert record["result"] == "success"


class TestPiiFieldsConfig:
    """Tests for PII fields configuration."""
    
    def test_common_pii_fields_included(self):
        """Common PII field names should be in PII_FIELDS."""
        expected = ["nome", "name", "cpf", "email", "telefone", "phone"]
        for field in expected:
            assert field in PII_FIELDS
    
    def test_safe_fields_are_features(self):
        """SAFE_FIELDS should include model features."""
        expected = ["turnover", "headcount", "nota_exame", "idade"]
        for field in expected:
            assert field in SAFE_FIELDS
    
    def test_no_overlap(self):
        """PII_FIELDS and SAFE_FIELDS should not overlap."""
        overlap = PII_FIELDS & SAFE_FIELDS
        assert len(overlap) == 0
