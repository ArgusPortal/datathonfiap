# Model Changelog

## Histórico de Versões

### v1.1.0 (2025-01-15) - Current Champion

**Status:** ✅ Production

**Changes:**
- Calibração do modelo via CalibratedClassifierCV (isotonic)
- Novo threshold otimizado: 0.040221
- Melhoria na calibração (Brier Score: 0.15 → 0.12)
- Feature engineering refinado

**Metrics:**
| Metric | v1.0.0 | v1.1.0 | Delta |
|--------|--------|--------|-------|
| AUC-ROC | 0.82 | 0.85 | +0.03 |
| AUC-PR | 0.68 | 0.72 | +0.04 |
| Brier | 0.15 | 0.12 | -0.03 |
| F1 | 0.71 | 0.74 | +0.03 |

**Training Data:**
- Dataset: data/processed/dataset_v2.csv
- Samples: 4,847
- Train/Val/Test: 70/15/15

**Artifacts:**
- Model: `models/registry/v1.1.0/model.joblib`
- Metadata: `models/registry/v1.1.0/metadata.json`
- Signature: `models/registry/v1.1.0/signature.json`

**Approved by:** ML Team Lead
**Deploy date:** 2025-01-15

---

### v1.0.0 (2025-01-01) - Archived

**Status:** 📦 Archived

**Changes:**
- Primeira versão de produção
- Random Forest com 100 estimadores
- Threshold: 0.5 (default)

**Metrics:**
| Metric | Value |
|--------|-------|
| AUC-ROC | 0.82 |
| AUC-PR | 0.68 |
| Brier | 0.15 |
| F1 | 0.71 |

**Known Issues:**
- Calibração subótima
- Threshold default não otimizado para o problema

**Artifacts:**
- Model: `models/registry/v1.0.0/model.joblib`
- Metadata: `models/registry/v1.0.0/metadata.json`

**Deprecated:** 2025-01-15

---

## Versões em Desenvolvimento

### v1.2.0 (Planned)

**Status:** 🔬 Development

**Planned Changes:**
- Incorporar dados de 2025-S1
- Experimentar XGBoost como alternativa
- Feature selection automatizado
- Threshold dinâmico por segmento

**Timeline:**
- [ ] Coleta de dados: 2025-Q1
- [ ] Experimentação: 2025-Q2
- [ ] Validação: 2025-Q2
- [ ] Deploy: 2025-Q3

---

## Política de Versionamento

### Semantic Versioning

```
MAJOR.MINOR.PATCH

MAJOR: Mudança breaking (novo schema, features removidas)
MINOR: Novo modelo, melhorias significativas
PATCH: Bug fixes, ajustes menores
```

### Exemplos

| Mudança | Versão |
|---------|--------|
| Novo algoritmo | +1.0.0 |
| Recalibração | +0.1.0 |
| Fix no pipeline | +0.0.1 |
| Nova feature | +1.0.0 |
| Threshold ajustado | +0.1.0 |

---

## Processo de Release

### Checklist

1. [ ] Treino completo com validação cruzada
2. [ ] Métricas atendem guardrails
3. [ ] Testes de integração passando
4. [ ] Model card atualizado
5. [ ] Changelog atualizado
6. [ ] Review por ML Lead
7. [ ] A/B test ou shadow deploy
8. [ ] Rollout gradual
9. [ ] Monitoramento pós-deploy

### Guardrails para Deploy

| Métrica | Mínimo | Atual |
|---------|--------|-------|
| AUC-ROC | 0.75 | ≥ |
| Precision | 0.65 | ≥ |
| Recall | 0.60 | ≥ |
| Latency P95 | 500ms | ≤ |

---

## Rollback History

| Date | From | To | Reason | Duration |
|------|------|-----|--------|----------|
| - | - | - | Nenhum rollback registrado | - |

---

## Artifact Hashes

### v1.1.0

```
model.joblib: sha256:a1b2c3d4e5f6...
metadata.json: sha256:f6e5d4c3b2a1...
signature.json: sha256:1a2b3c4d5e6f...
```

### v1.0.0

```
model.joblib: sha256:x1y2z3w4v5u6...
metadata.json: sha256:u6v5w4z3y2x1...
```

---

## Notes

- Todos os modelos arquivados mantidos por 1 ano
- Rollback imediato disponível para versão N-1
- Drift monitoring ativo em todas as versões em produção
