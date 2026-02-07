# Retraining Policy

## Gatilhos para Retrain

| Gatilho | Condição | Ação |
|---------|----------|------|
| **Drift Alert** | score_psi ≥ 0.25 OU feature_psi ≥ 0.25 | Investigar + retrain |
| **Schedule** | Trimestral (quarterly) | Retrain preventivo |
| **Labels** | Novos labels disponíveis (lag ~90 dias) | Avaliar performance + retrain se necessário |

## Processo Champion/Challenger

```
1. Treinar challenger
   python -m src.retrain --new_version vX.Y.Z --data data/processed/...

2. Avaliar com protocolo temporal
   - Split treino/validação respeitando tempo
   - Métricas: recall, precision, F2, PR-AUC, Brier

3. Comparar com champion
   - Recall challenger >= recall champion - 0.02 (guardrail)
   - F2 challenger >= F2 champion
   - PR-AUC challenger >= PR-AUC champion

4. Decisão
   - Aprovado: registrar + promover
   - Reprovado: registrar como "rejected" + manter champion
```

## Comandos

```bash
# Retrain completo
python -m src.retrain \
  --new_version v1.3.0 \
  --data data/processed/dataset_train_2023.parquet \
  --registry models/registry

# Apenas comparar (dry-run)
python -m src.retrain \
  --new_version v1.3.0 \
  --data data/processed/dataset_train_2023.parquet \
  --dry_run
```

## Guardrails

- Recall não pode cair mais que 2% (absoluto) — mínimo: 0.75
- Precision não pode cair mais que 5% (absoluto) — mínimo: 0.50
- Brier Score não pode aumentar mais que 0.02
- F2-Score não pode cair mais que 3% (absoluto)
- Mínimo 100 amostras de validação
- Validação de regras de negócio via `src/business_rules.py`
