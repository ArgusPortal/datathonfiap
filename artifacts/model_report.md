# Model Report - v1.2.0

**Gerado em:** 2026-02-07 18:56

## 1. Definição do Problema

- **Target:** em_risco=1 se defasagem<0 em t+1 (aluno atrasado)
- **Período:** 2023->2024 (val split interno)
- **População:** all_phases
- **Modelo:** hist_gb (calibração: sigmoid)

## 2. Por que Recall como Métrica Principal?

1. **Custo assimétrico:** Não identificar aluno em risco (FN) tem custo maior que falso alerta (FP)
2. **Objetivo operacional:** Maximizar cobertura de alunos vulneráveis para intervenção
3. **Trade-off aceito:** Precisão mais baixa é aceitável se recall alto

## 3. Resultados (Teste Final)

| Métrica | Valor |
|---------|-------|
| **Recall** | **0.935** |
| Precision | 0.699 |
| F1 | 0.800 |
| F2 | 0.876 |
| PR-AUC | 0.830 |
| Brier Score | 0.13162929645602361 |

**Threshold:** 0.3499

### Matriz de Confusão
```
              Pred=0   Pred=1
Real=0 (ok)      66      25
Real=1 (risco)    4      58
```

- Total: 153 amostras (62 positivos = 40.5%)

## 4. Comparativo de Modelos

| Rank | Modelo | Recall | Precision | PR-AUC |
|------|--------|--------|-----------|--------|
| 1 | hist_gb | 0.935 | 0.699 | 0.830 |
| 2 | rf | 0.984 | 0.592 | 0.847 |
| 3 | logreg | 0.984 | 0.530 | 0.852 |
| 4 | dummy_baseline | 0.000 | 0.000 | 0.423 |

## 5. Threshold Trade-off

- Objetivo: maximizar recall com min_recall ≥ 0.75
- Threshold escolhido em validação: 0.3499
- Recall final: 0.935 | Precision: 0.699

## 6. Riscos e Limitações

1. **Sem backtest multi-ano:** validação apenas em 2023→2024
2. **Split simples:** holdout 20%, sem GroupKFold por escola
3. **Population drift:** performance pode variar com mudanças demográficas
4. **Features limitadas:** apenas indicadores 2023 disponíveis
5. **Threshold fixo:** pode precisar recalibração em produção
6. **Desbalanceamento moderado:** ~40% positivos, tratado com class_weight

---
*Relatório gerado automaticamente por src/model_card.py*
