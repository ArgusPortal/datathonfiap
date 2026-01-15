"""
Retrain Pipeline - treina challenger e compara com champion.

Uso:
    python -m src.retrain --new_version v1.2.0 --data data/processed/dataset.parquet
"""

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.registry import (
    register_model,
    promote_champion,
    get_champion_version,
    resolve_champion_path,
)
from src.schema_validation import validate_training_data

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("retrain")

# Guardrails
RECALL_DELTA_MAX = 0.02  # Recall não pode cair mais que 2%
PRECISION_DELTA_MAX = 0.05
BRIER_DELTA_MAX = 0.02
MIN_VALIDATION_SAMPLES = 500


def load_champion_metrics(registry_dir: Path) -> Optional[Dict[str, Any]]:
    """Carrega métricas do champion atual."""
    champion_path = resolve_champion_path(registry_dir)
    if not champion_path:
        logger.warning("Nenhum champion encontrado")
        return None
    
    metrics_path = champion_path / "metrics.json"
    if not metrics_path.exists():
        logger.warning(f"Métricas do champion não encontradas: {metrics_path}")
        return None
    
    with open(metrics_path, "r", encoding="utf-8") as f:
        return json.load(f)


def compare_metrics(
    challenger: Dict[str, Any],
    champion: Dict[str, Any]
) -> Tuple[bool, str]:
    """
    Compara métricas challenger vs champion.
    
    Returns:
        (aprovado, motivo)
    """
    reasons = []
    
    # Extrai métricas (flexível para diferentes estruturas)
    def get_metric(d: Dict, key: str, default: float = 0.0) -> float:
        if key in d:
            return float(d[key])
        if "validation" in d and key in d["validation"]:
            return float(d["validation"][key])
        return default
    
    champ_recall = get_metric(champion, "recall", 0.75)
    chall_recall = get_metric(challenger, "recall", 0.0)
    
    champ_precision = get_metric(champion, "precision", 0.4)
    chall_precision = get_metric(challenger, "precision", 0.0)
    
    champ_brier = get_metric(champion, "brier_score", 0.15)
    chall_brier = get_metric(challenger, "brier_score", 1.0)
    
    champ_auc = get_metric(champion, "roc_auc", 0.8)
    chall_auc = get_metric(challenger, "roc_auc", 0.0)
    
    # Guardrails
    if champ_recall - chall_recall > RECALL_DELTA_MAX:
        reasons.append(f"Recall caiu demais: {chall_recall:.3f} vs {champ_recall:.3f} (delta > {RECALL_DELTA_MAX})")
    
    if champ_precision - chall_precision > PRECISION_DELTA_MAX:
        reasons.append(f"Precision caiu demais: {chall_precision:.3f} vs {champ_precision:.3f}")
    
    if chall_brier - champ_brier > BRIER_DELTA_MAX:
        reasons.append(f"Brier piorou: {chall_brier:.3f} vs {champ_brier:.3f}")
    
    if chall_auc < champ_auc:
        reasons.append(f"AUC pior: {chall_auc:.3f} vs {champ_auc:.3f}")
    
    if reasons:
        return False, "; ".join(reasons)
    
    return True, f"Challenger aprovado (recall={chall_recall:.3f}, auc={chall_auc:.3f})"


def run_training(
    data_path: Path,
    artifacts_dir: Path,
    version: str
) -> Dict[str, Any]:
    """
    Executa pipeline de treino.
    
    Returns:
        Métricas do modelo treinado
    """
    import subprocess
    
    logger.info(f"Executando treino para versão {version}...")
    
    # Executa src.train
    cmd = [
        sys.executable, "-m", "src.train",
        "--data", str(data_path),
        "--artifacts", str(artifacts_dir),
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        logger.error(f"Treino falhou:\n{result.stderr}")
        raise RuntimeError(f"Treino falhou: {result.stderr}")
    
    logger.info("Treino concluído")
    
    # Carrega métricas geradas
    metrics_path = artifacts_dir / "metrics_v1.json"
    if not metrics_path.exists():
        metrics_path = artifacts_dir / "metrics.json"
    
    if metrics_path.exists():
        with open(metrics_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    return {}


def retrain(
    new_version: str,
    data_path: Path,
    registry_dir: Path,
    artifacts_dir: Path,
    baseline_dir: Optional[Path] = None,
    dry_run: bool = False,
    force: bool = False
) -> bool:
    """
    Pipeline completo de retrain.
    
    Args:
        new_version: Versão do challenger
        data_path: Caminho dos dados de treino
        registry_dir: Diretório do registry
        artifacts_dir: Diretório para artefatos temporários
        baseline_dir: Diretório do baseline (opcional)
        dry_run: Se True, apenas compara sem promover
        force: Se True, promove mesmo se guardrails falharem
    
    Returns:
        True se challenger foi promovido
    """
    registry_dir = Path(registry_dir)
    artifacts_dir = Path(artifacts_dir)
    data_path = Path(data_path)
    
    # Valida dados
    import pandas as pd
    logger.info(f"Validando dados de treino: {data_path}")
    df = pd.read_parquet(data_path) if str(data_path).endswith(".parquet") else pd.read_csv(data_path)
    
    try:
        validate_training_data(df)
    except Exception as e:
        logger.error(f"Validação de dados falhou: {e}")
        raise
    
    if len(df) < MIN_VALIDATION_SAMPLES:
        logger.warning(f"Dataset pequeno: {len(df)} < {MIN_VALIDATION_SAMPLES}")
    
    # Carrega métricas do champion
    champion_version = get_champion_version(registry_dir)
    champion_metrics = load_champion_metrics(registry_dir)
    
    logger.info(f"Champion atual: {champion_version}")
    
    # Treina challenger
    logger.info(f"Treinando challenger {new_version}...")
    challenger_metrics = run_training(data_path, artifacts_dir, new_version)
    
    # Compara
    if champion_metrics:
        approved, reason = compare_metrics(challenger_metrics, champion_metrics)
        logger.info(f"Comparação: {reason}")
    else:
        approved = True
        reason = "Primeiro modelo (sem champion para comparar)"
        logger.info(reason)
    
    if dry_run:
        logger.info(f"[DRY RUN] Challenger {'aprovado' if approved else 'reprovado'}")
        return approved
    
    # Registra challenger
    register_model(
        version=new_version,
        artifacts_dir=artifacts_dir,
        registry_dir=registry_dir,
        baseline_dir=baseline_dir,
        notes=reason,
        promoted_by="retrain_pipeline"
    )
    
    # Promove se aprovado
    if approved or force:
        promote_champion(new_version, registry_dir, promoted_by="retrain_pipeline")
        logger.info(f"✅ Challenger {new_version} promovido para champion")
        return True
    else:
        logger.warning(f"❌ Challenger {new_version} reprovado: {reason}")
        # Atualiza manifest com status rejected
        manifest_path = registry_dir / new_version / "manifest.json"
        if manifest_path.exists():
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
            manifest["status"] = "rejected"
            manifest["rejection_reason"] = reason
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)
        return False


def main():
    parser = argparse.ArgumentParser(description="Retrain Pipeline")
    parser.add_argument("--new_version", "-v", required=True, help="Versão do challenger (ex: v1.2.0)")
    parser.add_argument("--data", "-d", required=True, help="Caminho dos dados de treino")
    parser.add_argument("--registry", "-r", default="models/registry", help="Diretório do registry")
    parser.add_argument("--artifacts", "-a", default="artifacts", help="Diretório de artefatos")
    parser.add_argument("--baseline", "-b", help="Diretório do baseline")
    parser.add_argument("--dry_run", action="store_true", help="Apenas compara, não promove")
    parser.add_argument("--force", action="store_true", help="Promove mesmo se guardrails falharem")
    
    args = parser.parse_args()
    
    baseline = Path(args.baseline) if args.baseline else None
    
    success = retrain(
        new_version=args.new_version,
        data_path=Path(args.data),
        registry_dir=Path(args.registry),
        artifacts_dir=Path(args.artifacts),
        baseline_dir=baseline,
        dry_run=args.dry_run,
        force=args.force,
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
