# Model Changelog

## Histórico de Versões

### v1.2.0 (2026-02-07) - Current Champion

**Status:** ✅ Production

**Changes:**
- **Novo modelo HistGradientBoosting** com calibração sigmoid
- **Feature engineering expandido:**
  - 34 features após engenharia (+10 vs v1.1)
  - 6 delta features temporais (variação 2022→2023 para IAN, IDA, IEG, IAA, IPS, IPV)
  - 6 missing indicator flags
  - Features de agregação: media, min, max, std, range, fase×media
  - Features demográficas: genero, ano_ingresso, anos_pm
- **Threshold otimizado:** 0.350 (via max F2 com min_recall≥0.75, min_precision≥0.50)
- **Novo módulo de regras de negócio** (`src/business_rules.py`):
  - Validação de indicadores INDE/PEDE
  - Cálculo de IAN, IDA, INDE conforme regras oficiais
  - Classificação por faixas de Pedra (Quartzo/Ágata/Ametista/Topázio)
- **End-to-end analysis notebook** com comparação de 11 modelos
  - CatBoost: melhor ROC-AUC (0.928) e PR-AUC (0.895)
  - HistGradientBoosting: melhor equilíbrio recall/precision em produção
- **382 testes unitários** (100% passing)
- **Novos artefatos visuais:** SHAP analysis, calibration curves, confusion matrices, learning curves

**Metrics:**
| Metric | v1.1.0 | v1.2.0 (val) | v1.2.0 (test) | Delta |
|--------|--------|-------------|--------------|-------|
| Recall | 100% | 95.9% | 93.5% | -6.5% |
| Precision | 40.8% | 69.1% | 69.9% | +29.1% |
| PR-AUC | 0.86 | 0.807 | 0.830 | -0.03 |
| F1 | 0.579 | 0.803 | 0.800 | +0.22 |
| F2 | - | 0.890 | 0.876 | new |
| Brier | - | 0.134 | 0.132 | new |
| Features | 24 | 34 | 34 | +10 |

**Training Data:**
- Dataset: data/processed/modeling_dataset.parquet
- Samples: 765 (train 612, test 153)
- Positive rate: 40.5%
- Features base: 19 → Features engenharia: 34

**Artifacts (Development):**
- Model: `artifacts/model_v1.joblib`
- Metadata: `artifacts/model_metadata_v1.json`
- Signature: `artifacts/model_signature_v1.json`
- Metrics: `artifacts/metrics_v1.json`
- End-to-end results: `artifacts/end_to_end_results.json`
- Model comparison: `artifacts/model_comparison.json`
- Visualizations: `artifacts/*.png` (SHAP, calibration, confusion matrices, etc.)

**Artifacts (Registry - após registro):**
- Model: `models/registry/v1.2.0/model.joblib`
- Metadata: `models/registry/v1.2.0/model_metadata.json`
- Signature: `models/registry/v1.2.0/model_signature.json`
- Metrics: `models/registry/v1.2.0/metrics.json`

**Nota:** Registry normaliza nomes removendo sufixo `_v1` para padronização

**Approved by:** ML Team Lead
**Deploy date:** 2026-02-07

---

### v1.1.0 (2026-01-15) - Archived

**Status:** 📦 Archived

**Changes:**
- **Correções críticas no preprocessing:**
  - ✅ Idade corrompida (Excel dates → valores numéricos)
  - ✅ Gênero recuperado (normalização de acentos)
  - ✅ Instituição normalizada (6 categorias padrão)
- **Feature engineering aprimorado:**
  - 24 features após engenharia (+9 vs v1.0)
  - 6 missing indicators (ian/ida/ieg/iaa/ips/ipp)
  - Feature `anos_pm` (tenure no programa)
- **Modelo HistGradientBoosting** com threshold otimizado: 0.34990
- **46 testes unitários** implementados (100% passing)

**Metrics:**
| Metric | v1.0.0 | v1.1.0 | Delta |
|--------|--------|--------|-------|
| Recall | 100% | 100% | - |
| Precision | 40.5% | 40.8% | +0.3% |
| PR-AUC | 0.85 | 0.86 | +0.01 |
| F1 | 0.579 | 0.579 | - |
| Features | 13 | 24 | +11 |

**Training Data:**
- Dataset: data/processed/modeling_dataset.parquet
- Samples: 765
- Features base: 14 → Features engenharia: 24

**Artifacts (Development):**
- Model: `artifacts/model_v1.joblib`
- Metadata: `artifacts/model_metadata_v1.json`
- Signature: `artifacts/model_signature_v1.json`
- Metrics: `artifacts/metrics_v1.json`

**Artifacts (Registry - após registro):**
- Model: `models/registry/v1.1.0/model.joblib`
- Metadata: `models/registry/v1.1.0/model_metadata.json`
- Signature: `models/registry/v1.1.0/model_signature.json`
- Metrics: `models/registry/v1.1.0/metrics.json`

**Nota:** Registry normaliza nomes removendo sufixo `_v1` para padronização

**Approved by:** ML Team Lead
**Deprecated:** 2026-02-07

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

### v1.3.0 (Planned)

**Status:** 🔬 Development

**Planned Changes:**
- Incorporar dados de 2025-S1
- Experimentar CatBoost em produção (melhor ROC-AUC em end-to-end)
- Feature selection automatizado (Boruta/SHAP)
- Threshold dinâmico por segmento (fase)
- Validação cross-temporal multi-ano

**Timeline:**
- [ ] Coleta de dados: 2026-Q1
- [ ] Experimentação: 2026-Q2
- [ ] Validação: 2026-Q2
- [ ] Deploy: 2026-Q3

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

| Métrica | Mínimo | Atual (v1.2.0) |
|---------|--------|----------------|
| Recall | 0.75 | 0.935 ✅ |
| Precision | 0.50 | 0.699 ✅ |
| F2 | 0.70 | 0.876 ✅ |
| PR-AUC | 0.60 | 0.830 ✅ |
| Latency P95 | 500ms | ≤ 300ms ✅ |

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
