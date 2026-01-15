# KPIs e Baseline — Modelo de Risco de Defasagem

## 1. KPI Principal de Impacto

### Redução de Defasagem
| Métrica | Definição | Fórmula |
|---------|-----------|---------|
| **Taxa de Defasagem** | % alunos com DEFASAGEM > 0 | `count(DEFASAGEM > 0) / count(alunos)` |
| **IAN Médio** | Índice de Adequação ao Nível | `mean(IAN)` onde IAN ∈ [0, 1] |
| **Redução Relativa** | Variação vs baseline | `(taxa_pos - taxa_baseline) / taxa_baseline` |

### Recortes Obrigatórios
- Por **FASE** (1-9)
- Por **PEDRA** (Topázio, Ametista, Ágata, Quartzo)
- Por **ANO_ESCOLAR**
- Por **período** (bimestre/semestre)

---

## 2. KPIs de Processo (Leading Indicators)

| KPI | Definição | Meta | Frequência |
|-----|-----------|------|------------|
| **Cobertura de Scoring** | % alunos com score calculado | ≥ 95% | Semanal |
| **Taxa de Intervenção** | % alunos alto risco que receberam ação | ≥ 80% | Mensal |
| **Tempo até Ação** | Dias entre score alto e intervenção | ≤ 7 dias | Mensal |
| **Aderência do Time** | % tutores usando score ativamente | ≥ 70% | Mensal |
| **Taxa de Registro** | % intervenções com desfecho registrado | ≥ 60% | Mensal |

---

## 3. Baseline (Período Pré-Adoção)

### Período de Referência
- **Baseline:** 2022-2024 (pré-adoção do modelo)
- **Pós-adoção:** a partir de {{ADOPTION_DATE}}

### Métricas Baseline por Segmento

| Segmento | Taxa Defasagem | IAN Médio | N Alunos |
|----------|----------------|-----------|----------|
| **Geral** | {{baseline_geral}}% | {{ian_geral}} | {{n_geral}} |
| Fase 1-3 | {{baseline_f1}}% | {{ian_f1}} | {{n_f1}} |
| Fase 4-6 | {{baseline_f2}}% | {{ian_f2}} | {{n_f2}} |
| Fase 7-9 | {{baseline_f3}}% | {{ian_f3}} | {{n_f3}} |
| Topázio | {{baseline_top}}% | {{ian_top}} | {{n_top}} |
| Ametista | {{baseline_ame}}% | {{ian_ame}} | {{n_ame}} |
| Ágata | {{baseline_aga}}% | {{ian_aga}} | {{n_aga}} |
| Quartzo | {{baseline_qua}}% | {{ian_qua}} | {{n_qua}} |

*Preencher com dados históricos antes do go-live*

---

## 4. Estratégias de Avaliação de Impacto

### MVP: Antes/Depois com Controle de Sazonalidade
- Comparar mesmo período (bimestre) entre anos
- Ajustar por fatores sazonais conhecidos (ex: início de ano)
- Limitação: não isola efeito do modelo de outras mudanças

### Melhor: Piloto por Grupos (Stepped-Wedge)
- Adoção escalonada por turmas/fases
- Grupo controle = ainda não adotou
- Comparação contemporânea (mesmo período)
- Análise de tendência pré/pós por grupo
- Reduz viés de seleção e sazonalidade

### Critérios para Atribuir Impacto
- Diferença estatisticamente significativa (p < 0.05)
- Magnitude relevante (>5% redução relativa)
- Consistência entre segmentos
- Ausência de fatores confundidores conhecidos

---

## 5. Dicionário de Métricas

| Métrica | Definição | Fonte | Cálculo |
|---------|-----------|-------|---------|
| `DEFASAGEM` | Anos de atraso escolar | Dados cadastrais | `IDADE - IDADE_IDEAL_PARA_FASE` |
| `IAN` | Índice de Adequação ao Nível [0-1] | Avaliações | Score normalizado de adequação |
| `risk_score` | Probabilidade de defasagem [0-1] | Modelo | Output do classificador |
| `risk_band` | Faixa de risco | Modelo | alto (≥0.7) / médio (0.3-0.7) / baixo (<0.3) |
| `intervention_rate` | Taxa de intervenção | Logs | `count(intervenções) / count(alto_risco)` |
| `time_to_action` | Tempo até ação (dias) | Logs | `intervention_date - score_date` |

---

## 6. Fontes de Dados

| Dado | Fonte | Atualização |
|------|-------|-------------|
| Dados cadastrais (FASE, PEDRA, IDADE) | Sistema escolar | Semestral |
| Avaliações (IAN, notas) | Plataforma avaliações | Bimestral |
| Scores de risco | `inference_store.jsonl` | Real-time |
| Intervenções | `intervention_log.csv` | Contínuo |
| Desfechos | `outcomes_log.csv` | Mensal |

---

## Referências
- Matriz de ação: `docs/action_matrix_and_feedback_loop.md`
- Dashboard spec: `docs/dashboards_spec.md`
