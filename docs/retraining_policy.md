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
   - Métricas: recall, precision, ROC-AUC, Brier

3. Comparar com champion
   - Recall challenger >= recall champion - 0.02 (guardrail)
   - AUC challenger >= AUC champion

4. Decisão
   - Aprovado: registrar + promover
   - Reprovado: registrar como "rejected" + manter champion
```

## Comandos

```bash
# Retrain completo
python -m src.retrain \
  --new_version v1.2.0 \
  --data data/processed/dataset_train_2023.parquet \
  --registry models/registry

# Apenas comparar (dry-run)
python -m src.retrain \
  --new_version v1.2.0 \
  --data data/processed/dataset_train_2023.parquet \
  --dry_run
```

## Guardrails

- Recall não pode cair mais que 2% (absoluto)
- Precision não pode cair mais que 5% (absoluto)
- Brier Score não pode aumentar mais que 0.02
- Mínimo 500 amostras de validação
