"""
Ablation experiment: compare model performance with different feature subsets.

Tests 5 configurations using 5-fold stratified CV with calibrated HistGradientBoosting.
"""

import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import numpy as np  # noqa: E402
from sklearn.calibration import CalibratedClassifierCV  # noqa: E402
from sklearn.ensemble import HistGradientBoostingClassifier  # noqa: E402
from sklearn.metrics import fbeta_score, precision_score, recall_score  # noqa: E402
from sklearn.model_selection import StratifiedKFold  # noqa: E402
from sklearn.pipeline import Pipeline  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.feature_engineering import make_features  # noqa: E402
from src.preprocessing import build_preprocessor, convert_mixed_types, prepare_features  # noqa: E402
from src.utils import load_dataset  # noqa: E402

SEED = 42
np.random.seed(SEED)

# Load data
df = load_dataset("data/processed/modeling_dataset.parquet")
df = convert_mixed_types(df)
df = make_features(df)
X, y = prepare_features(df, "em_risco_2024", ["ra"], 2024)

print(f"Dataset: {X.shape[0]} samples, {X.shape[1]} features")
print(f"Target: {y.value_counts().to_dict()}")
print()

# Feature sets from stability analysis
ALL_FEATURES = list(X.columns)
NEGATIVE_FEATS = ["max_indicador", "ipv_2023"]
NOISE_FEATS = [
    "delta_ida_2022_2023",
    "delta_ips_2022_2023",
    "ano_ingresso_2023",
    "ieg_2023",
    "has_prev_year_data",
    "iaa_2023",
    "iaa_missing",
    "ian_missing",
    "ida_missing",
    "ieg_missing",
    "ips_missing",
    "ipp_missing",
    "min_indicador",
    "range_indicadores",
    "max_indicador",
    "ipv_2023",
]
VOLATILE_FEATS = [
    "ips_2023",
    "ipp_2023",
    "delta_ipv_2022_2023",
    "std_indicadores",
    "delta_iaa_2022_2023",
    "media_indicadores",
    "ida_2023",
    "ian_2023",
    "delta_ieg_2022_2023",
    "delta_ian_2022_2023",
    "idade_2023",
]
STABLE_FEATS = ["genero_2023", "instituicao_2023", "fase_2023", "fase_x_media"]

# Experiment configurations
EXPERIMENTS = {
    "BASELINE (all 32)": ALL_FEATURES,
    "REMOVE_NEGATIVE (30)": [f for f in ALL_FEATURES if f not in NEGATIVE_FEATS],
    "REMOVE_NOISE (16)": [f for f in ALL_FEATURES if f not in NOISE_FEATS],
    "VOLATILE_ONLY (11)": VOLATILE_FEATS,
    "VOLATILE+STABLE (15)": VOLATILE_FEATS + STABLE_FEATS,
}

# Stratified 5-fold CV for each experiment
results = []
for name, features in EXPERIMENTS.items():
    X_exp = X[features].copy()

    f2_scores = []
    recall_scores_list = []
    precision_scores_list = []

    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)

    for fold, (train_idx, test_idx) in enumerate(skf.split(X_exp, y)):
        X_train, X_test = X_exp.iloc[train_idx], X_exp.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

        # Build preprocessor (returns tuple)
        preprocessor, _, _ = build_preprocessor(X_train)

        model = HistGradientBoostingClassifier(
            max_iter=100,
            max_depth=6,
            learning_rate=0.1,
            random_state=SEED,
            class_weight="balanced",
        )

        pipe = Pipeline([("preprocessor", preprocessor), ("classifier", model)])

        # Calibrate
        calibrated = CalibratedClassifierCV(pipe, method="sigmoid", cv=3)
        calibrated.fit(X_train, y_train)

        # Predict with threshold optimization
        y_proba = calibrated.predict_proba(X_test)[:, 1]

        # Try thresholds 0.15-0.65
        best_f2 = 0
        best_thresh = 0.35
        for t in np.arange(0.15, 0.65, 0.01):
            y_pred_t = (y_proba >= t).astype(int)
            rec = recall_score(y_test, y_pred_t, zero_division=0)
            prec = precision_score(y_test, y_pred_t, zero_division=0)
            if rec >= 0.75 and prec >= 0.45:
                f2_t = fbeta_score(y_test, y_pred_t, beta=2, zero_division=0)
                if f2_t > best_f2:
                    best_f2 = f2_t
                    best_thresh = t

        y_pred = (y_proba >= best_thresh).astype(int)
        f2 = fbeta_score(y_test, y_pred, beta=2, zero_division=0)
        rec = recall_score(y_test, y_pred, zero_division=0)
        prec = precision_score(y_test, y_pred, zero_division=0)

        f2_scores.append(f2)
        recall_scores_list.append(rec)
        precision_scores_list.append(prec)

    results.append(
        {
            "name": name,
            "n_features": len(features),
            "f2_mean": np.mean(f2_scores),
            "f2_std": np.std(f2_scores),
            "recall_mean": np.mean(recall_scores_list),
            "recall_std": np.std(recall_scores_list),
            "precision_mean": np.mean(precision_scores_list),
            "precision_std": np.std(precision_scores_list),
        }
    )
    print(
        f"  {name}: F2={np.mean(f2_scores):.4f}+/-{np.std(f2_scores):.4f}, "
        f"Recall={np.mean(recall_scores_list):.4f}+/-{np.std(recall_scores_list):.4f}, "
        f"Prec={np.mean(precision_scores_list):.4f}+/-{np.std(precision_scores_list):.4f}"
    )

# Summary table
print()
print("=" * 95)
header = f"{'Experiment':<30} {'#Feat':>5} {'F2':>14} {'Recall':>14} {'Precision':>14}"
print(header)
print("-" * 95)
for r in sorted(results, key=lambda x: x["f2_mean"], reverse=True):
    line = (
        f"{r['name']:<30} {r['n_features']:>5} "
        f"{r['f2_mean']:>6.4f}+/-{r['f2_std']:.3f} "
        f"{r['recall_mean']:>6.4f}+/-{r['recall_std']:.3f} "
        f"{r['precision_mean']:>6.4f}+/-{r['precision_std']:.3f}"
    )
    print(line)
print("=" * 95)

# Identify best
best = max(results, key=lambda x: x["f2_mean"])
baseline = [r for r in results if "BASELINE" in r["name"]][0]
print(f"\nBest: {best['name']} — F2={best['f2_mean']:.4f}")
print(
    f"vs Baseline delta: F2={best['f2_mean'] - baseline['f2_mean']:+.4f}, "
    f"Recall={best['recall_mean'] - baseline['recall_mean']:+.4f}, "
    f"Precision={best['precision_mean'] - baseline['precision_mean']:+.4f}"
)

# Save results JSON
import json  # noqa: E402

out = {
    "experiments": results,
    "best": best["name"],
    "recommendation": (
        "Use VOLATILE+STABLE (15 features) for production"
        if "VOLATILE+STABLE" in best["name"]
        else f"Best config: {best['name']}"
    ),
}
with open("artifacts/ablation_results.json", "w") as f:
    json.dump(out, f, indent=2)
print("\nResults saved to artifacts/ablation_results.json")
