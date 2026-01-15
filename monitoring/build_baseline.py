"""
Build baseline profile from training data for drift detection.
Generates feature_profile.json, score_profile.json, baseline_metadata.json.
"""

import argparse
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def compute_numeric_profile(series: pd.Series) -> Dict[str, Any]:
    """Compute profile for numeric feature."""
    clean = series.dropna()
    
    if len(clean) == 0:
        return {
            "type": "numeric",
            "count": 0,
            "missing_rate": 1.0,
            "quantiles": {},
            "mean": None,
            "std": None,
        }
    
    missing_rate = 1 - len(clean) / len(series) if len(series) > 0 else 0
    
    quantiles = {
        "p05": float(clean.quantile(0.05)),
        "p25": float(clean.quantile(0.25)),
        "p50": float(clean.quantile(0.50)),
        "p75": float(clean.quantile(0.75)),
        "p95": float(clean.quantile(0.95)),
    }
    
    return {
        "type": "numeric",
        "count": len(series),
        "missing_rate": round(missing_rate, 4),
        "quantiles": {k: round(v, 4) for k, v in quantiles.items()},
        "mean": round(float(clean.mean()), 4),
        "std": round(float(clean.std()), 4) if len(clean) > 1 else 0.0,
        "min": round(float(clean.min()), 4),
        "max": round(float(clean.max()), 4),
    }


def compute_categorical_profile(series: pd.Series, top_k: int = 10) -> Dict[str, Any]:
    """Compute profile for categorical feature."""
    clean = series.dropna()
    missing_rate = 1 - len(clean) / len(series) if len(series) > 0 else 0
    
    value_counts = clean.value_counts()
    total = len(clean)
    
    top_values = {}
    for val, count in value_counts.head(top_k).items():
        top_values[str(val)] = {
            "count": int(count),
            "freq": round(count / total, 4) if total > 0 else 0
        }
    
    # Add "other" category if there are more values
    other_count = value_counts.iloc[top_k:].sum() if len(value_counts) > top_k else 0
    if other_count > 0:
        top_values["__other__"] = {
            "count": int(other_count),
            "freq": round(other_count / total, 4)
        }
    
    return {
        "type": "categorical",
        "count": len(series),
        "missing_rate": round(missing_rate, 4),
        "n_unique": int(series.nunique()),
        "top_values": top_values,
    }


def compute_score_profile(scores: np.ndarray, n_bins: int = 20) -> Dict[str, Any]:
    """Compute profile for prediction scores."""
    clean = scores[~np.isnan(scores)]
    
    if len(clean) == 0:
        return {"count": 0, "quantiles": {}, "histogram": {}}
    
    quantiles = {
        "p05": float(np.percentile(clean, 5)),
        "p10": float(np.percentile(clean, 10)),
        "p25": float(np.percentile(clean, 25)),
        "p50": float(np.percentile(clean, 50)),
        "p75": float(np.percentile(clean, 75)),
        "p90": float(np.percentile(clean, 90)),
        "p95": float(np.percentile(clean, 95)),
    }
    
    # Create histogram
    bin_edges = np.linspace(0, 1, n_bins + 1)
    hist_counts, _ = np.histogram(clean, bins=bin_edges)
    
    histogram = {
        "bin_edges": [round(e, 4) for e in bin_edges.tolist()],
        "counts": hist_counts.tolist(),
        "frequencies": [round(c / len(clean), 4) for c in hist_counts],
    }
    
    return {
        "count": len(clean),
        "mean": round(float(np.mean(clean)), 4),
        "std": round(float(np.std(clean)), 4),
        "min": round(float(np.min(clean)), 4),
        "max": round(float(np.max(clean)), 4),
        "quantiles": {k: round(v, 4) for k, v in quantiles.items()},
        "histogram": histogram,
        "positive_rate": round(float(np.mean(clean >= 0.5)), 4),
    }


def build_feature_profile(
    df: pd.DataFrame,
    feature_list: List[str],
    signature: Dict[str, str]
) -> Dict[str, Any]:
    """Build feature profiles for all features."""
    profiles = {}
    
    for feature in feature_list:
        if feature not in df.columns:
            logger.warning(f"Feature {feature} not in data, creating empty profile")
            profiles[feature] = {
                "type": "unknown",
                "count": 0,
                "missing_rate": 1.0,
            }
            continue
        
        series = df[feature]
        dtype = signature.get(feature, "float64")
        
        if dtype in ("object", "category", "string"):
            profiles[feature] = compute_categorical_profile(series)
        else:
            # Try to convert to numeric
            try:
                numeric_series = pd.to_numeric(series, errors="coerce")
                profiles[feature] = compute_numeric_profile(numeric_series)
            except Exception:
                profiles[feature] = compute_categorical_profile(series)
    
    return profiles


def build_baseline(
    data_path: Path,
    signature_path: Path,
    metadata_path: Path,
    output_dir: Path,
    model_version: str,
    source: str = "train_data"
) -> Tuple[Path, Path, Path]:
    """
    Build baseline profiles from training data.
    
    Returns paths to: feature_profile.json, score_profile.json, baseline_metadata.json
    """
    logger.info(f"Building baseline for model {model_version}")
    
    # Load signature
    with open(signature_path, "r", encoding="utf-8") as f:
        signature_data = json.load(f)
    
    input_schema = signature_data.get("input_schema", {})
    feature_list = sorted(input_schema.keys())
    
    logger.info(f"Loaded signature with {len(feature_list)} features")
    
    # Load metadata for threshold
    threshold = 0.5
    if metadata_path.exists():
        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        threshold_policy = metadata.get("threshold_policy", {})
        threshold = threshold_policy.get("threshold_value", 0.5)
    
    # Create versioned output directory
    version_dir = output_dir / model_version
    version_dir.mkdir(parents=True, exist_ok=True)
    
    # Load data
    if data_path.suffix == ".parquet":
        df = pd.read_parquet(data_path)
    elif data_path.suffix == ".csv":
        df = pd.read_csv(data_path)
    else:
        raise ValueError(f"Unsupported data format: {data_path.suffix}")
    
    logger.info(f"Loaded data with {len(df)} rows and {len(df.columns)} columns")
    
    # Build feature profile
    feature_profile = build_feature_profile(df, feature_list, input_schema)
    
    # Build score profile (if target column exists or we compute from model)
    # For baseline from train data, we use proxy based on target or synthetic scores
    score_profile = {}
    target_col = "em_risco"
    
    if target_col in df.columns:
        # Use target as proxy for scores (0 or 1)
        scores = df[target_col].astype(float).values
        # Add some noise to simulate probability distribution
        np.random.seed(42)
        noise = np.random.uniform(-0.1, 0.1, len(scores))
        scores = np.clip(scores + noise * 0.5, 0, 1)
        score_profile = compute_score_profile(scores)
        logger.info(f"Built score profile from target column with positive rate: {score_profile.get('positive_rate', 0)}")
    else:
        # Create minimal profile
        logger.warning(f"Target column '{target_col}' not found, creating minimal score profile")
        score_profile = {
            "count": len(df),
            "mean": 0.5,
            "std": 0.2,
            "quantiles": {"p05": 0.1, "p25": 0.3, "p50": 0.5, "p75": 0.7, "p95": 0.9},
            "histogram": {
                "bin_edges": [i/20 for i in range(21)],
                "counts": [len(df)//20] * 20,
                "frequencies": [0.05] * 20,
            },
            "positive_rate": 0.5,
            "note": "synthetic_profile_no_target"
        }
    
    # Build metadata
    baseline_metadata = {
        "model_version": model_version,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "data_path": str(data_path),
        "n_samples": len(df),
        "feature_list": feature_list,
        "n_features": len(feature_list),
        "threshold": threshold,
        "notes": f"Baseline built from {source} with {len(df)} samples",
    }
    
    # Save profiles
    feature_profile_path = version_dir / "feature_profile.json"
    score_profile_path = version_dir / "score_profile.json"
    metadata_file_path = version_dir / "baseline_metadata.json"
    
    with open(feature_profile_path, "w", encoding="utf-8") as f:
        json.dump(feature_profile, f, indent=2)
    
    with open(score_profile_path, "w", encoding="utf-8") as f:
        json.dump(score_profile, f, indent=2)
    
    with open(metadata_file_path, "w", encoding="utf-8") as f:
        json.dump(baseline_metadata, f, indent=2)
    
    logger.info(f"Saved baseline profiles to {version_dir}")
    
    return feature_profile_path, score_profile_path, metadata_file_path


def main():
    parser = argparse.ArgumentParser(description="Build baseline profile for drift detection")
    parser.add_argument("--model_version", type=str, default="v1.1.0", help="Model version")
    parser.add_argument("--signature", type=str, default="artifacts/model_signature_v1.json", help="Path to model signature")
    parser.add_argument("--metadata", type=str, default="artifacts/model_metadata_v1.json", help="Path to model metadata")
    parser.add_argument("--source", type=str, default="data/processed/modeling_dataset.parquet", help="Path to training data")
    parser.add_argument("--output", type=str, default="monitoring/baseline", help="Output directory")
    
    args = parser.parse_args()
    
    build_baseline(
        data_path=Path(args.source),
        signature_path=Path(args.signature),
        metadata_path=Path(args.metadata),
        output_dir=Path(args.output),
        model_version=args.model_version,
        source="train_data"
    )
    
    print(f"\n✅ Baseline built successfully for {args.model_version}")
    print(f"   Output: {args.output}/{args.model_version}/")


if __name__ == "__main__":
    main()
