"""
Model Card: gera relatório curto do modelo.
"""

from typing import Dict, Any
from datetime import datetime


def build_model_card(
    metadata: Dict[str, Any],
    test_metrics: Dict[str, Any],
    comparison: Dict[str, Any],
) -> str:
    """
    Gera model report em markdown (máx ~1 página).
    
    Args:
        metadata: model_metadata_v1.json
        test_metrics: métricas do teste final
        comparison: model_comparison.json
        
    Returns:
        String markdown
    """
    version = metadata.get('model_version', 'v1.0.0')
    target_def = metadata.get('target_definition', 'em_risco=1 se defasagem<0')
    periods = metadata.get('training_periods', ['2023->2024'])
    population = metadata.get('population_filter', 'all_phases')
    model_family = metadata.get('model_family', 'unknown')
    threshold = metadata.get('threshold_policy', {}).get('threshold_value', 0.5)
    calibration = metadata.get('calibration', 'none')
    
    recall = test_metrics.get('recall', 0)
    precision = test_metrics.get('precision', 0)
    f1 = test_metrics.get('f1', 0)
    f2 = test_metrics.get('f2', 0)
    pr_auc = test_metrics.get('pr_auc', 0)
    brier = test_metrics.get('brier_score', None)
    n_samples = test_metrics.get('n_samples', 0)
    n_positive = test_metrics.get('n_positive', 0)
    
    cm = test_metrics.get('confusion_matrix', [[0,0],[0,0]])
    tn, fp = cm[0] if len(cm) > 0 else (0, 0)
    fn, tp = cm[1] if len(cm) > 1 else (0, 0)
    
    ranking = comparison.get('ranking', [])
    ranking_str = "\n".join([
        f"| {r.get('rank',i+1)} | {r.get('model','')} | {r.get('recall',0):.3f} | {r.get('precision',0):.3f} | {r.get('pr_auc',0):.3f} |"
        for i, r in enumerate(ranking[:5])
    ])
    
    md = f"""# Model Report - {version}

**Gerado em:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

## 1. Definição do Problema

- **Target:** {target_def}
- **Período:** {', '.join(periods)}
- **População:** {population}
- **Modelo:** {model_family} (calibração: {calibration})

## 2. Por que Recall como Métrica Principal?

1. **Custo assimétrico:** Não identificar aluno em risco (FN) tem custo maior que falso alerta (FP)
2. **Objetivo operacional:** Maximizar cobertura de alunos vulneráveis para intervenção
3. **Trade-off aceito:** Precisão mais baixa é aceitável se recall alto

## 3. Resultados (Teste Final)

| Métrica | Valor |
|---------|-------|
| **Recall** | **{recall:.3f}** |
| Precision | {precision:.3f} |
| F1 | {f1:.3f} |
| F2 | {f2:.3f} |
| PR-AUC | {pr_auc:.3f} |
| Brier Score | {brier if brier else 'N/A'} |

**Threshold:** {threshold:.4f}

### Matriz de Confusão
```
              Pred=0   Pred=1
Real=0 (ok)    {tn:4d}    {fp:4d}
Real=1 (risco) {fn:4d}    {tp:4d}
```

- Total: {n_samples} amostras ({n_positive} positivos = {100*n_positive/n_samples:.1f}%)

## 4. Comparativo de Modelos

| Rank | Modelo | Recall | Precision | PR-AUC |
|------|--------|--------|-----------|--------|
{ranking_str}

## 5. Threshold Trade-off

- Objetivo: maximizar recall com min_recall ≥ 0.75
- Threshold escolhido em validação: {threshold:.4f}
- Recall final: {recall:.3f} | Precision: {precision:.3f}

## 6. Riscos e Limitações

1. **Sem backtest multi-ano:** validação apenas em 2023→2024
2. **Split simples:** holdout 20%, sem GroupKFold por escola
3. **Population drift:** performance pode variar com mudanças demográficas
4. **Features limitadas:** apenas indicadores 2023 disponíveis
5. **Threshold fixo:** pode precisar recalibração em produção
6. **Desbalanceamento moderado:** ~40% positivos, tratado com class_weight

---
*Relatório gerado automaticamente por src/model_card.py*
"""
    return md
