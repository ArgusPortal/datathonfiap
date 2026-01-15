# Runbook de Monitoramento - API de Risco de Defasagem

## Visão Geral

Este runbook documenta os procedimentos operacionais para monitorar a API de predição de risco de defasagem escolar.

---

## 1. Sinais e Sintomas

### 1.1 Drift Vermelho (Crítico)
- **Sintoma**: Dashboard mostra status RED em features ou score
- **Causa provável**: Mudança significativa na distribuição de dados de entrada
- **Impacto**: Predições podem estar incorretas

### 1.2 Drift Amarelo (Warning)
- **Sintoma**: Dashboard mostra status YELLOW
- **Causa provável**: Drift moderado, possível mudança sazonal
- **Impacto**: Monitorar evolução

### 1.3 Aumento de Erros HTTP
- **Sintoma**: Muitos 4xx/5xx nos logs
- **Causa provável**: Payload inválido, feature faltando, ou erro no modelo
- **Impacto**: Requisições falhando

### 1.4 Latência Alta
- **Sintoma**: `latency_ms` > 500ms consistentemente
- **Causa provável**: Batch muito grande, recursos insuficientes
- **Impacto**: Experiência degradada

---

## 2. Diagnóstico

### 2.1 Gerar Drift Report

```bash
# Gerar relatório de drift dos últimos 7 dias
python -m monitoring.drift_report --model_version v1.1.0 --last_n_days 7

# Relatório gerado em:
# monitoring/reports/v1.1.0/drift_report_YYYYMMDD.html
# monitoring/reports/v1.1.0/drift_metrics_YYYYMMDD.json
```

### 2.2 Inspecionar Logs

```bash
# Buscar logs por request_id específico
grep "request_id.*abc123" logs/app.log

# Ver últimos erros
grep '"level": "ERROR"' logs/app.log | tail -20

# Contar erros por hora
grep '"level": "ERROR"' logs/app.log | cut -d'T' -f1-2 | uniq -c
```

### 2.3 Verificar Versão do Modelo

```bash
# Via endpoint
curl http://localhost:8000/metadata | jq

# Deve retornar:
# {
#   "model_version": "v1.1.0",
#   "threshold": 0.040221,
#   ...
# }
```

### 2.4 Verificar Health

```bash
curl http://localhost:8000/health

# Esperado:
# {"status": "healthy", "model_loaded": true, "model_version": "v1.1.0", ...}
```

### 2.5 Inspecionar Inference Store

```bash
# Listar arquivos de inferência
ls -la monitoring/inference_store/

# Verificar últimos registros (Python)
python -c "
import pandas as pd
from pathlib import Path
files = sorted(Path('monitoring/inference_store').glob('*.parquet'))
if files:
    df = pd.read_parquet(files[-1])
    print(df.tail())
"
```

---

## 3. Ações de Mitigação

### 3.1 Drift Alto em Features

1. **Investigar causa**:
   - Verificar se houve mudança no sistema upstream
   - Analisar features específicas com PSI alto
   - Comparar distribuições baseline vs. atual

2. **Mitigação rápida**:
   - Se feature não-crítica: considerar remover/imputar
   - Se crítica: comunicar stakeholders

3. **Ação corretiva**:
   - Retreinar modelo com dados mais recentes
   - Atualizar baseline

### 3.2 Drift Alto em Score

1. **Verificar performance real** (se ground truth disponível):
   ```bash
   python -c "
   # Calcular métricas com labels reais
   # (requer dados com ground truth)
   "
   ```

2. **Se performance degradou**: iniciar retreino

3. **Se performance OK**: atualizar baseline (drift pode ser aceitável)

### 3.3 Ajustar Threshold

```bash
# 1. Editar variável de ambiente
export THRESHOLD=0.05

# 2. Reiniciar API
docker restart datathon-api

# OU editar .env e reiniciar
```

### 3.4 Rollback de Modelo

```bash
# 1. Verificar versões disponíveis
ls -la artifacts/

# 2. Atualizar variáveis de ambiente
export MODEL_PATH=artifacts/model_v0.joblib
export METADATA_PATH=artifacts/model_metadata_v0.json
export SIGNATURE_PATH=artifacts/model_signature_v0.json

# 3. Reiniciar container
docker restart datathon-api

# 4. Verificar
curl http://localhost:8000/metadata | jq '.model_version'
```

### 3.5 Retreino do Modelo

```bash
# 1. Garantir dados atualizados em data/processed/
python -m src.make_dataset

# 2. Retreinar
python -m src.train

# 3. Avaliar métricas
cat artifacts/model_report_v1.md

# 4. Se métricas OK, deploy
docker build -t datathon-api:v1.x .
docker stop datathon-api
docker run -d -p 8000:8000 --name datathon-api datathon-api:v1.x

# 5. Atualizar baseline
python -m monitoring.build_baseline --model_version v1.x.0
```

---

## 4. Procedimentos de Rotina

### 4.1 Monitoramento Diário

```bash
# Gerar drift report
python -m monitoring.drift_report --last_n_days 1

# Verificar status
open monitoring/reports/v1.1.0/drift_report_$(date +%Y%m%d).html
```

### 4.2 Monitoramento Semanal

```bash
# Drift report semanal
python -m monitoring.drift_report --last_n_days 7

# Verificar tendências
python -c "
import json
from pathlib import Path
reports = sorted(Path('monitoring/reports/v1.1.0').glob('drift_metrics_*.json'))
for r in reports[-7:]:
    data = json.load(open(r))
    print(f\"{r.stem}: {data.get('global_status', 'unknown')}\")
"
```

### 4.3 Atualização de Baseline (Mensal ou após retreino)

```bash
python -m monitoring.build_baseline \
    --model_version v1.1.0 \
    --source data/processed/modeling_dataset.parquet
```

---

## 5. Thresholds e SLAs

### 5.1 Drift Thresholds

| Métrica | Warning | Alert |
|---------|---------|-------|
| Feature PSI | ≥ 0.10 | ≥ 0.25 |
| Score PSI | ≥ 0.10 | ≥ 0.25 |
| Missing Rate Delta | ≥ 0.05 | ≥ 0.10 |

### 5.2 SLAs Operacionais (Sugeridos)

| Métrica | Target |
|---------|--------|
| Latência p95 | < 200ms |
| Taxa de erro | < 1% |
| Disponibilidade | > 99% |

---

## 6. Contatos e Escalação

| Nível | Condição | Ação |
|-------|----------|------|
| L1 | Status Yellow | Monitorar por 24h |
| L2 | Status Red | Investigar causa em 4h |
| L3 | Red + Performance degradada | Rollback + Comunicar stakeholders |

---

## 7. Comandos Rápidos

```bash
# Health check
curl -s http://localhost:8000/health | jq

# Metadata
curl -s http://localhost:8000/metadata | jq

# Predição de teste
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"instances": [{"fase_2023": 3, "idade_2023": 15, "iaa_2023": 6.5}]}'

# Logs em tempo real
docker logs -f datathon-api

# Drift report
python -m monitoring.drift_report --last_n_days 7

# Build baseline
python -m monitoring.build_baseline --model_version v1.1.0

# Restart API
docker restart datathon-api
```
