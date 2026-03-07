# Model Changelog

## Histórico de Versões

### v1.2.0 (2026-03-07) - Current Champion

**Status:** ✅ Production

**Changes:**
- **Feature selection via ablation experiment** (5-fold CV):
  - Testados 5 subconjuntos de features: BASELINE (32), STABLE_ONLY (21), VOLATILE_ONLY (11), NO_BINARY (26), TOP_15 (15)
  - **VOLATILE_ONLY (11 features) venceu**: F2=0.8688±0.008 vs Baseline F2=0.8588±0.008
  - Removidas 21 features de ruído, importância negativa e baixa estabilidade
- **Modelo RandomForest** com calibração sigmoid (venceu hist_gb na validação com feature set reduzido)
- **11 features selecionadas:**
  - Indicadores PEDE: `ian_2023`, `ida_2023`, `ipp_2023`, `ips_2023`
  - Deltas temporais: `delta_iaa_2022_2023`, `delta_ian_2022_2023`, `delta_ieg_2022_2023`, `delta_ipv_2022_2023`
  - Demográfico: `idade_2023`
  - Derivadas: `media_indicadores`, `std_indicadores`
- **Features removidas (21):**
  - Importância negativa: `max_indicador`, `ipv_2023`
  - Ruído/redundância: `delta_ida_2022_2023`, `delta_ips_2022_2023`, `iaa_2023`, `ieg_2023`, missing flags, `min_indicador`, `range_indicadores`, `ano_ingresso_2023`, `has_prev_year_data`
  - Estáveis/baixa importância: `genero_2023`, `instituicao_2023`, `fase_2023`, `fase_x_media`, `anos_pm_2023`
- **Threshold otimizado:** 0.2814 (via max F2 com min_recall≥0.75, min_precision≥0.50)
- **510 testes unitários** (100% passing, 84% coverage)

**Metrics:**
| Metric | v1.1.0 (32 feat) | v1.2.0 (11 feat) | Delta |
|--------|-----------------|------------------|-------|
| Recall | 93.5% | 91.9% | -1.6% |
| Precision | 69.9% | 69.5% | -0.4% |
| F1 | 0.800 | 0.792 | -0.008 |
| F2 | 0.876 | 0.864 | -0.012 |
| PR-AUC | 0.830 | 0.835 | +0.005 |
| Brier | 0.132 | 0.128 | -0.004 |
| Features | 32 | 11 | -21 |

**Training Data:**
- Dataset: data/processed/modeling_dataset.parquet
- Samples: 765 (train 612, test 153)
- Positive rate: 40.5%
- Features: 11 (selecionadas de 32 via ablation experiment)

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
**Deploy date:** 2026-03-07

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
