# Matriz de Ação e Feedback Loop

## 1. Faixas de Risco

| Faixa | risk_score | Descrição |
|-------|------------|-----------|
| **Alto** | ≥ 0.70 | Risco elevado, ação prioritária |
| **Médio** | 0.30 - 0.69 | Risco moderado, monitorar |
| **Baixo** | < 0.30 | Risco baixo, acompanhamento padrão |

> **Nota:** Thresholds calibrados com base no threshold operacional do modelo (0.040221 para classificação binária). Faixas de gestão acima são para priorização de intervenção.

---

## 2. Matriz de Decisão e Ação

| Faixa | Decisão | Intervenção Recomendada | SLA | Responsável |
|-------|---------|-------------------------|-----|-------------|
| **Alto** | Ação imediata | Tutoria reforçada + Plano individualizado | 7 dias | Tutor + Coord. Pedagógica |
| **Alto** (reincidente) | Escalação | Acompanhamento psicopedagógico + Família | 5 dias | Coord. + Psicopedagogo |
| **Médio** | Monitoramento ativo | Tutoria padrão + Checkin semanal | 14 dias | Tutor |
| **Médio** (tendência alta) | Prevenção | Reforço em disciplinas críticas | 10 dias | Tutor |
| **Baixo** | Acompanhamento padrão | Rotina normal | - | Professor |

### Intervenções Disponíveis
1. **Tutoria reforçada** — sessões extras com tutor
2. **Plano individualizado** — metas e atividades personalizadas
3. **Acompanhamento psicopedagógico** — avaliação especializada
4. **Comunicação com família** — reunião ou contato
5. **Reforço disciplinar** — foco em matérias específicas

---

## 3. Registro de Intervenção

### Campos Obrigatórios

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `student_key` | string | Hash anonimizado do aluno |
| `score_date` | date | Data do score que motivou ação |
| `risk_score` | float | Score no momento |
| `risk_band` | string | alto/médio/baixo |
| `intervention_type` | string | Tipo de intervenção |
| `intervention_date` | date | Data da ação |
| `responsible` | string | Papel do responsável |
| `status` | string | planejada/em_andamento/concluída/cancelada |
| `notes` | string | Observações (sem PII) |

**Template:** `docs/templates/intervention_log_template.csv`

---

## 4. Registro de Desfecho

### Campos Obrigatórios

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `student_key` | string | Hash anonimizado (mesmo do intervention) |
| `intervention_id` | string | ID da intervenção relacionada |
| `outcome_date` | date | Data da medição de desfecho |
| `outcome_type` | string | Tipo: IAN/DEFASAGEM/NOTA/OUTRO |
| `outcome_value` | float | Valor medido |
| `outcome_delta` | float | Variação vs. baseline do aluno |
| `outcome_category` | string | melhora/estável/piora |
| `period` | string | Período de referência (bimestre) |

**Template:** `docs/templates/outcomes_log_template.csv`

---

## 5. Feedback Loop — Score → Ação → Desfecho → Retraining

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   SCORE     │────▶│    AÇÃO     │────▶│  DESFECHO   │────▶│  RETRAINING │
│ risk_score  │     │ intervenção │     │  IAN/nota   │     │ novo modelo │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
      │                                        │                    │
      │                                        ▼                    │
      │                              ┌─────────────────┐            │
      └─────────────────────────────▶│  outcomes_store │◀───────────┘
                                     └─────────────────┘
```

### Processo de Ingestão de Labels

1. **Coleta:** Desfechos registrados em `outcomes_log.csv`
2. **Periodicidade:** Consolidação mensal
3. **Validação:**
   - student_key existe no histórico de scores
   - outcome_date > score_date
   - outcome_value dentro de range válido
4. **Transformação:** Criar label binário (melhora vs. não-melhora)
5. **Armazenamento:** `data/labels/outcomes_YYYYMM.csv`
6. **Trigger de retraining:** Se >500 novos labels ou trimestral

### Checks de Qualidade do Feedback

| Check | Critério | Ação se falhar |
|-------|----------|----------------|
| Cobertura | ≥30% dos alto-risco têm desfecho | Reforçar registro |
| Latência | outcome_date - intervention_date < 90 dias | Alertar responsáveis |
| Distribuição | Classes balanceadas (20-80%) | Investigar viés |
| Consistência | Sem duplicatas por student_key+period | Deduplicar |

---

## 6. Fluxo de Uso

### Coordenação Pedagógica (semanal)
1. Acessar lista de alunos alto risco
2. Verificar status das intervenções pendentes
3. Atribuir novas ações conforme matriz
4. Registrar em `intervention_log.csv`

### Tutores (contínuo)
1. Receber alunos designados
2. Executar intervenção
3. Atualizar status no log
4. Ao fim do bimestre: registrar desfecho

### Owner Técnico (mensal)
1. Consolidar outcomes
2. Validar qualidade
3. Avaliar necessidade de retraining
4. Atualizar métricas de feedback loop

---

## Referências
- Templates: `docs/templates/`
- Governance: `docs/model_governance.md`
- KPIs: `docs/kpis_and_baseline.md`
