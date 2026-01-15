# SRE Runbook - Incident Response

## Visão Geral

Este runbook contém procedimentos de resposta a incidentes para a API de predição de risco de defasagem escolar.

---

## SLOs (Service Level Objectives)

| Métrica | Target | Crítico |
|---------|--------|---------|
| Latência P95 | ≤ 300ms | > 500ms |
| Error Rate | ≤ 1% | > 5% |
| Availability | 99.5% | < 99% |

### Verificação de SLOs

```bash
# Via API
curl http://localhost:8000/slo

# Resposta esperada
{
  "latency_p95_ms": 45.2,
  "latency_slo_ms": 300,
  "latency_slo_met": true,
  "error_rate": 0.001,
  "error_rate_slo": 0.01,
  "error_rate_slo_met": true,
  "overall_healthy": true
}
```

---

## Endpoints de Monitoramento

| Endpoint | Uso | Auth |
|----------|-----|------|
| `GET /health` | Liveness probe | Não |
| `GET /ready` | Readiness probe | Não |
| `GET /metrics` | Métricas JSON | Sim |
| `GET /metrics?format=prometheus` | Prometheus | Sim |
| `GET /slo` | Status SLO | Sim |

---

## Alertas e Respostas

### 🔴 CRÍTICO: API Não Responde

**Sintoma:** `/health` retorna erro ou timeout

**Diagnóstico:**
```bash
# 1. Verificar container
docker ps | grep datathon
docker logs datathon-api --tail 100

# 2. Verificar recursos
docker stats datathon-api

# 3. Verificar rede
curl -v http://localhost:8000/health
```

**Ações:**
1. Reiniciar container: `docker restart datathon-api`
2. Se persistir, verificar logs de erro
3. Escalar para dev team se erro de modelo

---

### 🔴 CRÍTICO: Modelo Não Carregado

**Sintoma:** `/ready` retorna `{"ready": false, "reason": "model_not_loaded"}`

**Diagnóstico:**
```bash
# Verificar logs de startup
docker logs datathon-api | grep -i "model\|error"

# Verificar arquivos de modelo
docker exec datathon-api ls -la /app/artifacts/
```

**Ações:**
1. Verificar se artifacts existem no container
2. Verificar permissões dos arquivos
3. Rollback para versão anterior se necessário

---

### 🟠 HIGH: Latência Alta (P95 > 300ms)

**Sintoma:** `/slo` mostra `latency_slo_met: false`

**Diagnóstico:**
```bash
# Verificar métricas
curl http://localhost:8000/metrics -H "X-API-Key: $KEY"

# Verificar CPU/memória
docker stats datathon-api

# Verificar batch sizes nos logs
docker logs datathon-api --tail 200 | grep "batch\|instances"
```

**Ações:**
1. Verificar se há batches muito grandes
2. Verificar competição por recursos (CPU throttling)
3. Escalar horizontalmente se necessário

---

### 🟠 HIGH: Error Rate Alto (> 1%)

**Sintoma:** `/slo` mostra `error_rate_slo_met: false`

**Diagnóstico:**
```bash
# Verificar tipos de erro
docker logs datathon-api --tail 500 | grep -i "error\|exception"

# Verificar distribuição de status
curl http://localhost:8000/metrics -H "X-API-Key: $KEY" | jq '.requests'
```

**Ações:**
1. Identificar padrão nos erros (422 = input, 500 = interno)
2. Se 422: Verificar mudança no schema do cliente
3. Se 500: Escalar para dev team

---

### 🟡 MEDIUM: Rate Limiting Ativo

**Sintoma:** Clientes reportando 429

**Diagnóstico:**
```bash
# Verificar headers de rate limit
curl -I http://localhost:8000/predict -H "X-API-Key: $KEY"
# X-RateLimit-Remaining: 0
```

**Ações:**
1. Verificar se é uso legítimo ou abuso
2. Aumentar `RATE_LIMIT_RPM` se necessário
3. Considerar API key adicional para cliente

---

### 🟡 MEDIUM: Drift Detectado

**Sintoma:** Alertas de drift no monitoring

**Diagnóstico:**
```bash
# Executar drift report
python monitoring/drift_report.py --days 7

# Verificar distribution shift
python -c "
from monitoring.inference_store import InferenceStore
store = InferenceStore()
print(store.get_drift_summary())
"
```

**Ações:**
1. Documentar em incident ticket
2. Avaliar necessidade de retrain
3. Seguir processo de retraining (ver `docs/retraining_policy.md`)

---

## Procedimentos Operacionais

### Restart da API

```bash
# Docker standalone
docker restart datathon-api

# Docker Compose
docker-compose restart api

# Kubernetes
kubectl rollout restart deployment/datathon-api
```

### Rollback de Modelo

```bash
# Ver versões disponíveis
python src/registry.py list

# Rollback para versão anterior
python src/registry.py rollback --to v1.0.0

# Reiniciar API para carregar novo modelo
docker restart datathon-api
```

### Escalonamento Horizontal

```bash
# Docker Compose
docker-compose up -d --scale api=3

# Kubernetes
kubectl scale deployment/datathon-api --replicas=3
```

### Limpeza de Dados (Retenção)

```bash
# Dry run
python monitoring/retention.py --dry-run

# Executar limpeza
python monitoring/retention.py --days 30 --include-logs
```

---

## Contacts e Escalonamento

### Níveis de escalonamento

| Nível | Tempo | Contato |
|-------|-------|---------|
| L1 | 0-15 min | SRE on-call |
| L2 | 15-30 min | Tech Lead |
| L3 | 30+ min | Engineering Manager |

### Critérios de escalonamento

- **L1 → L2:** Incidente não resolvido em 15 min OU impacto > 10% usuários
- **L2 → L3:** Incidente crítico não resolvido em 30 min OU rollback necessário

---

## Post-mortem Template

```markdown
# Incident Report: [TÍTULO]

## Summary
- **Date:** YYYY-MM-DD
- **Duration:** X minutes
- **Impact:** X% requests affected
- **Severity:** P1/P2/P3

## Timeline
- HH:MM - Alert triggered
- HH:MM - On-call acknowledged
- HH:MM - Root cause identified
- HH:MM - Mitigation applied
- HH:MM - Resolved

## Root Cause
[Descrição técnica]

## Impact
[Métricas de impacto]

## Resolution
[Ações tomadas]

## Action Items
- [ ] Item 1 (Owner, Due Date)
- [ ] Item 2 (Owner, Due Date)

## Lessons Learned
[O que aprendemos]
```

---

## Checklists

### Deploy Checklist

- [ ] CI passou (tests, lint, security scan)
- [ ] Versão taggeada no registry
- [ ] Config review completo
- [ ] Backup do modelo anterior
- [ ] Comunicação aos stakeholders
- [ ] Rollback plan documentado

### Incident Checklist

- [ ] Incidente reconhecido em < 5 min
- [ ] Comunicação inicial enviada
- [ ] Diagnóstico iniciado
- [ ] Escalonamento se necessário
- [ ] Resolução/mitigação aplicada
- [ ] Post-mortem agendado

### Weekly Review Checklist

- [ ] SLO compliance verificado
- [ ] Alertas revisados
- [ ] Drift monitoring verificado
- [ ] Capacity planning atualizado
- [ ] Incidentes da semana revisados
