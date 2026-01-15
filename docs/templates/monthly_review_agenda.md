# Agenda — Reunião Mensal de Revisão do Modelo

**Duração:** 1 hora  
**Participantes:** PO Score, Owner Técnico, Data Steward  
**Frequência:** Primeira semana de cada mês

---

## Pauta (60 min)

### 1. Saúde Operacional (10 min)
- [ ] Disponibilidade do mês (uptime %)
- [ ] Taxa de erro média
- [ ] Latência p95 média
- [ ] Incidentes ocorridos e status

### 2. Drift e Qualidade (10 min)
- [ ] Status do drift report (verde/amarelo/vermelho)
- [ ] Features com maior drift
- [ ] Decisão: investigar / ignorar / retraining

### 3. KPIs de Processo (15 min)
- [ ] Cobertura de scoring (% alunos)
- [ ] Taxa de intervenção (% alto risco com ação)
- [ ] Tempo médio até ação
- [ ] Aderência do time (uso efetivo)

### 4. KPIs de Impacto (15 min)
- [ ] Taxa de defasagem atual vs baseline
- [ ] IAN médio atual vs baseline
- [ ] Análise por segmento (fase, pedra)
- [ ] Tendências observadas

### 5. Ações e Próximos Passos (10 min)
- [ ] Decisões tomadas (registrar)
- [ ] Ações pendentes e responsáveis
- [ ] Agenda da próxima reunião

---

## Preparação Prévia

**Owner Técnico deve trazer:**
- Relatório de drift atualizado
- Métricas de operação do mês
- Status de eventuais retrainings

**PO Score deve trazer:**
- Feedback qualitativo do time
- Dados de intervenções realizadas
- Questões de negócio pendentes

**Data Steward deve trazer:**
- Status da qualidade dos dados
- Mudanças em schemas ou fontes
- Issues de dados reportados

---

## Template de Registro

```
Data: ____/____/____
Participantes: _______________

Decisões:
1. 
2. 

Ações:
| Ação | Responsável | Prazo |
|------|-------------|-------|
|      |             |       |

Próxima reunião: ____/____/____
```
