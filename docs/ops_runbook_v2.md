# Ops Runbook v2

## Incidentes

### 1. Aumento de 5xx (> 1% por 10 min)

**Sintoma**: Alerta de error rate ou logs com status 500

**Diagnóstico**:
```bash
docker logs datathon-api --tail 100 | grep ERROR
curl http://localhost:8000/health
```

**Ação**:
1. Verificar se modelo está carregado (`/health`)
2. Se memory error: reiniciar container
3. Se bug: rollback para versão anterior
   ```bash
   python -m src.registry rollback --version vX.Y.Z --reason "5xx rate alto"
   docker restart datathon-api
   ```

### 2. Latência Alta (p95 > 500ms)

**Sintoma**: Requests lentos

**Diagnóstico**:
```bash
curl -w "@curl-format.txt" -X POST http://localhost:8000/predict ...
```

**Ação**:
1. Verificar batch size (máx 1000)
2. Verificar recursos do container
3. Se persistir: escalar ou investigar modelo

### 3. Drift Vermelho (PSI > 0.25)

**Sintoma**: Drift report com status `red`

**Diagnóstico**:
```bash
python -m monitoring.drift_report --model_version v1.1.0 --last_n_days 7
```

**Ação**:
1. Identificar features com drift alto
2. Investigar causa (mudança de população, bug de dados)
3. Se drift genuíno: iniciar retrain
   ```bash
   python -m src.retrain --new_version vX.Y.Z --data ...
   ```

### 4. Queda de Performance (quando labels disponíveis)

**Sintoma**: Performance report com recall < 0.70

**Diagnóstico**:
```bash
python -m monitoring.performance_drift --window 30
```

**Ação**:
1. Confirmar labels estão corretos
2. Comparar com métricas do treino
3. Retrain com dados mais recentes

---

## Operações de Rotina

### Verificar Status

```bash
# Health
curl http://localhost:8000/health

# Versão atual
curl http://localhost:8000/metadata | jq .model_version

# Champion no registry
cat models/registry/champion.json
```

### Promover Nova Versão

```bash
# 1. Registrar
python -m src.registry register --version vX.Y.Z --artifacts artifacts/

# 2. Promover
python -m src.registry promote --version vX.Y.Z

# 3. Reiniciar API
docker restart datathon-api
```

### Rollback

```bash
# 1. Identificar versão anterior
python -m src.registry list

# 2. Rollback
python -m src.registry rollback --version vX.Y.Z --reason "motivo"

# 3. Reiniciar
docker restart datathon-api

# 4. Validar
curl http://localhost:8000/health
```

### Gerar Relatórios

```bash
# Drift report
python -m monitoring.drift_report --model_version v1.1.0 --last_n_days 7

# Performance (quando labels disponíveis)
python -m monitoring.performance_drift --window 30
```

---

## Contatos

| Role | Responsável |
|------|-------------|
| On-call | {{ON_CALL}} |
| Tech Lead | {{TECH_LEAD}} |
| Data Team | {{DATA_TEAM}} |
