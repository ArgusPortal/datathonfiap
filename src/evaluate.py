"""Model evaluation module."""

import logging
from typing import Dict, Any, Optional
import numpy as np
import pandas as pd
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    recall_score,
    precision_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    precision_recall_curve
)

from .config import Config

logger = logging.getLogger(__name__)


class ModelEvaluator:
    """Handles model evaluation and metrics calculation."""
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.metrics = {}
        
    def evaluate(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        y_proba: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """
        Evaluate model performance with comprehensive metrics.
        
        Args:
            y_true: True labels
            y_pred: Predicted labels
            y_proba: Predicted probabilities (if available)
            
        Returns:
            Dictionary with evaluation metrics
        """
        logger.info("Evaluating model performance")
        
        # Basic classification metrics
        metrics = {
            'recall': recall_score(y_true, y_pred, pos_label=1),
            'precision': precision_score(y_true, y_pred, pos_label=1),
            'f1': f1_score(y_true, y_pred, pos_label=1),
            'recall_negative': recall_score(y_true, y_pred, pos_label=0),
            'precision_negative': precision_score(y_true, y_pred, pos_label=0),
        }
        
        # Confusion matrix
        cm = confusion_matrix(y_true, y_pred)
        metrics['confusion_matrix'] = cm.tolist()
        metrics['true_negatives'] = int(cm[0, 0])
        metrics['false_positives'] = int(cm[0, 1])
        metrics['false_negatives'] = int(cm[1, 0])
        metrics['true_positives'] = int(cm[1, 1])
        
        # Probability-based metrics (if probabilities available)
        if y_proba is not None:
            metrics['roc_auc'] = roc_auc_score(y_true, y_proba)
            metrics['pr_auc'] = average_precision_score(y_true, y_proba)
            
            # Precision at target recall
            precisions, recalls, thresholds = precision_recall_curve(y_true, y_proba)
            target_recall = self.config.RECALL_TARGET
            
            # Find precision at target recall
            idx = np.argmin(np.abs(recalls - target_recall))
            metrics['precision_at_recall_75'] = float(precisions[idx])
            metrics['threshold_at_recall_75'] = float(thresholds[idx]) if idx < len(thresholds) else 0.5
        
        # Store metrics
        self.metrics = metrics
        
        # Log key metrics
        logger.info(f"Recall (positive class): {metrics['recall']:.3f}")
        logger.info(f"Precision (positive class): {metrics['precision']:.3f}")
        logger.info(f"F1 Score: {metrics['f1']:.3f}")
        
        if y_proba is not None:
            logger.info(f"ROC-AUC: {metrics['roc_auc']:.3f}")
            logger.info(f"PR-AUC: {metrics['pr_auc']:.3f}")
        
        return metrics
    
    def check_mvp_criteria(self) -> Dict[str, bool]:
        """
        Check if model meets MVP criteria.
        
        Returns:
            Dictionary with criteria checks
        """
        if not self.metrics:
            raise ValueError("No metrics available. Run evaluate() first.")
        
        criteria = {
            'recall_target_met': self.metrics['recall'] >= self.config.RECALL_TARGET,
            'has_probability_metrics': 'pr_auc' in self.metrics,
        }
        
        # Check if precision is reasonable (not too many false positives)
        if 'precision' in self.metrics:
            criteria['precision_reasonable'] = self.metrics['precision'] >= 0.3
        
        logger.info("MVP Criteria Check:")
        for criterion, passed in criteria.items():
            status = "✓" if passed else "✗"
            logger.info(f"  {status} {criterion}: {passed}")
        
        return criteria
    
    def generate_report(self, y_true: np.ndarray, y_pred: np.ndarray) -> str:
        """
        Generate detailed classification report.
        
        Args:
            y_true: True labels
            y_pred: Predicted labels
            
        Returns:
            Classification report as string
        """
        report = classification_report(
            y_true, y_pred,
            target_names=['Not at risk', 'At risk'],
            digits=3
        )
        return report
    
    def analyze_errors(
        self,
        X: pd.DataFrame,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        top_n: int = 10
    ) -> Dict[str, Any]:
        """
        Analyze prediction errors.
        
        Args:
            X: Feature DataFrame
            y_true: True labels
            y_pred: Predicted labels
            top_n: Number of error examples to return
            
        Returns:
            Dictionary with error analysis
        """
        # Identify false positives and false negatives
        fp_mask = (y_true == 0) & (y_pred == 1)
        fn_mask = (y_true == 1) & (y_pred == 0)
        
        error_analysis = {
            'n_false_positives': int(fp_mask.sum()),
            'n_false_negatives': int(fn_mask.sum()),
            'false_positive_rate': float(fp_mask.sum() / (y_true == 0).sum()),
            'false_negative_rate': float(fn_mask.sum() / (y_true == 1).sum()),
        }
        
        # Sample false negatives (most critical errors)
        if fn_mask.sum() > 0:
            fn_indices = np.where(fn_mask)[0][:top_n]
            error_analysis['false_negative_samples'] = X.iloc[fn_indices].to_dict('records')
        
        logger.info(f"Error Analysis:")
        logger.info(f"  False Positives: {error_analysis['n_false_positives']}")
        logger.info(f"  False Negatives: {error_analysis['n_false_negatives']}")
        logger.info(f"  FP Rate: {error_analysis['false_positive_rate']:.3f}")
        logger.info(f"  FN Rate: {error_analysis['false_negative_rate']:.3f}")
        
        return error_analysis


def evaluate_model(
    model,
    X_test: pd.DataFrame,
    y_test: np.ndarray,
    config: Optional[Config] = None
) -> Dict[str, Any]:
    """
    Convenience function to evaluate a trained model.
    
    Args:
        model: Trained model with predict and predict_proba methods
        X_test: Test features
        y_test: Test labels
        config: Configuration object
        
    Returns:
        Dictionary with evaluation metrics
    """
    evaluator = ModelEvaluator(config)
    
    # Get predictions
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]  # Probability of positive class
    
    # Evaluate
    metrics = evaluator.evaluate(y_test, y_pred, y_proba)
    
    # Check MVP criteria
    criteria = evaluator.check_mvp_criteria()
    metrics['mvp_criteria'] = criteria
    
    # Generate report
    report = evaluator.generate_report(y_test, y_pred)
    metrics['classification_report'] = report
    
    # Error analysis
    errors = evaluator.analyze_errors(X_test, y_test, y_pred)
    metrics['error_analysis'] = errors
    
    return metrics
