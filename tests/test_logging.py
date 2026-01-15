"""
Testes unitários para logging e configuração.
"""

import json
import logging
import pytest

from app.logging_config import (
    RequestLogger,
    StructuredFormatter,
    generate_request_id,
    setup_logging,
)


class TestGenerateRequestId:
    """Testes para função generate_request_id."""
    
    def test_returns_string(self):
        """Deve retornar string."""
        request_id = generate_request_id()
        
        assert isinstance(request_id, str)
    
    def test_unique_ids(self):
        """Deve gerar IDs únicos."""
        ids = [generate_request_id() for _ in range(100)]
        
        assert len(set(ids)) == 100
    
    def test_id_not_empty(self):
        """ID não deve ser vazio."""
        request_id = generate_request_id()
        
        assert len(request_id) > 0


class TestStructuredFormatter:
    """Testes para StructuredFormatter."""
    
    @pytest.fixture
    def formatter(self):
        """Cria formatter para testes."""
        return StructuredFormatter()
    
    def test_formats_as_json(self, formatter):
        """Deve formatar como JSON."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        
        formatted = formatter.format(record)
        
        # Deve ser JSON válido
        data = json.loads(formatted)
        assert "message" in data
    
    def test_includes_timestamp(self, formatter):
        """Deve incluir timestamp."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        
        formatted = formatter.format(record)
        data = json.loads(formatted)
        
        assert "timestamp" in data
    
    def test_includes_level(self, formatter):
        """Deve incluir nível de log."""
        record = logging.LogRecord(
            name="test",
            level=logging.WARNING,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        
        formatted = formatter.format(record)
        data = json.loads(formatted)
        
        assert data["level"] == "WARNING"
    
    def test_includes_extra_fields(self, formatter):
        """Deve incluir campos extras."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.request_id = "test-123"
        record.latency_ms = 50.5
        
        formatted = formatter.format(record)
        data = json.loads(formatted)
        
        assert data["request_id"] == "test-123"
        assert data["latency_ms"] == 50.5


class TestRequestLogger:
    """Testes para RequestLogger."""
    
    @pytest.fixture
    def request_logger(self):
        """Cria RequestLogger para testes."""
        return RequestLogger("test-request-123")
    
    def test_stores_request_id(self, request_logger):
        """Deve armazenar request_id."""
        assert request_logger.request_id == "test-request-123"
    
    def test_log_request_start(self, request_logger, caplog):
        """Deve logar início do request."""
        with caplog.at_level(logging.INFO):
            request_logger.log_request_start(method="POST", path="/predict")
        
        assert "POST /predict" in caplog.text or len(caplog.records) > 0
    
    def test_log_request_end(self, request_logger, caplog):
        """Deve logar fim do request."""
        with caplog.at_level(logging.INFO):
            request_logger.log_request_end(status_code=200, latency_ms=50.5)
        
        assert len(caplog.records) > 0
    
    def test_log_error(self, request_logger, caplog):
        """Deve logar erro."""
        with caplog.at_level(logging.ERROR):
            request_logger.log_error("Test error", latency_ms=100.0)
        
        assert len(caplog.records) > 0


class TestSetupLogging:
    """Testes para função setup_logging."""
    
    def test_returns_logger(self):
        """Deve retornar logger."""
        logger = setup_logging("INFO")
        
        assert logger is not None
        assert isinstance(logger, logging.Logger)
    
    def test_accepts_debug_level(self):
        """Deve aceitar nível DEBUG."""
        logger = setup_logging("DEBUG")
        
        assert logger.level <= logging.DEBUG
    
    def test_accepts_warning_level(self):
        """Deve aceitar nível WARNING."""
        logger = setup_logging("WARNING")
        
        # Logger ou handler deve estar configurado
        assert logger is not None
