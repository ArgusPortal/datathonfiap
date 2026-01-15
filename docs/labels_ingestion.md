# Labels Ingestion

## Schema Esperado

```json
{
  "request_id": "abc123",
  "timestamp": "2026-04-15T10:30:00Z",
  "label": 1
}
```

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `request_id` | string | ID do request original (da resposta /predict) |
| `timestamp` | ISO datetime | Quando o label foi coletado |
| `label` | int (0/1) | 0 = não defasou, 1 = defasou |

## Formato Suportado

- `labels_store.jsonl` (um JSON por linha)
- `labels_store.csv`
- `labels_store.parquet`

## Como Jointar com Inferências

1. Inference store: `monitoring/inference_store/dt=YYYY-MM-DD/*.parquet`
2. Labels store: `monitoring/labels_store.jsonl`
3. Join por `request_id` (presente em ambos)

**Nota**: Não usar `ra` ou `student_id` para join (PII).

## Lag Esperado

- Labels chegam ~90 dias após predição
- Performance drift só é calculável após labels

## Comandos

```bash
# Adicionar label (manual)
echo '{"request_id":"abc123","timestamp":"2026-04-15T10:30:00Z","label":1}' >> monitoring/labels_store.jsonl

# Gerar relatório de performance
python -m monitoring.performance_drift --window 30
```
