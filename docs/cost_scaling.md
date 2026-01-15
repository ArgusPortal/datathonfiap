# Scaling & Cost Estimation

## Resource Sizing

### Single Instance (Baseline)

| Resource | Minimum | Recommended | Max |
|----------|---------|-------------|-----|
| CPU | 0.5 cores | 1 core | 2 cores |
| Memory | 256 MB | 512 MB | 1 GB |
| Storage | 500 MB | 1 GB | 2 GB |

### Performance Characteristics

| Metric | Value @ 1 CPU, 512MB |
|--------|----------------------|
| Cold start | ~3s |
| Warm latency P50 | 40ms |
| Warm latency P95 | 100ms |
| Max RPS (single) | ~25 |
| Batch 100 latency | ~500ms |

---

## Scaling Strategy

### Horizontal Scaling Formula

```
replicas = ceil(target_rps / rps_per_instance)

Exemplo:
  target_rps = 100
  rps_per_instance = 20
  replicas = ceil(100/20) = 5
```

### Scaling Triggers

| Metric | Scale Up | Scale Down |
|--------|----------|------------|
| CPU utilization | > 70% | < 30% |
| Memory utilization | > 80% | < 40% |
| Request latency P95 | > 200ms | < 50ms |
| Queue depth | > 10 | < 2 |

### Kubernetes HPA Example

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: datathon-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: datathon-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
```

---

## Load Scenarios

### Low Traffic (Dev/Staging)

| Parameter | Value |
|-----------|-------|
| Expected RPS | 1-5 |
| Replicas | 1 |
| CPU request | 0.25 |
| Memory request | 256Mi |

### Medium Traffic (Production Típica)

| Parameter | Value |
|-----------|-------|
| Expected RPS | 10-50 |
| Replicas | 2-3 |
| CPU request | 0.5 |
| Memory request | 512Mi |

### High Traffic (Pico)

| Parameter | Value |
|-----------|-------|
| Expected RPS | 50-200 |
| Replicas | 5-10 |
| CPU request | 1.0 |
| Memory request | 1Gi |

---

## Cost Estimation

### AWS ECS Fargate

| Config | vCPU | Memory | Price/hour | Monthly (24/7) |
|--------|------|--------|------------|----------------|
| Small | 0.25 | 0.5 GB | $0.012 | ~$9 |
| Medium | 0.5 | 1 GB | $0.024 | ~$18 |
| Large | 1.0 | 2 GB | $0.048 | ~$35 |

**Exemplo: 3 replicas Medium**
- 3 × $18 = $54/mês

### AWS EC2 (alternativa)

| Instance | vCPU | Memory | Price/hour | Monthly |
|----------|------|--------|------------|---------|
| t3.micro | 2 | 1 GB | $0.0104 | ~$8 |
| t3.small | 2 | 2 GB | $0.0208 | ~$15 |
| t3.medium | 2 | 4 GB | $0.0416 | ~$30 |

### Google Cloud Run

| Config | vCPU | Memory | Price/million req |
|--------|------|--------|-------------------|
| Default | 1 | 512 MB | ~$0.40 |

**Exemplo: 1M requests/mês**
- Compute: ~$0.40
- Free tier: 2M requests/mês

### Azure Container Instances

| Config | vCPU | Memory | Price/hour |
|--------|------|--------|------------|
| Small | 0.5 | 1 GB | $0.025 |
| Medium | 1.0 | 2 GB | $0.05 |

---

## Cost Optimization

### Estratégias

1. **Right-sizing**: Monitorar uso real e ajustar recursos
2. **Spot instances**: 60-90% desconto para workloads tolerantes a interrupção
3. **Reserved capacity**: 30-50% desconto para uso previsível
4. **Scale to zero**: Em dev/staging, desligar fora do horário

### Exemplo: Spot + Reserved Mix

```
Production baseline: 2 reserved (sempre on)
Production burst: 3 spot (picos)
Dev/Staging: 1 spot (horário comercial)

Custo estimado:
- 2 reserved × $18 × 0.6 (30% desconto) = $21.60
- 3 spot × $18 × 0.3 (70% desconto, 50% tempo) = $8.10
- 1 spot × $9 × 0.3 × 0.4 (40% tempo) = $1.08

Total: ~$31/mês vs $90 on-demand
```

---

## Monitoring Costs

### Included in baseline

- CloudWatch/Stackdriver básico
- Health checks
- Logs (retention limitada)

### Additional costs

| Service | Estimativa |
|---------|------------|
| CloudWatch detailed | $3-5/mês |
| Log retention 30d | $0.50/GB |
| Alerts | $0.10/alarm |

---

## Capacity Planning

### Fórmulas

```python
# RPS necessário
rps = daily_requests / (active_hours * 3600)

# Exemplo
daily_requests = 50000
active_hours = 12
rps = 50000 / (12 * 3600) = 1.16 RPS

# Com headroom (2x)
target_rps = rps * 2 = 2.32 RPS
replicas = ceil(2.32 / 20) = 1
```

### Seasonal Adjustments

| Período | Fator |
|---------|-------|
| Período letivo | 1.0x |
| Início de semestre | 1.5x |
| Fim de ano | 0.5x |
| Férias | 0.2x |

---

## Summary por Ambiente

### Development

```yaml
replicas: 1
cpu: 0.25
memory: 256Mi
cost: ~$9/mês
```

### Staging

```yaml
replicas: 1
cpu: 0.5
memory: 512Mi
cost: ~$18/mês
```

### Production

```yaml
replicas: 2-5
cpu: 0.5-1.0
memory: 512Mi-1Gi
cost: ~$36-90/mês
```

### Total Estimated

| Environment | Monthly Cost |
|-------------|--------------|
| Development | $9 |
| Staging | $18 |
| Production | $50 |
| **Total** | **~$77/mês** |

---

## Recommendations

1. **Start small**: 1 replica em staging, 2 em prod
2. **Monitor first**: Coletar métricas por 1-2 semanas antes de escalar
3. **Use HPA**: Deixar Kubernetes escalar automaticamente
4. **Set budgets**: Alertas de custo em 80% e 100% do orçamento
5. **Review monthly**: Ajustar sizing baseado em uso real
