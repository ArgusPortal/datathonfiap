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
- **Baseline:** 2022–2024 (pré-adoção do modelo)
- **Pós-adoção:** a partir da implantação em produção (previsto para 2026)

### Métricas Baseline por Segmento

| Segmento | Taxa Risco (em_risco_2024) | IAN Médio | N Alunos |
|----------|---------------------------|-----------|----------|
| **Geral** | 40.3% | 7.405 | 765 |
| Alfa + Fase 1-3 | 46.5% | 7.044 | 559 |
| Fase 4-6 | 37.8% | 7.579 | 127 |
| Fase 7-8 | 0.0% | 9.684 | 79 |
| ALFA | 75.9% | 7.328 | 174 |
| FASE 1 | 44.2% | 6.196 | 138 |
| FASE 2 | 16.3% | 7.092 | 153 |
| FASE 3 | 44.7% | 7.686 | 94 |
| FASE 4 | 37.3% | 7.948 | 67 |
| FASE 5 | 48.8% | 7.326 | 43 |
| FASE 6 | 11.8% | 6.765 | 17 |
| FASE 7 | 0.0% | 8.750 | 20 |
| FASE 8 | 0.0% | 10.000 | 59 |

*Dados computados a partir de `data/processed/modeling_dataset.parquet` (765 alunos com dados 2023→2024)*

> **Nota**: Pedra (Topázio, Ametista, Ágata, Quartzo) não está disponível no dataset de modelagem.
> Os recortes por Pedra poderão ser adicionados quando o campo for incluído no pipeline de features.

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
