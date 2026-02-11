"""Compute fairness analysis by subgroup for model card."""
import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import recall_score, precision_score, f1_score, fbeta_score

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.feature_engineering import make_features

# Load model
model = joblib.load("artifacts/model_v1.joblib")

# Load metadata for threshold
with open("artifacts/model_metadata_v1.json") as f:
    meta = json.load(f)
threshold = meta["threshold_policy"]["threshold_value"]

# Load signature for feature list
with open("artifacts/model_signature_v1.json") as f:
    sig = json.load(f)
feature_names = sorted(sig["input_schema"].keys())

# Load raw data and engineer features
df = pd.read_parquet("data/processed/modeling_dataset.parquet")

# Save subgroup columns before feature engineering
subgroup_cols = {
    "genero_2023": df["genero_2023"].copy(),
    "fase_2023": df["fase_2023"].copy(),
    "instituicao_2023": df["instituicao_2023"].copy(),
}
y_true = df["em_risco_2024"].values.astype(int)

# Apply feature engineering
df_feat = make_features(df.copy())

# Build feature matrix
X_cols = [c for c in feature_names if c in df_feat.columns]
missing_cols = [c for c in feature_names if c not in df_feat.columns]
print(f"Available: {len(X_cols)}/{len(feature_names)} features")
if missing_cols:
    print(f"Missing: {missing_cols}")
    # Add missing columns as 0
    for col in missing_cols:
        df_feat[col] = 0

X = df_feat[feature_names]

# Predict
y_prob = model.predict_proba(X)[:, 1]
y_pred = (y_prob >= threshold).astype(int)

# Overall metrics
print(f"\n{'='*60}")
print(f"OVERALL (N={len(y_true)}, threshold={threshold:.3f})")
print(f"  Recall:    {recall_score(y_true, y_pred):.3f}")
print(f"  Precision: {precision_score(y_true, y_pred):.3f}")
print(f"  F1:        {f1_score(y_true, y_pred):.3f}")
print(f"  F2:        {fbeta_score(y_true, y_pred, beta=2):.3f}")

results = {"overall": {
    "n": int(len(y_true)),
    "prevalence": float(y_true.mean()),
    "recall": float(recall_score(y_true, y_pred)),
    "precision": float(precision_score(y_true, y_pred)),
    "f1": float(f1_score(y_true, y_pred)),
    "f2": float(fbeta_score(y_true, y_pred, beta=2)),
}, "subgroups": {}}

# Fairness by subgroup
def analyze_subgroup(name, groups, y_t, y_p):
    print(f"\n{'='*60}")
    print(f"FAIRNESS BY {name.upper()}")
    print(f"{'Group':<20} {'N':>5} {'Prev':>6} {'Recall':>7} {'Prec':>7} {'F1':>6} {'F2':>6}")
    print("-" * 60)
    
    subgroup_results = {}
    for group_val in sorted(groups.unique()):
        mask = groups == group_val
        yt = y_t[mask]
        yp = y_p[mask]
        n = int(mask.sum())
        prev = float(yt.mean()) if n > 0 else 0
        
        if yt.sum() > 0 and n >= 5:
            rec = recall_score(yt, yp)
            prec = precision_score(yt, yp, zero_division=0)
            f1 = f1_score(yt, yp, zero_division=0)
            f2 = fbeta_score(yt, yp, beta=2, zero_division=0)
        else:
            rec = prec = f1 = f2 = float("nan")
        
        print(f"{str(group_val):<20} {n:>5} {prev:>6.1%} {rec:>7.3f} {prec:>7.3f} {f1:>6.3f} {f2:>6.3f}")
        subgroup_results[str(group_val)] = {
            "n": n, "prevalence": prev,
            "recall": round(rec, 3) if not np.isnan(rec) else None,
            "precision": round(prec, 3) if not np.isnan(prec) else None,
            "f1": round(f1, 3) if not np.isnan(f1) else None,
            "f2": round(f2, 3) if not np.isnan(f2) else None,
        }
    
    # Compute disparity (max - min recall)
    valid_recalls = [v["recall"] for v in subgroup_results.values() if v["recall"] is not None]
    if len(valid_recalls) >= 2:
        disparity = max(valid_recalls) - min(valid_recalls)
        print(f"\n  Recall disparity: {disparity:.3f} (max-min)")
        subgroup_results["_disparity"] = {"recall_disparity": round(disparity, 3)}
    
    return subgroup_results

results["subgroups"]["genero"] = analyze_subgroup(
    "Gênero", subgroup_cols["genero_2023"], y_true, y_pred
)

results["subgroups"]["fase"] = analyze_subgroup(
    "Fase", subgroup_cols["fase_2023"], y_true, y_pred
)

results["subgroups"]["instituicao"] = analyze_subgroup(
    "Instituição", subgroup_cols["instituicao_2023"], y_true, y_pred
)

# Save results
output_path = Path("artifacts/fairness_analysis.json")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(f"\n\nResults saved to {output_path}")
