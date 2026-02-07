# Playbook Operacional — Modelo de Risco de Defasagem

## 1. Comandos Essenciais

> Detalhes completos em `README.md`. Aqui apenas referência rápida.

| Ação | Comando |
|------|---------|
| Subir API (dev) | `uvicorn app.main:app --reload` |
| Subir API (Docker) | `docker-compose up -d` |
| Rodar testes | `pytest tests/ --cov=src --cov=app` |
| Gerar drift report | `python monitoring/drift_report.py` |
| Executar retraining | `python src/retrain.py` |
| Rollback de modelo | `python src/registry.py rollback --to vX.Y.Z` |

---

## 2. Como Ler Logs e Métricas

### Campos-chave no Log
```json
{
  "request_id": "uuid",
  "timestamp": "ISO8601",
  "model_version": "v1.2.0",
  "latency_ms": 45.2,
  "status_code": 200,
  "risk_score": 0.73,
  "risk_band": "alto"
}
```

### Onde encontrar
| Dado | Local |
|------|-------|
| Logs de inferência | `monitoring/inference_store.jsonl` |
| Métricas de API | `GET /metrics` |
| Status de SLO | `GET /slo` |
| Health check | `GET /health` |

---

## 3. Drift Report — Interpretação

### Executar
```bash
python monitoring/drift_report.py
```

### Interpretar Status

| Status | Significado | Ação |
|--------|-------------|------|
| 🟢 Verde | Sem drift significativo | Nenhuma |
| 🟡 Amarelo | Drift moderado detectado | Monitorar por 7 dias |
| 🔴 Vermelho | Drift severo | Investigar + considerar retraining |

### Output
- `monitoring/drift_metrics.json` — métricas detalhadas
- `monitoring/drift_report.html` — relatório visual

---

## 4. Resposta a Incidentes

### SE: Aumento de 5xx (>1% em 5min)
1. Verificar logs: `tail -100 logs/api.log | grep ERROR`
2. Checar health: `curl localhost:8000/health`
3. Se modelo não carregou: reiniciar container
4. Se persistir: rollback para versão anterior
5. Escalar para Owner Técnico

### SE: Latência p95 > 500ms
1. Verificar `GET /metrics` — campo `latency_p95`
2. Checar carga: volume de requests
3. Se carga alta: avaliar scale-up
4. Se carga normal: investigar modelo (tamanho, features)
5. Temporário: aumentar timeout ou rate limit

### SE: Drift Vermelho
1. Confirmar com `python monitoring/drift_report.py`
2. Identificar features afetadas no report
3. Verificar se houve mudança nos dados fonte
4. Comunicar PO Score
5. Decidir: investigar vs. retraining imediato

### SE: Falha de Carga do Modelo
1. Verificar `GET /health` — campo `model_loaded`
2. Checar path do modelo em `MODEL_PATH`
3. Verificar integridade: `python -c "import joblib; joblib.load('models/...')"`
4. Se corrompido: restaurar do registry
5. Reiniciar API

---

## 5. Checklist de Saúde

### Diário (automatizar se possível)
- [ ] API respondendo (`/health` = ok)
- [ ] Taxa de erro < 1%
- [ ] Latência p95 < 300ms
- [ ] Volume de requests dentro do esperado (±20%)

### Semanal
- [ ] Rodar drift report
- [ ] Verificar espaço em disco (logs)
- [ ] Checar security scans (se CI configurado)
- [ ] Revisar alertas pendentes

### Mensal
- [ ] Analisar performance com labels (se disponíveis)
- [ ] Revisar thresholds de risco
- [ ] Revisar features mais importantes
- [ ] Participar da reunião de revisão (ver `monthly_review_agenda.md`)

---

## 6. Árvore de Decisão

```
Problema detectado?
│
├─ Disponibilidade (5xx, timeout)
│  └─ Reiniciar → Rollback → Escalar
│
├─ Performance (latência)
│  └─ Scale → Otimizar → Simplificar modelo
│
├─ Qualidade (drift, métricas)
│  └─ Investigar → Retraining → Rollback
│
└─ Dados (schema break, missing)
   └─ Alertar Data Steward → Congelar scoring
```

---

## 7. Critérios de Ação

| Situação | Ação |
|----------|------|
| Erro rate > 5% por 10min | Rollback imediato |
| Drift vermelho > 7 dias | Retraining obrigatório |
| Recall < 0.75 (com labels) | Congelar + investigar |
| Mudança de schema dados | Congelar + alinhar Data Steward |
| Vulnerabilidade crítica | Patch em 24h ou desativar |

---

## 8. Contatos de Escalação

| Papel | Quando escalar |
|-------|----------------|
| Owner Técnico | Incidentes técnicos, retraining |
| PO Score | Decisões de negócio, thresholds |
| Data Steward | Problemas de dados, schema |
| SRE/Infra | Disponibilidade, infraestrutura |

---

## Referências
- README principal: `README.md`
- Governança: `docs/model_governance.md`
- SRE Runbook detalhado: `docs/sre_runbook.md`
