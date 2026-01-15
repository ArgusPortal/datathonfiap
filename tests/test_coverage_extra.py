"""
Testes adicionais para aumentar coverage.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta, timezone
import json
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestModelLoaderResolve:
    """Testes para resolução de modelo via registry."""
    
    def test_resolve_model_paths_no_version(self):
        """Testa quando MODEL_VERSION não está definido."""
        from app.model_loader import resolve_model_paths
        from app import config
        
        # Salva valores originais
        original_version = config.MODEL_VERSION
        
        try:
            # Simula MODEL_VERSION vazio
            config.MODEL_VERSION = ""
            
            model_path, meta_path, sig_path = resolve_model_paths()
            
            # Deve retornar paths padrão
            assert model_path == config.MODEL_PATH
            assert meta_path == config.METADATA_PATH
        finally:
            config.MODEL_VERSION = original_version


class TestRetrainPipelineIntegration:
    """Testes de integração para retrain."""
    
    def test_run_training_returns_dict(self, tmp_path):
        """Testa que run_training retorna dicionário."""
        from src.retrain import run_training
        from unittest.mock import patch, MagicMock
        
        # Mock subprocess
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        
        # Cria arquivo de métricas mock
        artifacts = tmp_path / "artifacts"
        artifacts.mkdir()
        metrics_file = artifacts / "metrics_v1.json"
        metrics_file.write_text('{"recall": 0.75, "precision": 0.40}')
        
        with patch('subprocess.run', return_value=mock_result):
            data_path = tmp_path / "data.parquet"
            # Cria arquivo de dados vazio
            pd.DataFrame({"a": [1]}).to_parquet(data_path)
            
            result = run_training(data_path, artifacts, "v1.0.0")
            
            assert isinstance(result, dict)


class TestPerformanceDriftIntegration:
    """Testes de integração para performance drift."""
    
    def test_load_inference_store_with_partitions(self, tmp_path):
        """Testa carregamento com partições de data."""
        from monitoring.performance_drift import load_inference_store
        
        store_dir = tmp_path / "inference_store"
        
        # Cria partições
        today = datetime.now()
        for i in range(3):
            date = today - timedelta(days=i)
            partition = store_dir / f"dt={date.strftime('%Y-%m-%d')}"
            partition.mkdir(parents=True)
            
            df = pd.DataFrame({
                "request_id": [f"req_{i}_{j}" for j in range(10)],
                "risk_score": np.random.random(10),
                "risk_label": np.random.randint(0, 2, 10)
            })
            df.to_parquet(partition / "part_0.parquet")
        
        start_date = today - timedelta(days=7)
        end_date = today
        
        result = load_inference_store(store_dir, start_date, end_date)
        
        assert len(result) == 30  # 3 partições * 10 registros


class TestRegistryManifest:
    """Testes para manifest do registry."""
    
    def test_manifest_contains_hashes(self, tmp_path):
        """Testa que manifest contém hashes dos arquivos."""
        from src.registry import register_model
        
        registry = tmp_path / "registry"
        registry.mkdir()
        
        artifacts = tmp_path / "artifacts"
        artifacts.mkdir()
        
        # Cria artefatos
        (artifacts / "model_v1.joblib").write_bytes(b"model content")
        (artifacts / "model_metadata_v1.json").write_text('{"version": "v1.0.0"}')
        (artifacts / "model_signature_v1.json").write_text('{"input": {}}')
        (artifacts / "metrics_v1.json").write_text('{"recall": 0.75}')
        
        register_model("v1.0.0", artifacts, registry)
        
        manifest_path = registry / "v1.0.0" / "manifest.json"
        assert manifest_path.exists()
        
        manifest = json.loads(manifest_path.read_text())
        assert "hashes" in manifest
        assert len(manifest["hashes"]) > 0


class TestSchemaValidationWarnings:
    """Testes para warnings de schema."""
    
    def test_out_of_range_generates_warning(self, caplog):
        """Testa que valores fora do range geram warning."""
        from src.schema_validation import validate_input_schema
        import logging
        
        df = pd.DataFrame({
            "fase_2023": [3],
            "iaa_2023": [15.0],  # Fora do range [0-10]
            "ian_2023": [7.2],
            "ida_2023": [5.8],
            "idade_2023": [14],
            "ieg_2023": [6.0],
            "instituicao_2023": [1],
            "ipp_2023": [7.5],
            "ips_2023": [8.0],
            "ipv_2023": [6.2],
            "max_indicador": [8.0],
            "media_indicadores": [6.8],
            "min_indicador": [5.0],
            "range_indicadores": [3.0],
            "std_indicadores": [0.9]
        })
        
        # Deve gerar warning mas não erro
        with caplog.at_level(logging.WARNING):
            validate_input_schema(df, mode="inference")
        
        # Verifica que warning foi gerado
        assert any("range" in record.message.lower() or "iaa" in record.message.lower() 
                   for record in caplog.records)
