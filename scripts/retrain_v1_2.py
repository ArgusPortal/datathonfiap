"""
Retrain v1.2.0 — 11 features (VOLATILE_ONLY) from ablation experiment.

Based on feature_selection_recommendation.md and ablation_results.json:
- VOLATILE_ONLY (11 features): F2=0.8688 > Baseline (32): F2=0.8588
- Removes noise, negative-importance, and bias-risk features
- Same pipeline: HistGradientBoosting + CalibratedClassifierCV(sigmoid)

Usage:
    python scripts/retrain_v1_2.py
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.calibration import CalibratedClassifierCV
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import (
    HistGradientBoostingClassifier,
    RandomForestClassifier,
)
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.evaluate import (
    calculate_calibration_metrics,
    compare_models,
    evaluate_predictions,
    generate_model_comparison_report,
    select_threshold_with_constraints,
)
from src.feature_engineering import make_features
from src.model_card import build_model_card
from src.preprocessing import build_preprocessor, convert_mixed_types, prepare_features
from src.utils import get_logger, load_dataset, save_json, set_seed

# === Configuration ===
SEED = 42
TARGET_COL = "em_risco_2024"
ID_COLS = ["ra"]
TARGET_YEAR = 2024
PRIMARY_METRIC = "f2"
MIN_RECALL = 0.75
MIN_PRECISION = 0.50
CALIBRATION = "sigmoid"
MODEL_VERSION = "v1.2.0"

# 11 VOLATILE features from ablation experiment
SELECTED_FEATURES = [
    "delta_iaa_2022_2023",
    "delta_ian_2022_2023",
    "delta_ieg_2022_2023",
    "delta_ipv_2022_2023",
    "ian_2023",
    "ida_2023",
    "idade_2023",
    "ipp_2023",
    "ips_2023",
    "media_indicadores",
    "std_indicadores",
]

logger = get_logger("retrain_v1_2")


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    set_seed(SEED)

    artifacts_dir = Path("artifacts")
    artifacts_dir.mkdir(exist_ok=True)

    # === 1. Load and prepare data ===
    logger.info("=" * 60)
    logger.info(f"RETRAIN {MODEL_VERSION} — {len(SELECTED_FEATURES)} features")
    logger.info("=" * 60)

    df = load_dataset("data/processed/modeling_dataset.parquet")
    df = convert_mixed_types(df)
    df = make_features(df)
    X_all, y = prepare_features(df, TARGET_COL, ID_COLS, TARGET_YEAR)

    # Filter to selected features only
    missing = [f for f in SELECTED_FEATURES if f not in X_all.columns]
    if missing:
        logger.error(f"Features not found in dataset: {missing}")
        sys.exit(1)

    X = X_all[SELECTED_FEATURES].copy()
    logger.info(f"Dataset: {X.shape[0]} samples, {X.shape[1]} features")
    logger.info(f"Target: {y.value_counts().to_dict()}")
    logger.info(f"Features: {sorted(SELECTED_FEATURES)}")

    # === 2. Train/test split ===
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=SEED, stratify=y
    )
    logger.info(f"Train: {len(y_train)}, Test: {len(y_test)}")

    # Internal validation split for threshold selection
    X_tr, X_val, y_tr, y_val = train_test_split(
        X_train, y_train, test_size=0.2, random_state=SEED, stratify=y_train
    )

    # === 3. Build preprocessor ===
    preprocessor, num_cols, cat_cols = build_preprocessor(X_tr, target_year=TARGET_YEAR)
    logger.info(f"Numeric: {len(num_cols)}, Categorical: {len(cat_cols)}")

    # === 4. Train all candidates ===
    candidates = {
        "dummy_baseline": DummyClassifier(strategy="stratified", random_state=SEED),
        "logreg": LogisticRegression(
            class_weight="balanced", max_iter=1000, random_state=SEED, C=1.0
        ),
        "hist_gb": HistGradientBoostingClassifier(
            max_iter=100, max_depth=6, learning_rate=0.1,
            random_state=SEED, class_weight="balanced",
        ),
        "rf": RandomForestClassifier(
            n_estimators=100, max_depth=10, class_weight="balanced",
            random_state=SEED, n_jobs=-1,
        ),
    }

    results_val = {}
    results_test = {}
    pipelines = {}
    thresholds = {}

    for name, model in candidates.items():
        logger.info(f"\n--- Training: {name} ---")

        pipe = Pipeline([("preprocessor", preprocessor), ("classifier", model)])
        pipe.fit(X_tr, y_tr)

        # Calibrate
        try:
            calibrated = CalibratedClassifierCV(pipe, method=CALIBRATION, cv=3)
            calibrated.fit(X_tr, y_tr)
            pipe = calibrated
        except Exception as e:
            logger.warning(f"Calibration failed for {name}: {e}")

        # Validation: threshold selection
        y_proba_val = pipe.predict_proba(X_val)[:, 1]
        threshold, val_metrics = select_threshold_with_constraints(
            y_val.values, y_proba_val,
            objective="max_f2", min_recall=MIN_RECALL, min_precision=MIN_PRECISION,
        )
        cal = calculate_calibration_metrics(y_val.values, y_proba_val)
        val_metrics["brier_score"] = cal["brier_score"]
        val_metrics["calibration_error"] = cal["calibration_error"]
        val_metrics["model_name"] = name
        results_val[name] = val_metrics
        thresholds[name] = threshold
        pipelines[name] = pipe

        logger.info(f"  Val — Recall: {val_metrics['recall']:.3f}, "
                     f"Precision: {val_metrics['precision']:.3f}, "
                     f"F2: {val_metrics['f2']:.3f}, Threshold: {threshold:.4f}")

        # Test evaluation
        y_proba_test = pipe.predict_proba(X_test)[:, 1]
        y_pred_test = (y_proba_test >= threshold).astype(int)
        test_metrics = evaluate_predictions(
            y_test.values, y_pred_test, y_proba_test,
            model_name=name, include_calibration=True,
        )
        test_metrics["threshold"] = threshold
        results_test[name] = test_metrics

        logger.info(f"  Test — Recall: {test_metrics['recall']:.3f}, "
                     f"Precision: {test_metrics['precision']:.3f}, "
                     f"F2: {test_metrics['f2']:.3f}")

    # === 5. Select best model ===
    best_name = max(
        results_val.items(), key=lambda x: (x[1].get("f2", 0), x[1].get("pr_auc", 0))
    )[0]
    best_test = results_test[best_name]
    best_threshold = thresholds[best_name]
    best_pipeline = pipelines[best_name]

    logger.info(f"\n{'='*60}")
    logger.info(f"BEST MODEL: {best_name}")
    logger.info(f"  Test Recall:    {best_test['recall']:.3f}")
    logger.info(f"  Test Precision: {best_test['precision']:.3f}")
    logger.info(f"  Test F2:        {best_test['f2']:.3f}")
    logger.info(f"  Threshold:      {best_threshold:.6f}")

    # === 6. Save artifacts ===

    # 6a. Model
    model_path = artifacts_dir / "model_v1.joblib"
    joblib.dump(best_pipeline, model_path)
    logger.info(f"Model saved: {model_path}")

    # 6b. Metrics v1
    metrics_v1 = {
        "created_at": datetime.now().isoformat(),
        "best_model": best_name,
        "threshold": best_threshold,
        "validation_metrics": results_val[best_name],
        "test_metrics": best_test,
        "calibration": CALIBRATION,
    }
    save_json(artifacts_dir / "metrics_v1.json", metrics_v1)

    # 6c. Metadata v1
    metadata = {
        "model_version": MODEL_VERSION,
        "created_at": datetime.now().isoformat(),
        "seed": SEED,
        "target_mode": "binary_future_t_plus_1",
        "target_definition": "em_risco=1 se defasagem<0 em t+1 (aluno atrasado)",
        "training_periods": ["2023->2024 (val split interno)"],
        "test_period": "2023->2024 (holdout 20%)",
        "population_filter": "all_phases",
        "expected_features": sorted(SELECTED_FEATURES),
        "blocked_features": [
            "ra", "nome", "em_risco_*", "defasagem_*",
            "ponto_virada_*", "pedra_*", "fase_ideal_*",
        ],
        "removed_features_v1_2": {
            "negative_importance": ["max_indicador", "ipv_2023"],
            "noise": [
                "delta_ida_2022_2023", "delta_ips_2022_2023", "ano_ingresso_2023",
                "ieg_2023", "has_prev_year_data", "iaa_2023",
                "iaa_2023_missing", "ida_2023_missing", "ieg_2023_missing",
                "ips_2023_missing", "ipp_2023_missing", "ipv_2023_missing",
                "min_indicador", "range_indicadores",
            ],
            "stable_low_importance": [
                "genero_2023", "instituicao_2023", "fase_2023",
                "fase_x_media", "anos_pm_2023",
            ],
        },
        "feature_selection_method": "ablation_experiment_5fold_cv",
        "preprocessing_summary": [
            "SimpleImputer(median) para numéricos",
            "StandardScaler para numéricos",
        ],
        "model_family": best_name,
        "calibration": CALIBRATION,
        "threshold_policy": {
            "objective": "max_f2",
            "min_recall": MIN_RECALL,
            "min_precision": MIN_PRECISION,
            "threshold_value": best_threshold,
        },
        "libs_versions": {
            "sklearn": sklearn.__version__,
            "pandas": pd.__version__,
            "numpy": np.__version__,
            "joblib": joblib.__version__,
        },
        "assumptions": [
            "11 features selecionadas via ablation experiment (VOLATILE_ONLY)",
            "Features de 2023 + deltas 2022->2023 predizem risco em 2024",
            "Sem backtest multi-ano (apenas 2023->2024)",
            "Split holdout simples com min_precision=0.50",
            "Calibração sigmoid aplicada",
            "Seleção de threshold via max F2 com constraints",
        ],
    }
    save_json(artifacts_dir / "model_metadata_v1.json", metadata)

    # Also save as model_metadata.json (the one the API loads primarily)
    metadata_api = metadata.copy()
    metadata_api["sklearn_version"] = sklearn.__version__
    save_json(artifacts_dir / "model_metadata.json", metadata_api)

    # 6d. Signature v1
    feature_schema = {f: "float64" for f in sorted(SELECTED_FEATURES)}
    signature = {
        "input_schema": feature_schema,
        "output_schema": {
            "risk_score": "float",
            "risk_label": "int",
            "model_version": "str",
        },
        "example_request": {f: 5.0 for f in list(sorted(SELECTED_FEATURES))[:5]},
        "example_response": {
            "risk_score": 0.72,
            "risk_label": 1,
            "model_version": MODEL_VERSION,
        },
    }
    save_json(artifacts_dir / "model_signature_v1.json", signature)

    # 6e. Model comparison
    comparison = generate_model_comparison_report(
        results_test, primary_metric=PRIMARY_METRIC,
        constraints={"min_recall": MIN_RECALL},
    )
    comparison["validation_results"] = results_val
    comparison["test_results"] = results_test
    comparison["selection_criteria"] = f"max {PRIMARY_METRIC} em validação"
    save_json(artifacts_dir / "model_comparison.json", comparison)

    # 6f. Model report
    report_md = build_model_card(metadata, best_test, comparison)
    (artifacts_dir / "model_report.md").write_text(report_md, encoding="utf-8")

    # === 7. Print comparison table ===
    logger.info(f"\n{'='*60}")
    logger.info("COMPARATIVO FINAL (TEST)")
    logger.info("=" * 60)
    comp_df = compare_models(results_test, PRIMARY_METRIC)
    print(comp_df.to_string(index=False))

    # === 8. Print vs v1.1.0 baseline ===
    logger.info(f"\n{'='*60}")
    logger.info(f"v1.2.0 ({len(SELECTED_FEATURES)} features) SUMMARY")
    logger.info("=" * 60)
    logger.info(f"  Recall:    {best_test['recall']:.3f}")
    logger.info(f"  Precision: {best_test['precision']:.3f}")
    logger.info(f"  F1:        {best_test['f1']:.3f}")
    logger.info(f"  F2:        {best_test['f2']:.3f}")
    logger.info(f"  PR-AUC:    {best_test['pr_auc']:.3f}")
    logger.info(f"  Brier:     {best_test['brier_score']:.4f}")
    logger.info(f"  Threshold: {best_threshold:.6f}")
    logger.info(f"  Features:  {len(SELECTED_FEATURES)}")
    logger.info(f"\n✅ Retrain {MODEL_VERSION} complete!")

    return 0


if __name__ == "__main__":
    sys.exit(main())
