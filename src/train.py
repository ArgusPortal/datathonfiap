"""
Train v1: pipeline de treinamento com múltiplos candidatos e calibração.

Uso:
    python -m src.train --data data/processed/modeling_dataset.parquet --artifacts artifacts/
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import (
    RandomForestClassifier,
    HistGradientBoostingClassifier,
    GradientBoostingClassifier,
)
from sklearn.dummy import DummyClassifier
from sklearn.model_selection import train_test_split, GroupKFold, StratifiedKFold
from sklearn.calibration import CalibratedClassifierCV

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.preprocessing import (
    build_preprocessor,
    prepare_features,
    convert_mixed_types,
)
from src.feature_engineering import make_features, get_feature_list
from src.evaluate import (
    calculate_metrics,
    select_threshold,
    select_threshold_with_constraints,
    evaluate_predictions,
    compare_models,
    generate_model_comparison_report,
    calculate_calibration_metrics,
)
from src.utils import load_dataset, save_json, set_seed, get_logger

# Configuração
SEED = 42
TARGET_COL = "em_risco_2024"
ID_COLS = ["ra"]
TARGET_YEAR = 2024
PRIMARY_METRIC = "recall"
MIN_RECALL_TARGET = 0.75
CALIBRATION_METHOD = "sigmoid"  # "sigmoid", "isotonic", ou None

logger = get_logger("train")


def load_and_prepare_data(
    data_path: str,
    target_col: str = TARGET_COL,
    id_cols: list = None
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series]:
    """Carrega e prepara dados para treino."""
    if id_cols is None:
        id_cols = ID_COLS

    logger.info(f"Carregando dados de {data_path}")
    df = load_dataset(data_path)
    logger.info(f"Shape original: {df.shape}")

    df = convert_mixed_types(df)
    df = make_features(df)

    X, y = prepare_features(df, target_col, id_cols, TARGET_YEAR)

    logger.info(f"Features: {X.shape[1]}, Amostras: {len(y)}")
    logger.info(f"Target: {y.value_counts().to_dict()}")

    return df, X, y


def create_candidate_models(seed: int = SEED) -> Dict[str, Any]:
    """Cria modelos candidatos para comparação."""
    return {
        "logreg": LogisticRegression(
            class_weight="balanced",
            max_iter=1000,
            random_state=seed,
            solver="lbfgs",
            C=1.0,
        ),
        "hist_gb": HistGradientBoostingClassifier(
            max_iter=100,
            max_depth=6,
            learning_rate=0.1,
            random_state=seed,
            class_weight="balanced",
        ),
        "rf": RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            class_weight="balanced",
            random_state=seed,
            n_jobs=-1,
        ),
    }


def train_single_model(
    model,
    preprocessor,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_val: pd.DataFrame,
    y_val: pd.Series,
    model_name: str,
    calibration: Optional[str] = CALIBRATION_METHOD,
    min_recall: float = MIN_RECALL_TARGET,
    min_precision: Optional[float] = None,
) -> Tuple[Pipeline, Dict[str, Any], float]:
    """
    Treina um modelo individual com validação.
    
    Returns:
        Tuple[pipeline, metrics_dict, threshold]
    """
    pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", model),
    ])

    pipeline.fit(X_train, y_train)

    # Calibração opcional
    if calibration and calibration != "none":
        try:
            calibrated = CalibratedClassifierCV(
                pipeline,
                method=calibration,
                cv=3,
            )
            calibrated.fit(X_train, y_train)
            pipeline = calibrated
        except Exception as e:
            logger.warning(f"Calibração falhou para {model_name}: {e}")

    # Probabilidades em validação
    y_proba_val = pipeline.predict_proba(X_val)[:, 1]

    # Seleciona threshold em validação
    threshold, val_metrics = select_threshold_with_constraints(
        y_val.values,
        y_proba_val,
        objective="max_recall",
        min_recall=min_recall,
        min_precision=min_precision,
    )

    # Adiciona calibração
    if calibration and calibration != "none":
        cal_metrics = calculate_calibration_metrics(y_val.values, y_proba_val)
        val_metrics['brier_score'] = cal_metrics['brier_score']
        val_metrics['calibration_error'] = cal_metrics['calibration_error']

    val_metrics['model_name'] = model_name

    return pipeline, val_metrics, threshold


def train_and_evaluate_v1(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    seed: int = SEED,
    calibration: str = CALIBRATION_METHOD,
    min_recall: float = MIN_RECALL_TARGET,
    min_precision: Optional[float] = None,
) -> Tuple[Dict[str, Dict], Pipeline, float, str]:
    """
    Treina múltiplos candidatos, avalia e seleciona melhor.
    
    Returns:
        Tuple[all_results, best_pipeline, best_threshold, best_model_name]
    """
    set_seed(seed)

    # Preprocessor
    preprocessor, numeric_cols, categorical_cols = build_preprocessor(
        X_train, target_year=TARGET_YEAR
    )
    logger.info(f"Numeric: {len(numeric_cols)}, Categorical: {len(categorical_cols)}")

    # Cria candidatos
    candidates = create_candidate_models(seed)

    # Split interno para validação (usado para threshold selection)
    X_tr, X_val, y_tr, y_val = train_test_split(
        X_train, y_train, test_size=0.2, random_state=seed, stratify=y_train
    )

    results_val = {}
    results_test = {}
    pipelines = {}
    thresholds = {}

    for name, model in candidates.items():
        logger.info(f"\n{'='*50}")
        logger.info(f"Treinando: {name}")

        pipeline, val_metrics, threshold = train_single_model(
            model=model,
            preprocessor=preprocessor,
            X_train=X_tr,
            y_train=y_tr,
            X_val=X_val,
            y_val=y_val,
            model_name=name,
            calibration=calibration,
            min_recall=min_recall,
            min_precision=min_precision,
        )

        results_val[name] = val_metrics
        pipelines[name] = pipeline
        thresholds[name] = threshold

        logger.info(f"  Val Recall: {val_metrics['recall']:.3f}")
        logger.info(f"  Val Precision: {val_metrics['precision']:.3f}")
        logger.info(f"  Threshold: {threshold:.3f}")

        # Avalia no teste final
        y_proba_test = pipeline.predict_proba(X_test)[:, 1]
        y_pred_test = (y_proba_test >= threshold).astype(int)
        test_metrics = evaluate_predictions(
            y_test.values, y_pred_test, y_proba_test, model_name=name,
            include_calibration=(calibration and calibration != "none")
        )
        test_metrics['threshold'] = threshold
        results_test[name] = test_metrics

        logger.info(f"  Test Recall: {test_metrics['recall']:.3f}")
        logger.info(f"  Test Precision: {test_metrics['precision']:.3f}")

    # Seleciona melhor baseado em validação
    best_name = max(
        results_val.items(),
        key=lambda x: (x[1].get('recall', 0), x[1].get('pr_auc', 0))
    )[0]

    logger.info(f"\n{'='*50}")
    logger.info(f"Melhor modelo: {best_name}")
    logger.info(f"  Val Recall: {results_val[best_name]['recall']:.3f}")
    logger.info(f"  Test Recall: {results_test[best_name]['recall']:.3f}")

    all_results = {
        'validation': results_val,
        'test': results_test,
    }

    return all_results, pipelines[best_name], thresholds[best_name], best_name


def save_artifacts_v1(
    artifacts_dir: Path,
    pipeline: Pipeline,
    all_results: Dict[str, Dict],
    threshold: float,
    best_model_name: str,
    feature_names: List[str],
    seed: int = SEED,
    calibration: str = CALIBRATION_METHOD,
) -> None:
    """Salva artefatos v1."""
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    # 1. Model v1
    model_path = artifacts_dir / "model_v1.joblib"
    joblib.dump(pipeline, model_path)
    logger.info(f"Modelo salvo: {model_path}")

    # 2. Metrics v1
    best_test = all_results['test'][best_model_name]
    best_val = all_results['validation'][best_model_name]

    metrics_v1 = {
        "created_at": datetime.now().isoformat(),
        "best_model": best_model_name,
        "threshold": threshold,
        "validation_metrics": best_val,
        "test_metrics": best_test,
        "calibration": calibration,
    }
    save_json(artifacts_dir / "metrics_v1.json", metrics_v1)

    # 3. Metadata v1
    import sklearn
    metadata = {
        "model_version": "v1.1.0",
        "created_at": datetime.now().isoformat(),
        "seed": seed,
        "target_mode": "binary_future_t_plus_1",
        "target_definition": "em_risco=1 se defasagem<0 em t+1 (aluno atrasado)",
        "training_periods": ["2023->2024 (val split interno)"],
        "test_period": "2023->2024 (holdout 20%)",
        "population_filter": "all_phases",
        "expected_features": sorted(feature_names),
        "blocked_features": [
            "ra", "nome", "em_risco_*", "defasagem_*",
            "ponto_virada_*", "pedra_*", "fase_ideal_*",
        ],
        "preprocessing_summary": [
            "SimpleImputer(median) para numéricos",
            "SimpleImputer('missing') para categóricos",
            "OneHotEncoder(handle_unknown='ignore')",
            "StandardScaler para numéricos",
        ],
        "model_family": best_model_name,
        "calibration": calibration,
        "threshold_policy": {
            "objective": "max_recall",
            "min_recall": MIN_RECALL_TARGET,
            "min_precision": None,
            "threshold_value": threshold,
        },
        "libs_versions": {
            "sklearn": sklearn.__version__,
            "pandas": pd.__version__,
            "numpy": np.__version__,
            "joblib": joblib.__version__,
        },
        "assumptions": [
            "Features de 2023 predizem risco em 2024",
            "Sem backtest multi-ano (apenas 2023->2024)",
            "Split holdout simples (sem GroupKFold por escola)",
            "Calibração sigmoid aplicada",
        ],
    }
    save_json(artifacts_dir / "model_metadata_v1.json", metadata)

    # 4. Signature v1
    feature_schema = {}
    for f in feature_names:
        if 'instituicao' in f.lower() or 'fase' in f.lower():
            feature_schema[f] = "object"
        else:
            feature_schema[f] = "float64"

    signature = {
        "input_schema": feature_schema,
        "output_schema": {
            "risk_score": "float",
            "risk_label": "int",
            "model_version": "str",
        },
        "example_request": {f: 5.0 if feature_schema[f] == "float64" else "A"
                           for f in list(feature_names)[:5]},
        "example_response": {
            "risk_score": 0.72,
            "risk_label": 1,
            "model_version": "v1.1.0",
        },
    }
    save_json(artifacts_dir / "model_signature_v1.json", signature)

    # 5. Model Comparison
    comparison_report = generate_model_comparison_report(
        all_results['test'],
        primary_metric=PRIMARY_METRIC,
        constraints={"min_recall": MIN_RECALL_TARGET},
    )
    comparison_report['validation_results'] = all_results['validation']
    comparison_report['test_results'] = all_results['test']
    comparison_report['selection_criteria'] = f"max {PRIMARY_METRIC} em validação"
    save_json(artifacts_dir / "model_comparison.json", comparison_report)

    # 6. Model Report (curto)
    from src.model_card import build_model_card
    report_md = build_model_card(metadata, best_test, comparison_report)
    (artifacts_dir / "model_report.md").write_text(report_md, encoding='utf-8')

    logger.info(f"Todos artefatos v1 salvos em {artifacts_dir}")


def main():
    parser = argparse.ArgumentParser(description="Treina modelo v1")
    parser.add_argument("--data", type=str, default="data/processed/modeling_dataset.parquet")
    parser.add_argument("--artifacts", type=str, default="artifacts")
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--calibration", type=str, default=CALIBRATION_METHOD)

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    set_seed(args.seed)

    logger.info("=" * 60)
    logger.info("PIPELINE DE TREINO v1 - Passos Mágicos")
    logger.info("=" * 60)

    df, X, y = load_and_prepare_data(args.data)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=args.seed, stratify=y
    )
    logger.info(f"Train: {len(y_train)}, Test: {len(y_test)}")

    all_results, best_pipeline, best_threshold, best_name = train_and_evaluate_v1(
        X_train, y_train, X_test, y_test,
        seed=args.seed,
        calibration=args.calibration,
    )

    save_artifacts_v1(
        Path(args.artifacts),
        best_pipeline,
        all_results,
        best_threshold,
        best_name,
        X.columns.tolist(),
        args.seed,
        args.calibration,
    )

    logger.info("\n" + "=" * 60)
    logger.info("COMPARATIVO FINAL (TEST)")
    logger.info("=" * 60)
    comparison = compare_models(all_results['test'], PRIMARY_METRIC)
    print(comparison.to_string(index=False))

    logger.info("\n✅ Pipeline v1 concluído!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
