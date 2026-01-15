"""
Model Registry - versionamento simples por pasta.

Uso:
    python -m src.registry register --version v1.1.0
    python -m src.registry promote --version v1.1.0
    python -m src.registry rollback --version v1.0.0
    python -m src.registry list
"""

import argparse
import hashlib
import json
import logging
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("registry")

# Artefatos obrigatórios para registro
REQUIRED_ARTIFACTS = [
    "model.joblib",
    "model_metadata.json",
    "model_signature.json",
    "metrics.json",
]

REQUIRED_BASELINE = [
    "feature_profile.json",
    "score_profile.json",
    "baseline_metadata.json",
]


def compute_file_hash(filepath: Path) -> str:
    """Computa SHA256 de um arquivo."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def compute_hashes(files: List[Path]) -> Dict[str, str]:
    """Computa hashes para lista de arquivos."""
    return {f.name: compute_file_hash(f) for f in files if f.exists()}


def validate_artifacts(artifacts_dir: Path) -> List[str]:
    """Valida que todos os artefatos obrigatórios existem."""
    missing = []
    
    # Verifica artefatos principais (com ou sem sufixo _v1)
    for artifact in REQUIRED_ARTIFACTS:
        base_name = artifact.replace("model_", "").replace("model.", "")
        possible_names = [
            artifact,
            artifact.replace("model", "model_v1"),
            f"model_v1.{base_name}" if "." in artifact else f"model_{base_name}_v1.json",
        ]
        
        found = False
        for name in possible_names:
            if (artifacts_dir / name).exists():
                found = True
                break
        
        if not found:
            # Tenta encontrar qualquer arquivo que corresponda
            pattern = artifact.split(".")[0]
            matches = list(artifacts_dir.glob(f"{pattern}*"))
            if not matches:
                missing.append(artifact)
    
    return missing


def find_artifact(artifacts_dir: Path, base_name: str) -> Optional[Path]:
    """Encontra artefato com possíveis variações de nome."""
    # Ordem de preferência
    candidates = [
        artifacts_dir / base_name,
        artifacts_dir / base_name.replace("model", "model_v1"),
    ]
    
    for candidate in candidates:
        if candidate.exists():
            return candidate
    
    # Fallback: busca por padrão
    pattern = base_name.split(".")[0]
    matches = list(artifacts_dir.glob(f"*{pattern}*"))
    if matches:
        return matches[0]
    
    return None


def register_model(
    version: str,
    artifacts_dir: Path,
    registry_dir: Path,
    baseline_dir: Optional[Path] = None,
    notes: str = "",
    promoted_by: str = "auto"
) -> Path:
    """
    Registra nova versão do modelo no registry.
    
    Args:
        version: Versão do modelo (ex: v1.1.0)
        artifacts_dir: Diretório com artefatos fonte
        registry_dir: Diretório do registry
        baseline_dir: Diretório com baseline de monitoramento
        notes: Notas sobre esta versão
        promoted_by: Quem/o quê registrou
    
    Returns:
        Path do diretório da versão registrada
    """
    artifacts_dir = Path(artifacts_dir)
    registry_dir = Path(registry_dir)
    
    if not artifacts_dir.exists():
        raise FileNotFoundError(f"Diretório de artefatos não existe: {artifacts_dir}")
    
    # Valida artefatos
    missing = validate_artifacts(artifacts_dir)
    if missing:
        raise ValueError(f"Artefatos obrigatórios faltando: {missing}")
    
    # Cria diretório da versão
    version_dir = registry_dir / version
    if version_dir.exists():
        logger.warning(f"Versão {version} já existe. Sobrescrevendo...")
        shutil.rmtree(version_dir)
    
    version_dir.mkdir(parents=True, exist_ok=True)
    
    # Copia artefatos com nomes padronizados
    artifact_mapping = {
        "model.joblib": ["model_v1.joblib", "model.joblib"],
        "model_metadata.json": ["model_metadata_v1.json", "model_metadata.json"],
        "model_signature.json": ["model_signature_v1.json", "model_signature.json"],
        "metrics.json": ["metrics_v1.json", "metrics.json"],
    }
    
    copied_files = []
    for target_name, source_candidates in artifact_mapping.items():
        for source_name in source_candidates:
            source_path = artifacts_dir / source_name
            if source_path.exists():
                target_path = version_dir / target_name
                shutil.copy2(source_path, target_path)
                copied_files.append(target_path)
                logger.info(f"Copiado: {source_name} -> {target_name}")
                break
    
    # Copia baseline se fornecido
    baseline_dest = version_dir / "monitoring_baseline"
    if baseline_dir and Path(baseline_dir).exists():
        baseline_dest.mkdir(exist_ok=True)
        for baseline_file in REQUIRED_BASELINE:
            src = Path(baseline_dir) / baseline_file
            if src.exists():
                shutil.copy2(src, baseline_dest / baseline_file)
                copied_files.append(baseline_dest / baseline_file)
                logger.info(f"Copiado baseline: {baseline_file}")
    
    # Cria manifest
    manifest = {
        "version": version,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "promoted_by": promoted_by,
        "notes": notes,
        "status": "registered",
        "hashes": compute_hashes(copied_files),
        "artifacts": [f.name for f in (version_dir).glob("*") if f.is_file()],
        "has_baseline": baseline_dest.exists() and any(baseline_dest.iterdir()),
    }
    
    manifest_path = version_dir / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    
    logger.info(f"✅ Modelo {version} registrado em {version_dir}")
    return version_dir


def get_champion_version(registry_dir: Path) -> Optional[str]:
    """Obtém versão atual do champion."""
    registry_dir = Path(registry_dir)
    champion_file = registry_dir / "champion.json"
    
    if not champion_file.exists():
        return None
    
    with open(champion_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    return data.get("version")


def promote_champion(version: str, registry_dir: Path, promoted_by: str = "manual") -> None:
    """
    Promove versão para champion.
    
    Args:
        version: Versão a promover
        registry_dir: Diretório do registry
        promoted_by: Quem promoveu
    """
    registry_dir = Path(registry_dir)
    version_dir = registry_dir / version
    
    if not version_dir.exists():
        raise FileNotFoundError(f"Versão {version} não encontrada no registry")
    
    # Verifica manifest
    manifest_path = version_dir / "manifest.json"
    if not manifest_path.exists():
        raise ValueError(f"Versão {version} não possui manifest válido")
    
    # Obtém champion anterior
    old_champion = get_champion_version(registry_dir)
    
    # Atualiza champion.json
    champion_data = {
        "version": version,
        "promoted_at": datetime.now(timezone.utc).isoformat(),
        "promoted_by": promoted_by,
        "previous_champion": old_champion,
    }
    
    champion_file = registry_dir / "champion.json"
    with open(champion_file, "w", encoding="utf-8") as f:
        json.dump(champion_data, f, indent=2, ensure_ascii=False)
    
    # Atualiza manifest da versão
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    
    manifest["status"] = "champion"
    manifest["promoted_at"] = champion_data["promoted_at"]
    
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    
    logger.info(f"✅ Versão {version} promovida para champion")
    if old_champion:
        logger.info(f"   Champion anterior: {old_champion}")


def rollback_to(version: str, registry_dir: Path, reason: str = "") -> None:
    """
    Rollback para versão anterior.
    
    Args:
        version: Versão para rollback
        registry_dir: Diretório do registry
        reason: Motivo do rollback
    """
    registry_dir = Path(registry_dir)
    version_dir = registry_dir / version
    
    if not version_dir.exists():
        raise FileNotFoundError(f"Versão {version} não encontrada para rollback")
    
    current_champion = get_champion_version(registry_dir)
    
    if current_champion == version:
        logger.warning(f"Versão {version} já é o champion atual")
        return
    
    # Registra rollback
    rollback_dir = registry_dir / "rollback"
    rollback_dir.mkdir(exist_ok=True)
    
    rollback_log = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "from_version": current_champion,
        "to_version": version,
        "reason": reason,
    }
    
    rollback_file = rollback_dir / f"rollback_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(rollback_file, "w", encoding="utf-8") as f:
        json.dump(rollback_log, f, indent=2, ensure_ascii=False)
    
    # Promove versão anterior
    promote_champion(version, registry_dir, promoted_by=f"rollback: {reason}")
    
    logger.info(f"✅ Rollback de {current_champion} para {version}")


def list_versions(registry_dir: Path) -> List[Dict[str, Any]]:
    """Lista todas as versões no registry."""
    registry_dir = Path(registry_dir)
    versions = []
    
    if not registry_dir.exists():
        return versions
    
    champion = get_champion_version(registry_dir)
    
    for version_dir in sorted(registry_dir.iterdir()):
        if not version_dir.is_dir() or version_dir.name in ["rollback"]:
            continue
        
        manifest_path = version_dir / "manifest.json"
        if manifest_path.exists():
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
            manifest["is_champion"] = (manifest.get("version") == champion)
            versions.append(manifest)
    
    return versions


def resolve_champion_path(registry_dir: Path) -> Optional[Path]:
    """Resolve o caminho para o diretório do champion."""
    registry_dir = Path(registry_dir)
    champion = get_champion_version(registry_dir)
    
    if champion:
        champion_dir = registry_dir / champion
        if champion_dir.exists():
            return champion_dir
    
    return None


def main():
    parser = argparse.ArgumentParser(description="Model Registry CLI")
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponíveis")
    
    # Register
    register_parser = subparsers.add_parser("register", help="Registra nova versão")
    register_parser.add_argument("--version", "-v", required=True, help="Versão (ex: v1.1.0)")
    register_parser.add_argument("--artifacts", "-a", default="artifacts", help="Diretório de artefatos")
    register_parser.add_argument("--registry", "-r", default="models/registry", help="Diretório do registry")
    register_parser.add_argument("--baseline", "-b", help="Diretório do baseline")
    register_parser.add_argument("--notes", "-n", default="", help="Notas")
    
    # Promote
    promote_parser = subparsers.add_parser("promote", help="Promove versão para champion")
    promote_parser.add_argument("--version", "-v", required=True, help="Versão a promover")
    promote_parser.add_argument("--registry", "-r", default="models/registry", help="Diretório do registry")
    
    # Rollback
    rollback_parser = subparsers.add_parser("rollback", help="Rollback para versão anterior")
    rollback_parser.add_argument("--version", "-v", required=True, help="Versão para rollback")
    rollback_parser.add_argument("--registry", "-r", default="models/registry", help="Diretório do registry")
    rollback_parser.add_argument("--reason", default="", help="Motivo do rollback")
    
    # List
    list_parser = subparsers.add_parser("list", help="Lista versões")
    list_parser.add_argument("--registry", "-r", default="models/registry", help="Diretório do registry")
    
    args = parser.parse_args()
    
    if args.command == "register":
        baseline_dir = Path(args.baseline) if args.baseline else None
        register_model(
            version=args.version,
            artifacts_dir=Path(args.artifacts),
            registry_dir=Path(args.registry),
            baseline_dir=baseline_dir,
            notes=args.notes,
        )
    
    elif args.command == "promote":
        promote_champion(args.version, Path(args.registry))
    
    elif args.command == "rollback":
        rollback_to(args.version, Path(args.registry), args.reason)
    
    elif args.command == "list":
        versions = list_versions(Path(args.registry))
        if not versions:
            print("Nenhuma versão registrada")
        else:
            print(f"\n{'Versão':<12} {'Status':<12} {'Criado em':<25} {'Champion'}")
            print("-" * 60)
            for v in versions:
                champion_mark = "★" if v.get("is_champion") else ""
                print(f"{v['version']:<12} {v['status']:<12} {v['created_at'][:19]:<25} {champion_mark}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
