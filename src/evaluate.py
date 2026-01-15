"""
Evaluate: métricas, calibração e seleção de threshold.
"""

import logging
from typing import Dict, Any, Optional, Tuple, List
import numpy as np
import pandas as pd
from sklearn.metrics import (
    recall_score,
    precision_score,
    f1_score,
    fbeta_score,
    confusion_matrix,
    precision_recall_curve,
    average_precision_score,
    brier_score_loss,
)
from sklearn.calibration import calibration_curve

logger = logging.getLogger(__name__)


def calculate_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_proba: Optional[np.ndarray] = None
) -> Dict[str, Any]:
    """
    Calcula métricas de classificação.
    
    Returns:
        Dict com recall, precision, f1, f2, pr_auc, confusion_matrix
    """
    metrics = {
        'recall': float(recall_score(y_true, y_pred, pos_label=1, zero_division=0)),
        'precision': float(precision_score(y_true, y_pred, pos_label=1, zero_division=0)),
        'f1': float(f1_score(y_true, y_pred, pos_label=1, zero_division=0)),
        'f2': float(fbeta_score(y_true, y_pred, beta=2, pos_label=1, zero_division=0)),
    }
    
    cm = confusion_matrix(y_true, y_pred)
    metrics['confusion_matrix'] = cm.tolist()
    metrics['true_negatives'] = int(cm[0, 0]) if cm.shape[0] > 0 else 0
    metrics['false_positives'] = int(cm[0, 1]) if cm.shape[1] > 1 else 0
    metrics['false_negatives'] = int(cm[1, 0]) if cm.shape[0] > 1 else 0
    metrics['true_positives'] = int(cm[1, 1]) if cm.shape[0] > 1 and cm.shape[1] > 1 else 0
    
    if y_proba is not None:
        metrics['pr_auc'] = float(average_precision_score(y_true, y_proba))
    
    return metrics


def calculate_calibration_metrics(
    y_true: np.ndarray,
    y_proba: np.ndarray,
    n_bins: int = 10
) -> Dict[str, Any]:
    """
    Calcula métricas de calibração.
    
    Returns:
        Dict com brier_score, calibration_curve data
    """
    brier = float(brier_score_loss(y_true, y_proba))
    
    try:
        prob_true, prob_pred = calibration_curve(y_true, y_proba, n_bins=n_bins, strategy='uniform')
        calibration_data = {
            'prob_true': prob_true.tolist(),
            'prob_pred': prob_pred.tolist(),
        }
    except ValueError:
        calibration_data = {'prob_true': [], 'prob_pred': []}
    
    return {
        'brier_score': brier,
        'calibration_curve': calibration_data,
        'calibration_error': float(np.mean(np.abs(
            np.array(calibration_data['prob_true']) - np.array(calibration_data['prob_pred'])
        ))) if calibration_data['prob_true'] else None
    }


def select_threshold(
    y_true: np.ndarray,
    y_proba: np.ndarray,
    objective: str = "max_recall",
    min_precision: Optional[float] = None,
    min_recall: float = 0.75
) -> Tuple[float, Dict[str, float]]:
    """
    Seleciona threshold ótimo baseado no objetivo.
    
    Args:
        y_true: Labels verdadeiros
        y_proba: Probabilidades preditas
        objective: "max_recall", "max_f2", ou "balanced"
        min_precision: Precisão mínima requerida (opcional)
        min_recall: Recall mínimo requerido
        
    Returns:
        Tuple[threshold, metrics_at_threshold]
    """
    precisions, recalls, thresholds = precision_recall_curve(y_true, y_proba)
    
    precisions = precisions[:-1]
    recalls = recalls[:-1]
    
    best_threshold = 0.5
    best_score = -1
    
    for i, (p, r, t) in enumerate(zip(precisions, recalls, thresholds)):
        if min_precision is not None and p < min_precision:
            continue
        if r < min_recall:
            continue
        
        if objective == "max_recall":
            score = r
        elif objective == "max_f2":
            score = (5 * p * r) / (4 * p + r) if (4 * p + r) > 0 else 0
        elif objective == "balanced":
            score = 2 * p * r / (p + r) if (p + r) > 0 else 0
        else:
            score = r
        
        if score > best_score:
            best_score = score
            best_threshold = t
    
    y_pred = (y_proba >= best_threshold).astype(int)
    metrics_at_threshold = calculate_metrics(y_true, y_pred, y_proba)
    metrics_at_threshold['threshold'] = float(best_threshold)
    
    return best_threshold, metrics_at_threshold


def select_threshold_with_constraints(
    y_true: np.ndarray,
    y_proba: np.ndarray,
    objective: str = "max_recall",
    min_precision: Optional[float] = None,
    min_recall: Optional[float] = None,
    max_fpr: Optional[float] = None
) -> Tuple[float, Dict[str, Any]]:
    """
    Seleciona threshold com múltiplas restrições.
    
    Returns:
        Tuple[threshold, detailed_metrics]
    """
    precisions, recalls, thresholds = precision_recall_curve(y_true, y_proba)
    precisions, recalls = precisions[:-1], recalls[:-1]
    
    candidates = []
    
    for p, r, t in zip(precisions, recalls, thresholds):
        y_pred = (y_proba >= t).astype(int)
        tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel() if len(np.unique(y_pred)) > 1 else (0, 0, 0, 0)
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
        
        # Aplica constraints
        if min_precision is not None and p < min_precision:
            continue
        if min_recall is not None and r < min_recall:
            continue
        if max_fpr is not None and fpr > max_fpr:
            continue
        
        if objective == "max_recall":
            score = r
        elif objective == "max_f2":
            score = (5 * p * r) / (4 * p + r) if (4 * p + r) > 0 else 0
        elif objective == "max_precision":
            score = p
        else:
            score = 2 * p * r / (p + r) if (p + r) > 0 else 0
        
        candidates.append((t, score, p, r, fpr))
    
    if not candidates:
        # Fallback: retorna threshold 0.5
        y_pred = (y_proba >= 0.5).astype(int)
        return 0.5, calculate_metrics(y_true, y_pred, y_proba)
    
    # Ordena por score
    best = max(candidates, key=lambda x: x[1])
    best_threshold = best[0]
    
    y_pred = (y_proba >= best_threshold).astype(int)
    metrics = calculate_metrics(y_true, y_pred, y_proba)
    metrics['threshold'] = float(best_threshold)
    metrics['fpr'] = best[4]
    
    return best_threshold, metrics


def evaluate_predictions(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_proba: Optional[np.ndarray] = None,
    model_name: str = "model",
    include_calibration: bool = False
) -> Dict[str, Any]:
    """
    Avalia predições e retorna relatório completo.
    """
    metrics = calculate_metrics(y_true, y_pred, y_proba)
    
    n_total = len(y_true)
    n_positive = int(y_true.sum())
    n_negative = n_total - n_positive
    
    metrics['n_samples'] = n_total
    metrics['n_positive'] = n_positive
    metrics['n_negative'] = n_negative
    metrics['baseline_rate'] = float(n_positive / n_total) if n_total > 0 else 0
    metrics['model_name'] = model_name
    
    if include_calibration and y_proba is not None:
        cal_metrics = calculate_calibration_metrics(y_true, y_proba)
        metrics['brier_score'] = cal_metrics['brier_score']
        metrics['calibration_error'] = cal_metrics['calibration_error']
    
    return metrics


def compare_models(
    results: Dict[str, Dict],
    primary_metric: str = "recall"
) -> pd.DataFrame:
    """
    Compara resultados de múltiplos modelos e retorna ranking.
    
    Args:
        results: Dict de {model_name: metrics_dict}
        primary_metric: Métrica principal para ranking
        
    Returns:
        DataFrame com comparativo ordenado
    """
    rows = []
    for name, metrics in results.items():
        rows.append({
            'model': name,
            'recall': metrics.get('recall', 0),
            'precision': metrics.get('precision', 0),
            'f1': metrics.get('f1', 0),
            'f2': metrics.get('f2', 0),
            'pr_auc': metrics.get('pr_auc', None),
            'brier_score': metrics.get('brier_score', None),
            'threshold': metrics.get('threshold', 0.5),
        })
    
    df = pd.DataFrame(rows)
    df = df.sort_values(primary_metric, ascending=False)
    df['rank'] = range(1, len(df) + 1)
    return df


def generate_model_comparison_report(
    results: Dict[str, Dict],
    primary_metric: str = "recall",
    constraints: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Gera relatório completo de comparação de modelos.
    
    Returns:
        Dict com ranking, melhor modelo, trade-offs
    """
    comparison_df = compare_models(results, primary_metric)
    
    best_model = comparison_df.iloc[0]['model']
    best_metrics = results[best_model]
    
    report = {
        'ranking': comparison_df.to_dict(orient='records'),
        'best_model': best_model,
        'best_metrics': best_metrics,
        'primary_metric': primary_metric,
        'constraints_applied': constraints or {},
        'trade_offs': {
            'recall_vs_precision': {
                'chosen_recall': best_metrics.get('recall', 0),
                'chosen_precision': best_metrics.get('precision', 0),
            }
        }
    }
    
    return report
