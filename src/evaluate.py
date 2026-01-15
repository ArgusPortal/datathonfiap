"""
Evaluate: métricas e seleção de threshold.
"""

import logging
from typing import Dict, Any, Optional, Tuple
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
)

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
    
    # Remove último elemento (recall sempre é 0, precision é indefinido)
    precisions = precisions[:-1]
    recalls = recalls[:-1]
    
    best_threshold = 0.5
    best_score = -1
    
    for i, (p, r, t) in enumerate(zip(precisions, recalls, thresholds)):
        # Verifica constraints
        if min_precision is not None and p < min_precision:
            continue
        if r < min_recall:
            continue
        
        # Calcula score baseado no objetivo
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
    
    # Calcula métricas no threshold escolhido
    y_pred = (y_proba >= best_threshold).astype(int)
    metrics_at_threshold = calculate_metrics(y_true, y_pred, y_proba)
    metrics_at_threshold['threshold'] = float(best_threshold)
    
    return best_threshold, metrics_at_threshold


def evaluate_predictions(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_proba: Optional[np.ndarray] = None,
    model_name: str = "model"
) -> Dict[str, Any]:
    """
    Avalia predições e retorna relatório completo.
    """
    metrics = calculate_metrics(y_true, y_pred, y_proba)
    
    # Adiciona análise de erros
    n_total = len(y_true)
    n_positive = int(y_true.sum())
    n_negative = n_total - n_positive
    
    metrics['n_samples'] = n_total
    metrics['n_positive'] = n_positive
    metrics['n_negative'] = n_negative
    metrics['baseline_rate'] = float(n_positive / n_total) if n_total > 0 else 0
    metrics['model_name'] = model_name
    
    return metrics


def compare_models(results: Dict[str, Dict]) -> pd.DataFrame:
    """
    Compara resultados de múltiplos modelos.
    
    Args:
        results: Dict de {model_name: metrics_dict}
        
    Returns:
        DataFrame com comparativo
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
        })
    
    df = pd.DataFrame(rows)
    df = df.sort_values('recall', ascending=False)
    return df
