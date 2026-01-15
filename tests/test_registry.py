"""
Testes para src/registry.py - Model Registry.
"""

import json
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Importar após setup para evitar side effects
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestRegistryFunctions:
    """Testes para funções do registry."""
    
    @pytest.fixture
    def temp_registry(self, tmp_path):
        """Cria estrutura temporária de registry."""
        registry = tmp_path / "registry"
        registry.mkdir()
        return registry
    
    @pytest.fixture
    def temp_artifacts(self, tmp_path):
        """Cria artefatos temporários para teste."""
        artifacts = tmp_path / "artifacts"
        artifacts.mkdir()
        
        # Model fake
        model_path = artifacts / "model_v1.joblib"
        model_path.write_bytes(b"fake model content")
        
        # Metadata
        metadata = {
            "model_version": "v1.0.0",
            "created_at": "2024-01-01",
            "expected_features": ["f1", "f2"]
        }
        metadata_path = artifacts / "model_metadata_v1.json"
        metadata_path.write_text(json.dumps(metadata))
        
        # Signature
        signature = {
            "input_schema": {"f1": "float", "f2": "int"}
        }
        signature_path = artifacts / "model_signature_v1.json"
        signature_path.write_text(json.dumps(signature))
        
        # Metrics
        metrics = {"recall": 0.75, "precision": 0.40}
        metrics_path = artifacts / "metrics_v1.json"
        metrics_path.write_text(json.dumps(metrics))
        
        return artifacts
    
    def test_compute_hash(self):
        """Testa computação de hash."""
        from src.registry import compute_file_hash
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
            f.write(b"test content")
            f.flush()
            
            hash_value = compute_file_hash(Path(f.name))
            assert len(hash_value) == 64  # SHA256 hex
            assert hash_value == compute_file_hash(Path(f.name))  # Determinístico
    
    def test_register_model(self, temp_registry, temp_artifacts):
        """Testa registro de modelo."""
        from src.registry import register_model
        
        version_dir = register_model(
            version="v1.0.0",
            artifacts_dir=temp_artifacts,
            registry_dir=temp_registry
        )
        
        assert version_dir.exists()
        assert (version_dir / "model.joblib").exists()
        assert (version_dir / "model_metadata.json").exists()
        assert (version_dir / "model_signature.json").exists()
        assert (version_dir / "manifest.json").exists()
    
    def test_register_duplicate_version_overwrites(self, temp_registry, temp_artifacts):
        """Testa que versão duplicada é sobrescrita com warning."""
        from src.registry import register_model
        
        # Primeiro registro
        register_model(
            version="v1.0.0",
            artifacts_dir=temp_artifacts,
            registry_dir=temp_registry
        )
        
        # Segundo registro sobrescreve
        version_dir = register_model(
            version="v1.0.0",
            artifacts_dir=temp_artifacts,
            registry_dir=temp_registry
        )
        
        assert version_dir.exists()
    
    def test_promote_champion(self, temp_registry, temp_artifacts):
        """Testa promoção para champion."""
        from src.registry import register_model, promote_champion, get_champion_version
        
        # Registrar primeiro
        register_model(
            version="v1.0.0",
            artifacts_dir=temp_artifacts,
            registry_dir=temp_registry
        )
        
        # Promover
        promote_champion("v1.0.0", registry_dir=temp_registry)
        
        # Verificar champion
        champion = get_champion_version(temp_registry)
        assert champion == "v1.0.0"
        
        # Verificar champion.json
        champion_file = temp_registry / "champion.json"
        assert champion_file.exists()
    
    def test_promote_nonexistent_version(self, temp_registry):
        """Testa erro ao promover versão inexistente."""
        from src.registry import promote_champion
        
        with pytest.raises(FileNotFoundError):
            promote_champion("v9.9.9", registry_dir=temp_registry)
    
    def test_rollback(self, temp_registry, temp_artifacts):
        """Testa rollback para versão anterior."""
        from src.registry import register_model, promote_champion, rollback_to, get_champion_version
        
        # Registrar v1.0.0
        register_model(
            version="v1.0.0",
            artifacts_dir=temp_artifacts,
            registry_dir=temp_registry
        )
        promote_champion("v1.0.0", registry_dir=temp_registry)
        
        # Registrar v1.1.0
        register_model(
            version="v1.1.0",
            artifacts_dir=temp_artifacts,
            registry_dir=temp_registry
        )
        promote_champion("v1.1.0", registry_dir=temp_registry)
        
        # Rollback para v1.0.0
        rollback_to("v1.0.0", registry_dir=temp_registry, reason="teste")
        
        champion = get_champion_version(temp_registry)
        assert champion == "v1.0.0"
    
    def test_list_versions(self, temp_registry, temp_artifacts):
        """Testa listagem de versões."""
        from src.registry import register_model, list_versions
        
        # Registrar múltiplas versões
        for v in ["v1.0.0", "v1.1.0", "v2.0.0"]:
            register_model(
                version=v,
                artifacts_dir=temp_artifacts,
                registry_dir=temp_registry
            )
        
        versions = list_versions(registry_dir=temp_registry)
        
        assert len(versions) == 3
        version_names = [v["version"] for v in versions]
        assert "v1.0.0" in version_names
        assert "v1.1.0" in version_names
        assert "v2.0.0" in version_names
    
    def test_resolve_champion_path(self, temp_registry, temp_artifacts):
        """Testa resolução do path do champion."""
        from src.registry import register_model, promote_champion, resolve_champion_path
        
        register_model(
            version="v1.0.0",
            artifacts_dir=temp_artifacts,
            registry_dir=temp_registry
        )
        promote_champion("v1.0.0", registry_dir=temp_registry)
        
        champion_dir = resolve_champion_path(registry_dir=temp_registry)
        
        assert champion_dir is not None
        assert champion_dir.exists()
        assert (champion_dir / "model.joblib").exists()
    
    def test_resolve_champion_no_champion(self, temp_registry):
        """Testa resolução quando não há champion."""
        from src.registry import resolve_champion_path
        
        champion_dir = resolve_champion_path(registry_dir=temp_registry)
        
        assert champion_dir is None


class TestRegistryCLI:
    """Testes para CLI do registry."""
    
    def test_cli_help(self):
        """Testa help do CLI."""
        from src.registry import main
        import sys
        
        with patch.object(sys, 'argv', ['registry', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0
    
    def test_cli_list_empty(self, tmp_path):
        """Testa listagem vazia."""
        from src.registry import main
        import sys
        
        registry = tmp_path / "registry"
        registry.mkdir()
        
        with patch.object(sys, 'argv', ['registry', 'list', '--registry', str(registry)]):
            # Não deve levantar exceção
            main()


class TestRegistryEdgeCases:
    """Testes de edge cases."""
    
    def test_missing_artifacts_dir(self, tmp_path):
        """Testa erro quando diretório de artefatos não existe."""
        from src.registry import register_model
        
        registry = tmp_path / "registry"
        registry.mkdir()
        
        with pytest.raises(FileNotFoundError):
            register_model(
                version="v1.0.0",
                artifacts_dir=tmp_path / "nonexistent",
                registry_dir=registry
            )
    
    def test_missing_required_artifacts(self, tmp_path):
        """Testa erro quando artefatos obrigatórios faltam."""
        from src.registry import register_model
        
        registry = tmp_path / "registry"
        registry.mkdir()
        
        artifacts = tmp_path / "empty_artifacts"
        artifacts.mkdir()
        
        with pytest.raises(ValueError) as exc_info:
            register_model(
                version="v1.0.0",
                artifacts_dir=artifacts,
                registry_dir=registry
            )
        
        assert "obrigatórios" in str(exc_info.value).lower() or "faltando" in str(exc_info.value).lower()
