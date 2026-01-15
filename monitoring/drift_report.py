"""
Drift Report Generator - Computes feature and score drift, generates HTML report.
Uses PSI (Population Stability Index) for drift detection.
"""

import argparse
import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Load config
CONFIG_PATH = Path(__file__).parent / "config.json"
DEFAULT_THRESHOLDS = {
    "feature_psi_warn": 0.1,
    "feature_psi_alert": 0.25,
    "score_psi_warn": 0.1,
    "score_psi_alert": 0.25,
    "missing_rate_delta_warn": 0.05,
    "missing_rate_delta_alert": 0.10,
    "yellow_feature_pct": 0.2,
}

EPSILON = 1e-6


def load_config() -> Dict[str, Any]:
    """Load monitoring config."""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
        return config.get("thresholds", DEFAULT_THRESHOLDS)
    return DEFAULT_THRESHOLDS


def compute_psi(
    baseline_freq: List[float],
    current_freq: List[float]
) -> float:
    """
    Compute Population Stability Index.
    PSI = sum((current - baseline) * ln(current / baseline))
    """
    baseline_arr = np.array(baseline_freq) + EPSILON
    current_arr = np.array(current_freq) + EPSILON
    
    # Normalize to ensure they sum to 1
    baseline_arr = baseline_arr / baseline_arr.sum()
    current_arr = current_arr / current_arr.sum()
    
    psi = np.sum((current_arr - baseline_arr) * np.log(current_arr / baseline_arr))
    return float(psi)


def compute_numeric_psi(
    baseline_profile: Dict[str, Any],
    current_values: List[float],
    n_bins: int = 10
) -> Tuple[float, Dict[str, Any]]:
    """Compute PSI for numeric feature using baseline quantiles as bin edges."""
    if not current_values:
        return 0.0, {"error": "no_current_values"}
    
    quantiles = baseline_profile.get("quantiles", {})
    if not quantiles:
        return 0.0, {"error": "no_baseline_quantiles"}
    
    # Create bins from baseline quantiles
    bin_edges = sorted(set([
        quantiles.get("p05", 0),
        quantiles.get("p25", 0),
        quantiles.get("p50", 0),
        quantiles.get("p75", 0),
        quantiles.get("p95", 0),
    ]))
    
    if len(bin_edges) < 2:
        # Fallback to min/max
        bin_edges = [baseline_profile.get("min", 0), baseline_profile.get("max", 1)]
    
    # Add extreme edges
    bin_edges = [-np.inf] + bin_edges + [np.inf]
    
    # Compute baseline frequencies (roughly equal for quantile-based bins)
    n_baseline_bins = len(bin_edges) - 1
    baseline_freq = [1.0 / n_baseline_bins] * n_baseline_bins
    
    # Compute current frequencies
    current_arr = np.array(current_values)
    current_counts, _ = np.histogram(current_arr, bins=bin_edges)
    current_freq = (current_counts / len(current_values)).tolist()
    
    psi = compute_psi(baseline_freq, current_freq)
    
    return psi, {
        "bin_edges": [float(e) if np.isfinite(e) else str(e) for e in bin_edges],
        "baseline_freq": baseline_freq,
        "current_freq": current_freq,
    }


def compute_categorical_psi(
    baseline_profile: Dict[str, Any],
    current_values: List[str]
) -> Tuple[float, Dict[str, Any]]:
    """Compute PSI for categorical feature."""
    if not current_values:
        return 0.0, {"error": "no_current_values"}
    
    top_values = baseline_profile.get("top_values", {})
    if not top_values:
        return 0.0, {"error": "no_baseline_top_values"}
    
    # Get baseline frequencies
    categories = list(top_values.keys())
    baseline_freq = [top_values[cat]["freq"] for cat in categories]
    
    # Compute current frequencies
    current_counts = pd.Series(current_values).value_counts()
    total = len(current_values)
    
    current_freq = []
    for cat in categories:
        if cat == "__other__":
            other_count = sum(current_counts.get(c, 0) for c in current_counts.index if c not in categories)
            current_freq.append(other_count / total if total > 0 else 0)
        else:
            current_freq.append(current_counts.get(cat, 0) / total if total > 0 else 0)
    
    psi = compute_psi(baseline_freq, current_freq)
    
    return psi, {
        "categories": categories,
        "baseline_freq": baseline_freq,
        "current_freq": current_freq,
    }


def get_status(value: float, warn_threshold: float, alert_threshold: float) -> str:
    """Get status color based on thresholds."""
    if value >= alert_threshold:
        return "red"
    elif value >= warn_threshold:
        return "yellow"
    return "green"


def analyze_drift(
    baseline_dir: Path,
    inference_store_dir: Path,
    model_version: str,
    last_n_days: int = 7,
    thresholds: Dict[str, float] = None
) -> Dict[str, Any]:
    """
    Analyze drift between baseline and recent inferences.
    
    Returns drift metrics and status.
    """
    thresholds = thresholds or load_config()
    
    # Load baseline profiles
    feature_profile_path = baseline_dir / model_version / "feature_profile.json"
    score_profile_path = baseline_dir / model_version / "score_profile.json"
    baseline_metadata_path = baseline_dir / model_version / "baseline_metadata.json"
    
    if not feature_profile_path.exists():
        raise FileNotFoundError(f"Feature profile not found: {feature_profile_path}")
    
    with open(feature_profile_path, "r", encoding="utf-8") as f:
        feature_profiles = json.load(f)
    
    with open(score_profile_path, "r", encoding="utf-8") as f:
        score_profile = json.load(f)
    
    with open(baseline_metadata_path, "r", encoding="utf-8") as f:
        baseline_metadata = json.load(f)
    
    # Load recent inferences
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=last_n_days)
    
    inference_events = load_inference_events(inference_store_dir, start_date, end_date)
    
    if not inference_events:
        return {
            "status": "no_data",
            "message": f"No inference data found for last {last_n_days} days",
            "window_start": start_date.isoformat(),
            "window_end": end_date.isoformat(),
        }
    
    logger.info(f"Loaded {len(inference_events)} inference events")
    
    # Extract feature values from inferences
    feature_values = extract_feature_values(inference_events)
    score_values = extract_score_values(inference_events)
    
    # Compute drift for each feature
    feature_drift = {}
    for feature, profile in feature_profiles.items():
        current_vals = feature_values.get(feature, [])
        
        if profile.get("type") == "numeric":
            psi, details = compute_numeric_psi(profile, current_vals)
        else:
            psi, details = compute_categorical_psi(profile, current_vals)
        
        # Compute missing rate delta
        baseline_missing = profile.get("missing_rate", 0)
        current_missing = 1 - len(current_vals) / len(inference_events) if inference_events else 0
        missing_delta = current_missing - baseline_missing
        
        status = get_status(
            psi,
            thresholds["feature_psi_warn"],
            thresholds["feature_psi_alert"]
        )
        
        # Check missing rate delta
        if abs(missing_delta) >= thresholds["missing_rate_delta_alert"]:
            status = "red"
        elif abs(missing_delta) >= thresholds["missing_rate_delta_warn"] and status == "green":
            status = "yellow"
        
        feature_drift[feature] = {
            "psi": round(psi, 4),
            "baseline_missing_rate": round(baseline_missing, 4),
            "current_missing_rate": round(current_missing, 4),
            "missing_delta": round(missing_delta, 4),
            "status": status,
            "type": profile.get("type", "unknown"),
            "details": details,
        }
    
    # Compute score drift
    if score_values:
        baseline_hist = score_profile.get("histogram", {})
        baseline_freq = baseline_hist.get("frequencies", [])
        
        if baseline_freq:
            bin_edges = baseline_hist.get("bin_edges", [i/20 for i in range(21)])
            current_counts, _ = np.histogram(score_values, bins=bin_edges)
            current_freq = (current_counts / len(score_values)).tolist()
            score_psi = compute_psi(baseline_freq, current_freq)
        else:
            score_psi = 0.0
        
        score_mean_baseline = score_profile.get("mean", 0.5)
        score_mean_current = float(np.mean(score_values))
        score_delta_mean = score_mean_current - score_mean_baseline
        
        score_status = get_status(
            score_psi,
            thresholds["score_psi_warn"],
            thresholds["score_psi_alert"]
        )
    else:
        score_psi = 0.0
        score_mean_current = 0.0
        score_delta_mean = 0.0
        score_status = "no_data"
    
    # Compute global status
    n_red = sum(1 for f in feature_drift.values() if f["status"] == "red")
    n_yellow = sum(1 for f in feature_drift.values() if f["status"] == "yellow")
    n_features = len(feature_drift)
    
    if n_red > 0 or score_status == "red":
        global_status = "red"
    elif n_yellow / n_features > thresholds["yellow_feature_pct"] if n_features > 0 else False:
        global_status = "yellow"
    elif score_status == "yellow":
        global_status = "yellow"
    else:
        global_status = "green"
    
    return {
        "model_version": model_version,
        "baseline_created_at": baseline_metadata.get("created_at"),
        "window_start": start_date.isoformat(),
        "window_end": end_date.isoformat(),
        "n_requests": len(inference_events),
        "n_instances": sum(e.get("n_instances", 1) for e in inference_events),
        "global_status": global_status,
        "feature_drift": feature_drift,
        "score_drift": {
            "psi": round(score_psi, 4),
            "baseline_mean": round(score_profile.get("mean", 0.5), 4),
            "current_mean": round(score_mean_current, 4),
            "delta_mean": round(score_delta_mean, 4),
            "status": score_status,
        },
        "summary": {
            "n_features": n_features,
            "n_red": n_red,
            "n_yellow": n_yellow,
            "n_green": n_features - n_red - n_yellow,
        },
        "thresholds_used": thresholds,
    }


def load_inference_events(
    store_dir: Path,
    start_date: datetime,
    end_date: datetime
) -> List[Dict[str, Any]]:
    """Load inference events from store."""
    events = []
    
    # Try parquet first, then csv
    for ext in ["parquet", "csv"]:
        files = sorted(store_dir.glob(f"inferences_*.{ext}"))
        
        for file_path in files:
            date_str = file_path.stem.replace("inferences_", "")
            try:
                file_date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            except ValueError:
                continue
            
            if file_date.date() < start_date.date() or file_date.date() > end_date.date():
                continue
            
            try:
                if ext == "parquet":
                    df = pd.read_parquet(file_path)
                else:
                    df = pd.read_csv(file_path)
                events.extend(df.to_dict("records"))
            except Exception as e:
                logger.warning(f"Failed to read {file_path}: {e}")
    
    return events


def extract_feature_values(events: List[Dict[str, Any]]) -> Dict[str, List[Any]]:
    """Extract feature values from inference events."""
    feature_values: Dict[str, List[Any]] = {}
    
    for event in events:
        # Try to parse numeric_means if available (aggregate mode)
        numeric_means_str = event.get("numeric_means", "{}")
        try:
            if isinstance(numeric_means_str, str):
                numeric_means = json.loads(numeric_means_str)
            else:
                numeric_means = numeric_means_str or {}
        except json.JSONDecodeError:
            numeric_means = {}
        
        for feature, value in numeric_means.items():
            if feature not in feature_values:
                feature_values[feature] = []
            feature_values[feature].append(value)
        
        # Try features_sanitized if available (row-level mode)
        features_str = event.get("features_sanitized", "{}")
        try:
            if isinstance(features_str, str):
                features = json.loads(features_str)
            else:
                features = features_str or {}
        except json.JSONDecodeError:
            features = {}
        
        for feature, value in features.items():
            if feature not in feature_values:
                feature_values[feature] = []
            feature_values[feature].append(value)
    
    return feature_values


def extract_score_values(events: List[Dict[str, Any]]) -> List[float]:
    """Extract score values from inference events."""
    scores = []
    
    for event in events:
        # Aggregate mode: use risk_score_mean
        if "risk_score_mean" in event:
            scores.append(float(event["risk_score_mean"]))
        # Row-level mode: use risk_score
        elif "risk_score" in event:
            scores.append(float(event["risk_score"]))
    
    return scores


def generate_html_report(drift_metrics: Dict[str, Any], output_path: Path) -> None:
    """Generate HTML drift report."""
    
    status_colors = {
        "green": "#28a745",
        "yellow": "#ffc107",
        "red": "#dc3545",
        "no_data": "#6c757d",
    }
    
    global_status = drift_metrics.get("global_status", "no_data")
    global_color = status_colors.get(global_status, "#6c757d")
    
    # Sort features by PSI (descending)
    feature_drift = drift_metrics.get("feature_drift", {})
    sorted_features = sorted(
        feature_drift.items(),
        key=lambda x: x[1].get("psi", 0),
        reverse=True
    )
    
    # Build feature rows
    feature_rows = []
    for feature, metrics in sorted_features[:20]:  # Top 20
        status = metrics.get("status", "green")
        color = status_colors.get(status, "#28a745")
        feature_rows.append(f"""
        <tr>
            <td>{feature}</td>
            <td>{metrics.get('type', 'unknown')}</td>
            <td>{metrics.get('psi', 0):.4f}</td>
            <td>{metrics.get('missing_delta', 0):+.4f}</td>
            <td style="background-color: {color}; color: white; font-weight: bold;">{status.upper()}</td>
        </tr>
        """)
    
    score_drift = drift_metrics.get("score_drift", {})
    score_status = score_drift.get("status", "no_data")
    score_color = status_colors.get(score_status, "#6c757d")
    
    summary = drift_metrics.get("summary", {})
    
    # Recommended actions based on status
    actions = []
    if global_status == "red":
        actions = [
            "🔴 <strong>CRÍTICO:</strong> Investigar imediatamente as features com drift alto",
            "Verificar se houve mudança no pipeline de dados upstream",
            "Considerar rollback para versão anterior do modelo se performance degradar",
            "Agendar retreino com dados recentes assim que possível",
        ]
    elif global_status == "yellow":
        actions = [
            "🟡 <strong>ATENÇÃO:</strong> Monitorar evolução do drift nos próximos dias",
            "Revisar features com PSI acima do threshold de warning",
            "Verificar se mudanças são sazonais ou permanentes",
            "Preparar pipeline de retreino preventivamente",
        ]
    else:
        actions = [
            "🟢 <strong>OK:</strong> Drift dentro dos limites aceitáveis",
            "Continuar monitoramento regular",
            "Nenhuma ação imediata necessária",
        ]
    
    actions_html = "\n".join([f"<li>{a}</li>" for a in actions])
    
    html_content = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Drift Report - {drift_metrics.get('model_version', 'unknown')}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 30px;
        }}
        h1 {{
            color: #333;
            border-bottom: 2px solid #eee;
            padding-bottom: 10px;
        }}
        .header-info {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }}
        .info-card {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
        }}
        .info-card label {{
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
        }}
        .info-card .value {{
            font-size: 18px;
            font-weight: bold;
            color: #333;
        }}
        .status-badge {{
            display: inline-block;
            padding: 10px 20px;
            border-radius: 4px;
            font-size: 24px;
            font-weight: bold;
            color: white;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }}
        th {{
            background: #f8f9fa;
            font-weight: 600;
        }}
        tr:hover {{
            background: #f8f9fa;
        }}
        .section {{
            margin-top: 30px;
        }}
        .section h2 {{
            color: #444;
            font-size: 18px;
        }}
        .actions {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 6px;
            margin-top: 30px;
        }}
        .actions ul {{
            margin: 10px 0;
            padding-left: 20px;
        }}
        .actions li {{
            margin: 8px 0;
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin-top: 20px;
        }}
        .summary-item {{
            text-align: center;
            padding: 15px;
            border-radius: 6px;
        }}
        .summary-item .number {{
            font-size: 32px;
            font-weight: bold;
        }}
        .summary-item .label {{
            font-size: 12px;
            color: #666;
        }}
        .score-section {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 6px;
            margin-top: 20px;
        }}
        .score-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-top: 10px;
        }}
        footer {{
            margin-top: 30px;
            text-align: center;
            color: #666;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Drift Report</h1>
        
        <div class="header-info">
            <div class="info-card">
                <label>Model Version</label>
                <div class="value">{drift_metrics.get('model_version', 'unknown')}</div>
            </div>
            <div class="info-card">
                <label>Período Analisado</label>
                <div class="value">{drift_metrics.get('window_start', '')[:10]} a {drift_metrics.get('window_end', '')[:10]}</div>
            </div>
            <div class="info-card">
                <label>Total de Requests</label>
                <div class="value">{drift_metrics.get('n_requests', 0):,}</div>
            </div>
            <div class="info-card">
                <label>Total de Instâncias</label>
                <div class="value">{drift_metrics.get('n_instances', 0):,}</div>
            </div>
        </div>
        
        <div style="text-align: center; margin: 30px 0;">
            <label style="display: block; margin-bottom: 10px; color: #666;">STATUS GERAL</label>
            <span class="status-badge" style="background-color: {global_color};">
                {global_status.upper()}
            </span>
        </div>
        
        <div class="summary-grid">
            <div class="summary-item" style="background: {status_colors['green']}20;">
                <div class="number" style="color: {status_colors['green']};">{summary.get('n_green', 0)}</div>
                <div class="label">Features OK</div>
            </div>
            <div class="summary-item" style="background: {status_colors['yellow']}20;">
                <div class="number" style="color: {status_colors['yellow']};">{summary.get('n_yellow', 0)}</div>
                <div class="label">Features Warning</div>
            </div>
            <div class="summary-item" style="background: {status_colors['red']}20;">
                <div class="number" style="color: {status_colors['red']};">{summary.get('n_red', 0)}</div>
                <div class="label">Features Alert</div>
            </div>
            <div class="summary-item" style="background: #f0f0f0;">
                <div class="number">{summary.get('n_features', 0)}</div>
                <div class="label">Total Features</div>
            </div>
        </div>
        
        <div class="section">
            <h2>🎯 Score Drift</h2>
            <div class="score-section">
                <div class="score-grid">
                    <div>
                        <label style="color: #666; font-size: 12px;">PSI Score</label>
                        <div style="font-size: 24px; font-weight: bold;">{score_drift.get('psi', 0):.4f}</div>
                    </div>
                    <div>
                        <label style="color: #666; font-size: 12px;">Baseline Mean</label>
                        <div style="font-size: 24px; font-weight: bold;">{score_drift.get('baseline_mean', 0):.4f}</div>
                    </div>
                    <div>
                        <label style="color: #666; font-size: 12px;">Current Mean</label>
                        <div style="font-size: 24px; font-weight: bold;">{score_drift.get('current_mean', 0):.4f}</div>
                    </div>
                    <div>
                        <label style="color: #666; font-size: 12px;">Delta Mean</label>
                        <div style="font-size: 24px; font-weight: bold;">{score_drift.get('delta_mean', 0):+.4f}</div>
                    </div>
                    <div>
                        <label style="color: #666; font-size: 12px;">Status</label>
                        <div style="font-size: 24px; font-weight: bold; color: {score_color};">{score_status.upper()}</div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>📈 Top Drift Features</h2>
            <table>
                <thead>
                    <tr>
                        <th>Feature</th>
                        <th>Tipo</th>
                        <th>PSI</th>
                        <th>Δ Missing Rate</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(feature_rows) if feature_rows else '<tr><td colspan="5" style="text-align: center;">Sem dados de features</td></tr>'}
                </tbody>
            </table>
        </div>
        
        <div class="actions">
            <h2>🎬 Ações Recomendadas</h2>
            <ul>
                {actions_html}
            </ul>
        </div>
        
        <footer>
            Gerado em {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')} | 
            Thresholds: PSI warn={drift_metrics.get('thresholds_used', {}).get('feature_psi_warn', 0.1)}, 
            alert={drift_metrics.get('thresholds_used', {}).get('feature_psi_alert', 0.25)}
        </footer>
    </div>
</body>
</html>
"""
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    logger.info(f"HTML report saved to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate drift report")
    parser.add_argument("--model_version", type=str, default="v1.1.0", help="Model version")
    parser.add_argument("--baseline_dir", type=str, default="monitoring/baseline", help="Baseline directory")
    parser.add_argument("--inference_store", type=str, default="monitoring/inference_store", help="Inference store directory")
    parser.add_argument("--output_dir", type=str, default="monitoring/reports", help="Output directory")
    parser.add_argument("--last_n_days", type=int, default=7, help="Number of days to analyze")
    
    args = parser.parse_args()
    
    # Analyze drift
    drift_metrics = analyze_drift(
        baseline_dir=Path(args.baseline_dir),
        inference_store_dir=Path(args.inference_store),
        model_version=args.model_version,
        last_n_days=args.last_n_days
    )
    
    # Generate outputs
    date_str = datetime.now().strftime("%Y%m%d")
    output_dir = Path(args.output_dir) / args.model_version
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save JSON metrics
    json_path = output_dir / f"drift_metrics_{date_str}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(drift_metrics, f, indent=2, default=str)
    
    # Generate HTML report
    html_path = output_dir / f"drift_report_{date_str}.html"
    generate_html_report(drift_metrics, html_path)
    
    print(f"\n✅ Drift report generated successfully")
    print(f"   Status: {drift_metrics.get('global_status', 'unknown').upper()}")
    print(f"   JSON: {json_path}")
    print(f"   HTML: {html_path}")


if __name__ == "__main__":
    main()
