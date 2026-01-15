"""
Performance Drift - monitora métricas quando labels estão disponíveis.

Uso:
    python -m monitoring.performance_drift --window 30 --output monitoring/reports/
"""

import argparse
import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("performance_drift")

# Thresholds de alerta
RECALL_ALERT = 0.70
PRECISION_ALERT = 0.30
AUC_ALERT = 0.75


def load_inference_store(store_dir: Path, start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """Carrega inferências do período."""
    store_dir = Path(store_dir)
    records = []
    
    if not store_dir.exists():
        logger.warning(f"Inference store não encontrado: {store_dir}")
        return pd.DataFrame()
    
    # Itera por partições de data
    for partition in store_dir.glob("dt=*"):
        date_str = partition.name.replace("dt=", "")
        try:
            partition_date = datetime.strptime(date_str, "%Y-%m-%d")
            if start_date.date() <= partition_date.date() <= end_date.date():
                for parquet_file in partition.glob("*.parquet"):
                    df = pd.read_parquet(parquet_file)
                    records.append(df)
        except ValueError:
            continue
    
    if not records:
        return pd.DataFrame()
    
    return pd.concat(records, ignore_index=True)


def load_labels_store(labels_path: Path) -> pd.DataFrame:
    """
    Carrega labels ground truth.
    
    Schema esperado:
    - request_id: str
    - timestamp: datetime
    - label: int (0/1)
    """
    labels_path = Path(labels_path)
    
    if not labels_path.exists():
        logger.warning(f"Labels store não encontrado: {labels_path}")
        return pd.DataFrame()
    
    if str(labels_path).endswith(".parquet"):
        return pd.read_parquet(labels_path)
    elif str(labels_path).endswith(".csv"):
        return pd.read_csv(labels_path)
    elif str(labels_path).endswith(".jsonl"):
        records = []
        with open(labels_path, "r", encoding="utf-8") as f:
            for line in f:
                records.append(json.loads(line))
        return pd.DataFrame(records)
    
    return pd.DataFrame()


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray, y_proba: np.ndarray) -> Dict[str, float]:
    """Calcula métricas de classificação."""
    from sklearn.metrics import (
        recall_score, precision_score, f1_score,
        roc_auc_score, average_precision_score, brier_score_loss
    )
    
    metrics = {}
    
    try:
        metrics["recall"] = float(recall_score(y_true, y_pred))
        metrics["precision"] = float(precision_score(y_true, y_pred, zero_division=0))
        metrics["f1"] = float(f1_score(y_true, y_pred))
        metrics["roc_auc"] = float(roc_auc_score(y_true, y_proba))
        metrics["pr_auc"] = float(average_precision_score(y_true, y_proba))
        metrics["brier_score"] = float(brier_score_loss(y_true, y_proba))
    except Exception as e:
        logger.warning(f"Erro ao calcular métricas: {e}")
    
    return metrics


def analyze_performance(
    inference_df: pd.DataFrame,
    labels_df: pd.DataFrame,
    window_days: int = 30
) -> Dict[str, Any]:
    """
    Analisa performance juntando inferências com labels.
    
    Returns:
        Dict com métricas e alertas
    """
    if inference_df.empty or labels_df.empty:
        return {"status": "no_data", "message": "Dados insuficientes"}
    
    # Join por request_id
    merged = inference_df.merge(
        labels_df[["request_id", "label"]],
        on="request_id",
        how="inner"
    )
    
    if len(merged) < 50:
        return {
            "status": "insufficient_data",
            "message": f"Apenas {len(merged)} amostras com labels",
            "n_samples": len(merged)
        }
    
    # Extrai predições e labels
    y_true = merged["label"].values
    y_pred = merged["risk_label"].values if "risk_label" in merged.columns else (merged["risk_score"] >= 0.5).astype(int).values
    y_proba = merged["risk_score"].values if "risk_score" in merged.columns else y_pred.astype(float)
    
    # Calcula métricas
    metrics = compute_metrics(y_true, y_pred, y_proba)
    
    # Determina status
    alerts = []
    if metrics.get("recall", 1.0) < RECALL_ALERT:
        alerts.append(f"Recall baixo: {metrics['recall']:.3f} < {RECALL_ALERT}")
    if metrics.get("precision", 1.0) < PRECISION_ALERT:
        alerts.append(f"Precision baixo: {metrics['precision']:.3f} < {PRECISION_ALERT}")
    if metrics.get("roc_auc", 1.0) < AUC_ALERT:
        alerts.append(f"AUC baixo: {metrics['roc_auc']:.3f} < {AUC_ALERT}")
    
    status = "red" if alerts else "green"
    
    return {
        "status": status,
        "window_days": window_days,
        "n_samples": len(merged),
        "n_positive": int(y_true.sum()),
        "positive_rate": float(y_true.mean()),
        "metrics": metrics,
        "alerts": alerts,
        "computed_at": datetime.now(timezone.utc).isoformat(),
    }


def generate_html_report(results: Dict[str, Any], output_path: Path) -> None:
    """Gera relatório HTML de performance."""
    status_colors = {"green": "#28a745", "yellow": "#ffc107", "red": "#dc3545"}
    status_color = status_colors.get(results.get("status", "green"), "#6c757d")
    
    metrics = results.get("metrics", {})
    
    html = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Performance Drift Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
        .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; }}
        .status {{ padding: 15px; border-radius: 4px; color: white; font-weight: bold; margin-bottom: 20px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #f8f9fa; }}
        .alert {{ background: #f8d7da; padding: 10px; border-radius: 4px; margin: 5px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Performance Drift Report</h1>
        <div class="status" style="background-color: {status_color}">
            Status: {results.get('status', 'unknown').upper()}
        </div>
        
        <h2>Resumo</h2>
        <table>
            <tr><td>Período (dias)</td><td>{results.get('window_days', 'N/A')}</td></tr>
            <tr><td>Amostras com label</td><td>{results.get('n_samples', 0)}</td></tr>
            <tr><td>Taxa de positivos</td><td>{results.get('positive_rate', 0):.2%}</td></tr>
            <tr><td>Gerado em</td><td>{results.get('computed_at', 'N/A')[:19]}</td></tr>
        </table>
        
        <h2>Métricas</h2>
        <table>
            <tr><th>Métrica</th><th>Valor</th></tr>
            <tr><td>Recall</td><td>{metrics.get('recall', 0):.3f}</td></tr>
            <tr><td>Precision</td><td>{metrics.get('precision', 0):.3f}</td></tr>
            <tr><td>F1 Score</td><td>{metrics.get('f1', 0):.3f}</td></tr>
            <tr><td>ROC AUC</td><td>{metrics.get('roc_auc', 0):.3f}</td></tr>
            <tr><td>PR AUC</td><td>{metrics.get('pr_auc', 0):.3f}</td></tr>
            <tr><td>Brier Score</td><td>{metrics.get('brier_score', 0):.3f}</td></tr>
        </table>
        
        {"<h2>Alertas</h2>" + "".join(f'<div class="alert">{a}</div>' for a in results.get('alerts', [])) if results.get('alerts') else ""}
    </div>
</body>
</html>
"""
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    logger.info(f"Relatório salvo em: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Performance Drift Analysis")
    parser.add_argument("--inference_store", "-i", default="monitoring/inference_store", help="Diretório do inference store")
    parser.add_argument("--labels", "-l", default="monitoring/labels_store.jsonl", help="Arquivo de labels")
    parser.add_argument("--window", "-w", type=int, default=30, help="Janela em dias")
    parser.add_argument("--output", "-o", default="monitoring/reports", help="Diretório de saída")
    
    args = parser.parse_args()
    
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=args.window)
    
    # Carrega dados
    inference_df = load_inference_store(Path(args.inference_store), start_date, end_date)
    labels_df = load_labels_store(Path(args.labels))
    
    # Analisa
    results = analyze_performance(inference_df, labels_df, args.window)
    
    # Salva resultados
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    date_str = datetime.now().strftime("%Y%m%d")
    
    # JSON
    json_path = output_dir / f"performance_metrics_{date_str}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # HTML
    html_path = output_dir / f"performance_report_{date_str}.html"
    generate_html_report(results, html_path)
    
    print(f"\nStatus: {results.get('status', 'unknown')}")
    if results.get("alerts"):
        print("Alertas:")
        for alert in results["alerts"]:
            print(f"  - {alert}")


if __name__ == "__main__":
    main()
