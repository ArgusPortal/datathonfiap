# Load Test Report

## Configuração do Teste

| Parâmetro | Valor |
|-----------|-------|
| Tool | Locust |
| Target | http://localhost:8000 |
| Users | 10 concurrent |
| Spawn rate | 2 users/second |
| Duration | 60 seconds |
| Target RPS | 10 req/s |

---

## Como Executar

### Pré-requisitos

```bash
pip install locust
```

### Execução

```bash
# Com interface web
locust -f loadtest/locustfile.py --host http://localhost:8000

# Headless (CI/CD)
locust -f loadtest/locustfile.py \
  --host http://localhost:8000 \
  --users 10 \
  --spawn-rate 2 \
  --run-time 60s \
  --headless \
  --csv=loadtest/results

# Com autenticação
export LOAD_TEST_API_KEY="your-api-key"
locust -f loadtest/locustfile.py --host http://localhost:8000
```

### Interface Web

Acesse http://localhost:8089 após iniciar o Locust.

---

## Cenários de Teste

### 1. DefasagemAPIUser (uso normal)

| Task | Weight | Descrição |
|------|--------|-----------|
| health_check | 1 | Verificação de saúde |
| readiness_check | 1 | Probe de readiness |
| get_metadata | 1 | Metadata do modelo |
| get_metrics | 1 | Métricas da API |
| predict_single | 10 | Predição única (principal) |
| predict_batch_small | 3 | Batch de 5 instâncias |
| predict_batch_medium | 1 | Batch de 20 instâncias |

### 2. HighLoadUser (stress test)

- Wait time: 0.1-0.5s (agressivo)
- Apenas predições rápidas
- Pode triggerar rate limiting

---

## Resultados Esperados

### SLOs Target

| Métrica | Target | Aceitável |
|---------|--------|-----------|
| P50 latency | < 100ms | < 150ms |
| P95 latency | < 300ms | < 500ms |
| P99 latency | < 500ms | < 1000ms |
| Error rate | < 1% | < 5% |
| Throughput | > 10 RPS | > 5 RPS |

### Baseline (single instance, 1 CPU)

```
# Métricas típicas observadas
Requests/s: 15-20
P50 latency: 40-60ms
P95 latency: 100-150ms
Error rate: 0%
```

---

## Análise de Resultados

### Métricas do Locust

Após execução, arquivos gerados em `loadtest/results_*.csv`:

- `results_stats.csv`: Estatísticas por endpoint
- `results_stats_history.csv`: Série temporal
- `results_failures.csv`: Falhas detalhadas
- `results_exceptions.csv`: Exceções

### Parsing dos resultados

```python
import pandas as pd

stats = pd.read_csv('loadtest/results_stats.csv')
print(stats[['Name', 'Request Count', 'Average Response Time', 'Requests/s']])
```

### Dashboard simples

```bash
# Ver resumo
cat loadtest/results_stats.csv | column -t -s,

# Verificar falhas
cat loadtest/results_failures.csv
```

---

## Interpretação

### ✅ Teste passou se:

1. P95 < 300ms para `/predict`
2. Error rate < 1%
3. Sem timeout ou connection errors
4. Rate limiting funcionando (429 esperado em stress test)

### ⚠️ Investigar se:

1. P95 > 300ms: Verificar CPU/memória, batch sizes
2. Error rate > 1%: Verificar logs, tipos de erro
3. Muitos 429: Rate limit muito agressivo ou load muito alto

### ❌ Falha se:

1. P95 > 500ms consistentemente
2. Error rate > 5%
3. Connection refused/timeout
4. Memory ou CPU exhaustion

---

## Tuning

### Aumentar throughput

```bash
# Mais workers uvicorn
uvicorn app.main:app --workers 4

# Ajustar rate limit
export RATE_LIMIT_RPM=120
```

### Reduzir latência

1. Verificar batch sizes (limitar a 100)
2. Verificar features desnecessárias
3. Otimizar modelo (quantização, pruning)

### Stress test guidelines

```bash
# Teste agressivo (cuidado com rate limiting)
locust -f loadtest/locustfile.py \
  --host http://localhost:8000 \
  --users 50 \
  --spawn-rate 10 \
  --run-time 120s \
  --headless
```

---

## CI Integration

### GitHub Actions

```yaml
- name: Run load tests
  run: |
    pip install locust
    locust -f loadtest/locustfile.py \
      --host http://localhost:8000 \
      --users 10 \
      --spawn-rate 2 \
      --run-time 30s \
      --headless \
      --csv=loadtest/results
    
    # Verificar P95 < 500ms
    python -c "
    import pandas as pd
    stats = pd.read_csv('loadtest/results_stats.csv')
    p95 = stats[stats['Name'] == '/predict [single]']['95%'].values[0]
    assert p95 < 500, f'P95 too high: {p95}ms'
    "
```

---

## Histórico de Testes

| Data | Versão | Users | RPS | P95 | Errors | Status |
|------|--------|-------|-----|-----|--------|--------|
| 2025-01-15 | v1.1.0 | 10 | 18 | 95ms | 0% | ✅ PASS |

---

## Próximos Passos

1. [ ] Integrar load test no CI
2. [ ] Configurar alertas baseados em resultados
3. [ ] Teste de soak (longa duração)
4. [ ] Teste de spike (burst traffic)
5. [ ] Chaos engineering (falhas injetadas)
