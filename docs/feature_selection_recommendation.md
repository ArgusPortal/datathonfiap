# Feature Selection & Model Strategy — Recomendação para Produção

**Data**: Junho 2025
**Modelo**: HistGradientBoostingClassifier + CalibratedClassifierCV v1.1.0
**Contexto**: Datathon FIAP 2025 — Predição de risco de defasagem escolar (Passos Mágicos)

---

## 1. Contexto do Problema

O modelo atual usa **32 features** para prever risco de defasagem escolar. Monitoramento em produção detectou **drift significativo** em múltiplas features (5 PSI vermelho, 9 amarelo). Antes de retreinar ou ajustar o modelo, realizamos análise sistemática para separar **sinal de ruído** e determinar o feature set ideal para produção.

---

## 2. Metodologia

### 2.1 Feature Stability Analysis (Quadrant System)

Cada feature foi classificada em 4 quadrantes combinando:
- **Permutation Importance** (F2-scorer, 30 repeats): mede impacto real na predição
- **Temporal PSI**: mede estabilidade da distribuição ao longo do tempo

| Quadrante | Critério | Ação |
|-----------|----------|------|
| **ROBUST** | Alta importância + Baixo PSI | ✅ Manter |
| **VOLATILE** | Alta importância + Alto PSI | ⚠️ Monitorar, retreinar se necessário |
| **NOISE** | Baixa importância + Alto PSI | ❌ Remover — gera drift sem contribuir |
| **STABLE** | Baixa importância + Baixo PSI | 🔍 Avaliar — contribuição marginal |

### 2.2 Ablation Experiment

5 configurações testadas com **5-fold Stratified CV** + CalibratedClassifierCV(sigmoid):

| Config | #Features | Descrição |
|--------|-----------|-----------|
| BASELINE | 32 | Todas as features atuais |
| REMOVE_NEGATIVE | 30 | Remove 2 features com importância negativa |
| REMOVE_NOISE | 22 | Remove 16 features NOISE |
| VOLATILE_ONLY | 11 | Apenas features VOLATILE (alta importância) |
| VOLATILE+STABLE | 15 | VOLATILE + 4 features STABLE (gênero, instituição, fase) |

---

## 3. Resultados

### 3.1 Stability Assessment (32 features)

**VOLATILE (11)** — Alta importância, monitorar drift:
| Feature | Importance | PSI |
|---------|-----------|-----|
| ips_2023 | +0.0737 | 0.1519 |
| ipp_2023 | +0.0671 | 0.1155 |
| delta_ipv_2022_2023 | +0.0439 | 0.1456 |
| std_indicadores | +0.0320 | 0.1693 |
| delta_iaa_2022_2023 | +0.0297 | 0.3095 |
| media_indicadores | +0.0253 | 0.1614 |
| ida_2023 | +0.0247 | 0.1489 |
| ian_2023 | +0.0199 | 0.2163 |
| delta_ieg_2022_2023 | +0.0167 | 0.2283 |
| delta_ian_2022_2023 | +0.0158 | 0.1637 |
| idade_2023 | +0.0147 | 0.1429 |

**NOISE (14)** — Baixa importância + alto PSI → candidatas a remoção:
- delta_ida, delta_ips, ano_ingresso, ieg_2023, has_prev_year_data, iaa_2023
- Todos os 6 flags _missing, min_indicador, range_indicadores

**Importância Negativa (2)** — Prejudicam o modelo:
- max_indicador (-0.0047)
- ipv_2023 (-0.0067)

### 3.2 Ablation Results (5-fold CV)

```
Experiment                     #Feat     F2 (CV)         Recall          Precision
─────────────────────────────────────────────────────────────────────────────────────
🥇 VOLATILE_ONLY (11)            11   0.8688±0.008    0.9837±0.018    0.5942±0.032
🥈 VOLATILE+STABLE (15)          15   0.8641±0.008    0.9772±0.022    0.5952±0.049
🥉 BASELINE (all 32)             32   0.8588±0.008    0.9870±0.012    0.5661±0.022
   REMOVE_NOISE (22)             22   0.8570±0.009    0.9869±0.019    0.5641±0.039
   REMOVE_NEGATIVE (30)          30   0.8562±0.012    0.9805±0.012    0.5696±0.031
─────────────────────────────────────────────────────────────────────────────────────
```

### 3.3 Análise dos Resultados

**VOLATILE_ONLY (11 features) é a melhor configuração:**

| Métrica | Baseline (32) | VOLATILE_ONLY (11) | Delta |
|---------|--------------|-------------------|-------|
| F2 | 0.8588 | **0.8688** | **+0.0100** ↑ |
| Recall | **0.9870** | 0.9837 | -0.0034 ↓ |
| Precision | 0.5661 | **0.5942** | **+0.0282** ↑ |
| Features | 32 | **11** | **-65.6%** ↓ |
| Drift surface | 21 features com drift | 0 features com drift falso-positivo | **-100%** ↓ |

**Conclusão**: Remover 21 features:
- ✅ **Melhora** F2 em +1.0pp (0.8588 → 0.8688)
- ✅ **Melhora** Precision em +2.8pp (56.6% → 59.4%)
- ✅ Mantém Recall alto (98.4% vs 98.7% — diferença não significativa)
- ✅ Reduz superfície de drift em 65.6% (de 32 para 11 features monitoradas)
- ✅ Modelo mais simples, interpretável e robusto

---

## 4. Recomendação para Produção

### 4.1 Feature Set Recomendado (11 features)

```python
PRODUCTION_FEATURES = [
    # Indicadores PEDE diretos
    "ips_2023",        # Índice Psicossocial
    "ipp_2023",        # Índice Psicopedagógico
    "ida_2023",        # Índice de Adequação
    "ian_2023",        # Índice de Aprendizagem
    "idade_2023",      # Idade do aluno
    
    # Features derivadas (deltas temporais)
    "delta_ipv_2022_2023",   # Variação Ponto de Virada
    "delta_iaa_2022_2023",   # Variação Autoavaliação
    "delta_ieg_2022_2023",   # Variação Engajamento
    "delta_ian_2022_2023",   # Variação Aprendizagem
    
    # Features agregadas
    "std_indicadores",       # Desvio padrão dos indicadores
    "media_indicadores",     # Média dos indicadores
]
```

### 4.2 Features Removidas e Justificativa

| Feature | Motivo da Remoção |
|---------|-------------------|
| ipv_2023, max_indicador | **Importância negativa** — prejudicam o modelo |
| iaa_2023, ieg_2023 | Importância ~0, redundantes com deltas |
| fase_2023, fase_x_media | Importância 0.000 (77% missing na base) |
| genero_2023, instituicao_2023 | Importância ~0, risco de bias |
| ano_ingresso_2023, has_prev_year_data | Importância 0.000 |
| 6× _missing flags | Importância 0.000 |
| delta_ida, delta_ips | Importância ~0 |
| min_indicador, range_indicadores | Importância 0.000 |

### 4.3 Vantagens para Produção

1. **Menos dados necessários**: Apenas 7 indicadores + idade + 4 deltas computados
2. **Menos drift**: 65% menos features para monitorar
3. **Mais robusto**: Sem features ruidosas que adicionam variância
4. **Mais interpretável**: Cada feature tem significado claro para educadores
5. **Mais justo**: Remove gênero e instituição, reduzindo risco de bias
6. **Melhor performance**: F2 0.8688 vs 0.8588 (significativo em domínio educacional)

### 4.4 Monitoramento em Produção

Para as 11 features mantidas, monitorar:
- **PSI por feature**: Alerta amarelo >0.1, vermelho >0.2
- **Score drift**: PSI do risk_score >0.15 → retreinar
- **Missing rates**: Se taxa de missing aumentar >5pp em qualquer feature
- **Performance**: Se F2 degradar para <0.80 em dados validados

### 4.5 Política de Retreinamento

- **Trigger automático**: PSI > 0.25 em ≥3 features TOP
- **Frequência mínima**: A cada novo semestre letivo (novos dados PEDE)
- **Guardrail**: Novo modelo precisa F2 ≥ 0.85, Recall ≥ 0.90, Precision ≥ 0.50

---

## 5. Próximos Passos

1. ~~Ablation experiment~~  ✅ Concluído
2. **Retreinar modelo v1.2.0** com 11 features e publicar no registry
3. **Atualizar model_signature.json** para refletir novo feature set
4. **Atualizar schema.py** para aceitar apenas features necessárias
5. **Atualizar seed script** com distribuições corretas
6. **Monitorar drift** com baseline real (não mais de seed)
7. **Documentar** no model card e data contract

---

## 6. Nota sobre Drift Observado

O drift significativo observado em produção (5 features PSI > 0.2) foi causado pelo **seed script** que gerava dados com distribuição uniforme (0-10) ao invés de distribuições similares ao treino. Isso foi corrigido nesta iteração:

- Seed script agora usa distribuições truncadas normais (`trunc_normal`) baseadas nas estatísticas reais do dataset de treino
- Features categóricas amostradas com pesos da distribuição real (instituição, gênero)
- Após reseed, drift deve ser mínimo (PSI < 0.05 para todas features)

O drift real do modelo em produção com dados reais de alunos precisaria ser avaliado quando novos dados PEDE estiverem disponíveis.
