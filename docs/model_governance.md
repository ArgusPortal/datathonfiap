# Model Governance — Risco de Defasagem Escolar

## Objetivo e Escopo

**O que faz:**
- Estima probabilidade de defasagem escolar (risk_score 0-1)
- Classifica alunos em faixas de risco (alto/médio/baixo)
- Suporta priorização de intervenções pedagógicas

**O que NÃO faz:**
- Não substitui avaliação pedagógica individualizada
- Não determina aprovação/reprovação
- Não gera diagnósticos clínicos ou psicológicos

---

## Papéis e Responsabilidades (RACI)

| Papel | Responsável | Atividades |
|-------|-------------|------------|
| **Product Owner do Score** | Coordenação Pedagógica | Decisão de uso, validação de thresholds, aprovação de novas versões |
| **Owner Técnico** | Time de Dados/ML | Pipeline, API, monitoramento, retraining |
| **Data Steward** | Secretaria/TI Escolar | Contrato de dados, qualidade, privacidade |
| **SRE/Operação** | Time de Infra/DevOps | Disponibilidade, incidentes, escalação |

### Matriz RACI Simplificada

| Atividade | PO Score | Owner Técnico | Data Steward | SRE |
|-----------|----------|---------------|--------------|-----|
| Aprovar nova versão | **A** | R | C | I |
| Executar retraining | C | **R/A** | C | I |
| Monitorar drift | I | **R** | I | C |
| Responder incidente | I | C | I | **R/A** |
| Atualizar dados fonte | I | I | **R/A** | I |

*R=Responsible, A=Accountable, C=Consulted, I=Informed*

---

## Versionamento e Rastreabilidade

### Versões Rastreadas
- `model_version`: versão do modelo (ex: v1.1.0)
- `data_version`: hash do dataset de treino
- `features_version`: versão do feature engineering
- `code_version`: git SHA do código
- `config_version`: hash do arquivo de configuração

### Registro por Previsão (Audit Log)
Campos obrigatórios (sem PII):
```
request_id, timestamp, model_version, input_hash, risk_score, risk_band, latency_ms
```
Armazenamento: `monitoring/inference_store.jsonl`

---

## Política de Atualização

### Quando fazer Retraining
- Drift vermelho persistente (>7 dias)
- Performance degradada (recall < 0.65 com labels)
- Mudança estrutural nos dados fonte
- Cadência regular: trimestral (mínimo)

### Quando Congelar
- Período de avaliações oficiais
- Investigação de incidente em andamento
- Aguardando validação de nova versão

### Quando Desativar
- Performance abaixo do aceitável sem recuperação
- Mudança de política/processo que invalida o modelo
- Substituição por nova versão validada

---

## Critérios de Promoção (Champion)

Nova versão só vira champion se:
- [ ] Recall (classe positiva) ≥ 0.70
- [ ] Cobertura de testes ≥ 80%
- [ ] Security scan sem vulnerabilidades críticas
- [ ] Drift status: sem vermelho
- [ ] Validação em shadow mode (≥7 dias)
- [ ] Aprovação do PO Score

---

## Política de Rollback

**Trigger:** degradação de performance, erro crítico, drift severo

**Processo:**
1. SRE aciona rollback via registry (ver `docs/sre_runbook.md`)
2. Owner Técnico investiga causa raiz
3. PO Score comunica stakeholders
4. Post-mortem em até 5 dias úteis

---

## Ritos de Revisão

### Reunião Mensal (1h)
- **Participantes:** PO Score, Owner Técnico, Data Steward
- **Agenda:** ver `docs/templates/monthly_review_agenda.md`

### Revisão Trimestral (2h)
- Análise de impacto (KPIs)
- Decisão de retraining
- Revisão de thresholds
- Planejamento próximo ciclo

---

## Referências
- Registro de versões: `models/registry/`
- Runbook operacional: `docs/ops_playbook.md`
- Model Card: `docs/model_card.md`
- Changelog: `docs/model_changelog.md`
