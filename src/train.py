"""
Train: pipeline de treinamento MVP com baselines.

Uso:
    python -m src.train --data data/processed/modeling_dataset.parquet --artifacts artifacts/
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.dummy import DummyClassifier
from sklearn.model_selection import train_test_split

# Imports locais
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.preprocessing import (
    build_preprocessor, 
    prepare_features, 
    convert_mixed_types,
)
from src.feature_engineering import make_features
from src.evaluate import (
    calculate_metrics, 
    select_threshold, 
    evaluate_predictions,
    compare_models
)
from src.utils import load_dataset, save_json, set_seed, get_logger


# Configuração
SEED = 42
TARGET_COL = "em_risco_2024"
ID_COLS = ["ra"]
TARGET_YEAR = 2024
MIN_RECALL_TARGET = 0.75

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
    logger.info(f"Shape: {df.shape}")
    
    # Converte tipos mistos
    df = convert_mixed_types(df)
    
    # Aplica feature engineering
    df = make_features(df)
    
    # Prepara X e y
    X, y = prepare_features(df, target_col, id_cols, TARGET_YEAR)
    
    logger.info(f"Features: {X.shape[1]}, Amostras: {len(y)}")
    logger.info(f"Target distribution: {y.value_counts().to_dict()}")
    
    return df, X, y


def create_baselines(seed: int = SEED) -> Dict[str, Any]:
    """Cria modelos baseline."""
    return {
        "baseline0_naive": DummyClassifier(strategy="most_frequent", random_state=seed),
        "baseline1_logistic": LogisticRegression(
            class_weight="balanced",
            max_iter=1000,
            random_state=seed,
            solver="lbfgs"
        ),
        "baseline2_rf": RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            class_weight="balanced",
            random_state=seed,
            n_jobs=-1
        )
    }


def train_and_evaluate(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    seed: int = SEED
) -> Tuple[Dict[str, Dict], Pipeline, float]:
    """Treina baselines e avalia."""
    set_seed(seed)
    
    # Constrói preprocessor
    preprocessor, numeric_cols, categorical_cols = build_preprocessor(
        X_train, target_year=TARGET_YEAR
    )
    
    logger.info(f"Numeric cols: {numeric_cols}")
    logger.info(f"Categorical cols: {categorical_cols}")
    
    # Cria baselines
    models = create_baselines(seed)
    
    results = {}
    best_model_name = None
    best_recall = -1
    best_pipeline = None
    best_threshold = 0.5
    
    for name, model in models.items():
        logger.info(f"\n{'='*50}")
        logger.info(f"Treinando: {name}")
        
        if name == "baseline0_naive":
            pipeline = model
            pipeline.fit(X_train, y_train)
            y_pred_test = pipeline.predict(X_test)
            y_proba_test = np.full(len(y_test), y_train.mean())
            threshold = 0.5
        else:
            pipeline = Pipeline([
                ("preprocessor", preprocessor),
                ("classifier", model)
            ])
            
            pipeline.fit(X_train, y_train)
            
            y_proba_train = pipeline.predict_proba(X_train)[:, 1]
            y_proba_test = pipeline.predict_proba(X_test)[:, 1]
            
            threshold, _ = select_threshold(
                y_train.values, 
                y_proba_train,
                objective="max_recall",
                min_precision=None,
                min_recall=MIN_RECALL_TARGET
            )
            
            y_pred_test = (y_proba_test >= threshold).astype(int)
        
        metrics = evaluate_predictions(
            y_test.values, 
            y_pred_test, 
            y_proba_test,
            model_name=name
        )
        metrics["threshold"] = float(threshold)
        results[name] = metrics
        
        logger.info(f"  Recall: {metrics['recall']:.3f}")
        logger.info(f"  Precision: {metrics['precision']:.3f}")
        logger.info(f"  F2: {metrics['f2']:.3f}")
        logger.info(f"  Threshold: {threshold:.3f}")
        
        if metrics["recall"] > best_recall and name != "baseline0_naive":
            best_recall = metrics["recall"]
            best_model_name = name
            best_pipeline = pipeline
            best_threshold = threshold
    
    logger.info(f"\n{'='*50}")
    logger.info(f"Melhor modelo: {best_model_name} (Recall: {best_recall:.3f})")
    
    return results, best_pipeline, best_threshold


def save_artifacts(
    artifacts_dir: Path,
    pipeline: Pipeline,
    results: Dict[str, Dict],
    threshold: float,
    feature_names: list,
    seed: int = SEED
) -> None:
    """Salva artefatos de treino."""
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Modelo
    model_path = artifacts_dir / "model.joblib"
    joblib.dump(pipeline, model_path)
    logger.info(f"Modelo salvo: {model_path}")
    
    # 2. Métricas
    best_model = max(
        [(k, v["recall"]) for k, v in results.items() if k != "baseline0_naive"],
        key=lambda x: x[1]
    )[0]
    
    metrics = {
        "created_at": datetime.now().isoformat(),
        "best_model": best_model,
        "threshold": threshold,
        "baselines": results,
        "notes": [
            "Recall otimizado como métrica principal",
            "Threshold selecionado em dados de treino",
            "Dataset limitado a 2023→2024 (sem backtest multi-ano)"
        ]
    }
    save_json(artifacts_dir / "metrics.json", metrics)
    
    # 3. Metadata
    import sklearn
    metadata = {
        "model_version": "v1.0.0",
        "created_at": datetime.now().isoformat(),
        "seed": seed,
        "sklearn_version": sklearn.__version__,
        "pandas_version": pd.__version__,
        "numpy_version": np.__version__,
        "target_definition": "em_risco = 1 se Defasagem < 0 (aluno atrasado)",
        "training_periods": ["2023->2024"],
        "population_filter": "all_phases",
        "expected_features": sorted(feature_names),
        "blocked_features": [
            "ra", "em_risco", "defasagem", "ponto_virada", 
            "pedra", "fase_ideal", "destaque_*", "rec_*"
        ],
        "threshold_policy": {
            "objective": "max_recall",
            "min_precision": None,
            "threshold_value": threshold
        },
        "assumptions": [
            "Features de 2023 predizem risco em 2024",
            "Sem dados de 2022 disponíveis no dataset final",
            "Split train/test por holdout simples (20%)"
        ]
    }
    save_json(artifacts_dir / "model_metadata.json", metadata)
    
    # 4. Signature
    feature_schema = {f: "float64" for f in feature_names}
    for f in feature_names:
        if "instituicao" in f.lower() or "fase" in f.lower():
            feature_schema[f] = "object"
    
    signature = {
        "input_schema": feature_schema,
        "output_schema": {
            "risk_score": "float",
            "risk_label": "int",
            "model_version": "str"
        },
        "example_request": {
            f: 5.0 if feature_schema[f] == "float64" else "example"
            for f in list(feature_names)[:5]
        },
        "example_response": {
            "risk_score": 0.65,
            "risk_label": 1,
            "model_version": "v1.0.0"
        }
    }
    save_json(artifacts_dir / "model_signature.json", signature)
    
    logger.info(f"Todos artefatos salvos em {artifacts_dir}")


def main():
    parser = argparse.ArgumentParser(description="Treina modelo de risco")
    parser.add_argument("--data", type=str, default="data/processed/modeling_dataset.parquet")
    parser.add_argument("--artifacts", type=str, default="artifacts")
    parser.add_argument("--seed", type=int, default=SEED)
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    set_seed(args.seed)
    
    logger.info("="*60)
    logger.info("PIPELINE DE TREINO - Passos Mágicos MVP")
    logger.info("="*60)
    
    df, X, y = load_and_prepare_data(args.data)
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=args.seed, stratify=y
    )
    
    logger.info(f"Train: {len(y_train)}, Test: {len(y_test)}")
    
    results, best_pipeline, best_threshold = train_and_evaluate(
        X_train, y_train, X_test, y_test, seed=args.seed
    )
    
    save_artifacts(
        Path(args.artifacts),
        best_pipeline,
        results,
        best_threshold,
        X.columns.tolist(),
        args.seed
    )
    
    logger.info("\n" + "="*60)
    logger.info("COMPARATIVO DE MODELOS")
    logger.info("="*60)
    comparison = compare_models(results)
    print(comparison.to_string(index=False))
    
    logger.info("\n✅ Pipeline concluído com sucesso!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
