# Cenários de Produção — Modelo de Risco de Defasagem

> Como o sistema se comporta em situações reais de operação.

---

## Cenário 1: Nova Coorte de Alunos (Início do Ano Letivo)

### Situação
É início de 2027. A Passos Mágicos finalizou as avaliações PEDE de 2026 e quer identificar quais alunos estão em risco de defasagem em 2027.

### Fluxo

1. **Coleta**: equipe exporta dados do PEDE 2026 (IAA, IAN, IDA, IEG, IPP, IPS, IPV) + cadastro (fase, idade, gênero, instituição)
2. **Preparação**: script `src/make_dataset.py` normaliza colunas, calcula deltas 2025→2026, gera flags de missing
3. **Scoring em batch**: chamada ao endpoint `/predict` com lote de alunos
4. **Resultado**: cada aluno recebe `risk_score` [0,1] e `risk_label` (0/1 com threshold 0.35)
5. **Ação**: coordenação pedagógica prioriza intervenções para alunos com `risk_score ≥ 0.35`

### Pontos de Atenção
- Alunos novos (sem dados de 2025) terão `has_prev_year_data = 0` e deltas = NaN → modelo lida com isso via flags de missing
- Se o perfil da coorte diferir muito do treino (ex: criação de novas turmas), o drift monitor emitirá alertas

---

## Cenário 2: Detecção de Drift em Produção

### Situação
Após 3 meses de uso, o dashboard de monitoramento mostra um alerta amarelo (PSI > 0.1) na feature `ieg_2023`.

### Fluxo

1. **Alerta**: endpoint `/drift/report` retorna PSI = 0.15 para `ieg_2023` (status YELLOW)
2. **Investigação**: equipe verifica se houve mudança na avaliação de engajamento (novo instrumento? novo avaliador?)
3. **Decisão**:
   - Se mudança é metodológica → **recalibrar** feature ou retreinar modelo
   - Se mudança é real da população → monitorar por mais 1 mês antes de agir
   - Se PSI > 0.2 (RED) → **retreinar** imediatamente com dados recentes
4. **Ação de retrain**: executar `python -m src.retrain` que treina challenger, compara com champion via métricas no test set, e promove automaticamente se superior

### Thresholds de Drift (PSI)
| PSI | Status | Ação |
|-----|--------|------|
| < 0.1 | 🟢 GREEN | Nenhuma ação |
| 0.1–0.2 | 🟡 YELLOW | Investigar causa raiz |
| ≥ 0.2 | 🔴 RED | Retreinar modelo |

---

## Cenário 3: Chegada de Labels (Feedback Loop)

### Situação
Passou-se 1 ano desde o scoring. Os resultados reais de 2027 estão disponíveis — sabemos quais alunos de fato ficaram defasados.

### Fluxo

1. **Coleta de labels**: equipe registra quais alunos tiveram defasagem em 2027 (`em_risco_2027 = 0/1`)
2. **Avaliação retrospectiva**: script `src/evaluate.py` compara predições de 2026 com labels reais de 2027
3. **Métricas de produção**:
   - Recall real ≥ 0.75? → modelo performou como esperado
   - Recall real < 0.75? → investigar degradação
4. **Decisão de retrain**:
   - Se métricas mantidas → manter modelo atual, atualizar baseline
   - Se métricas degradaram → retreinar com dados 2024-2026 → 2027

### Métricas a Comparar
| Métrica | Treino (2023→2024) | Produção (2026→2027) | Decisão |
|---------|-------------------|---------------------|---------|
| Recall | 93.5% | ≥ 75% → OK | Manter |
| Recall | 93.5% | < 75% → Degradou | Retreinar |
| Precision | 69.9% | ≥ 50% → OK | Manter |
| F2 | 0.876 | ≥ 0.70 → OK | Manter |

---

## Cenário 4: Ciclo Completo de Retraining

### Situação
O drift monitor detectou RED em 3+ features ou as labels reais mostraram recall < 75%. É necessário retreinar.

### Fluxo

1. **Preparação de dados**: combinar dados históricos (2022-2026) + novos labels (2027)
2. **Retrain**:
   ```bash
   python -m src.retrain \
     --data data/processed/modeling_dataset_2027.parquet \
     --registry models/registry
   ```
3. **Comparação champion vs challenger**:
   - Se challenger supera champion em Recall E F2 no test set → promover
   - Se não → manter champion, registrar challenger para análise
4. **Promoção**:
   ```bash
   python -m src.registry promote --version v1.2.0
   ```
5. **Atualização de baseline**:
   ```bash
   python -m monitoring.build_baseline --model_version v1.2.0
   ```
6. **Deploy**: rebuild do container Docker com novos artefatos

### Checklist de Retrain
- [ ] Dados de treino sem leakage (sem features do ano de predição)
- [ ] Split temporal preservado (treino em anos anteriores, teste no mais recente)
- [ ] Métricas do challenger ≥ métricas do champion
- [ ] Baseline de monitoramento reconstruído
- [ ] Fairness analysis recomputado para nova versão
- [ ] Model card atualizado com nova versão
- [ ] Testes automatizados passando (382+ testes)
- [ ] Container Docker reconstruído e testado

---

## Cenário 5: Rollback de Emergência

### Situação
Após promoção de uma nova versão, relatórios indicam que o modelo está gerando scores inconsistentes (ex: todos os alunos com score > 0.9).

### Fluxo

1. **Detecção**: equipe pedagógica reporta anomalia OU drift monitor detecta shift na distribuição de scores
2. **Diagnóstico rápido**: verificar `/api/metrics` — se `predictions_positive / predictions_total > 95%`, algo está errado
3. **Rollback**:
   ```bash
   python -m src.registry rollback --version v1.1.0 --reason "Score distribution anomaly"
   ```
4. **Atualizar config**: `app/config.py` aponta para artefatos da versão anterior
5. **Redeploy**: rebuild do container
6. **Post-mortem**: investigar causa raiz (bug no preprocessing? dados corrompidos? feature engineering incorreta?)

---

## Resumo: Política de Retraining

| Trigger | Ação | Frequência |
|---------|------|------------|
| Calendario | Retrain completo | Semestral (fev/ago) |
| Drift PSI ≥ 0.2 em ≥ 3 features | Retrain urgente | Ad hoc |
| Labels reais com recall < 75% | Retrain + investigação | Anual |
| Mudança metodológica no PEDE | Retrain + recalibração | Ad hoc |
| Novo drift (PSI 0.1–0.2) | Monitorar 30 dias | Contínuo |

---

## Referências

- Runbook de operação: [`docs/ops_runbook_v2.md`](ops_runbook_v2.md)
- Política de retrain: [`docs/retraining_policy.md`](retraining_policy.md)
- Monitoramento: [`docs/monitoring_runbook.md`](monitoring_runbook.md)
- Model card: [`docs/model_card.md`](model_card.md)
