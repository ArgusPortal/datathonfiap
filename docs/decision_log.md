# Decision Log: Modelo de Risco de Defasagem Escolar

**Projeto**: Datathon FIAP - Passos Mágicos  
**Data**: Janeiro 2026  
**Versão**: 0.1 (MVP)  
**Status**: Decisões iniciais travadas para Fase 0

---

## D1: Target (Variável Resposta)

**Definição MVP**: variável binária `em_risco` (0/1)
- `em_risco = 1`: estudante com defasagem moderada OU severa no ano t+1
- `em_risco = 0`: estudante sem defasagem OU defasagem leve no ano t+1

**Rationale**:
- Foco em casos que demandam intervenção intensiva (moderada + severa)
- Defasagem leve tratada como "não prioritário" no MVP
- {{Verificar: critérios exatos de classificação leve/moderada/severa no PEDE/IAN}}

**Evolução futura (pós-MVP)**:
- Predição multiclasse (leve/moderada/severa) se houver demanda operacional
- Predição de magnitude da defasagem (regressão do IAN)

---

## D2: Horizonte Temporal

**Escolha MVP**: predição **t → t+1** (usar dados do ano t para predizer risco no ano t+1)

**Rationale**:
- Alinha com ciclo de decisão (matrícula/alocação acontece entre anos letivos)
- Reduz vazamento de informação (não usa variáveis contemporâneas ao target)
- Permite validação temporal realista (treino em 2022-2023, validação em 2024)

**Restrições**:
- Features devem estar disponíveis até o final do ano t
- Não usar informações de desempenho/presença do próprio ano t+1
- {{Confirmar: janela exata de coleta de features no calendário escolar}}

---

## D3: Métrica de Avaliação

**Métrica principal**: **Recall da classe positiva** (em risco)
- Target MVP: Recall ≥ 0.75
- Justifica: custo de falso negativo > custo de falso positivo (não identificar aluno em risco é crítico)

**Métricas secundárias**:
- **PR-AUC**: avaliar trade-off precision/recall independente de threshold
- **Precision @ Recall=0.75**: entender taxa de falsos positivos no ponto de operação
- **F2-Score**: (opcional) balanceia recall e precision com peso maior em recall

**Por que não accuracy**:
- Dataset pode ser desbalanceado (poucos casos em risco)
- Accuracy alta não garante identificação adequada da classe minoritária

---

## D4: População e Recorte

**Escolha MVP**: estudantes em **Fases 0–7** (todas as fases do programa)

**Rationale**:
- Modelo único mais simples de operar inicialmente
- Permite avaliar se padrões de risco são consistentes entre fases
- {{Verificar: distribuição de defasagem por fase — há desequilíbrio crítico?}}

**Mitigação de heterogeneidade**:
- Incluir `fase` como feature (encoding apropriado)
- Análise pós-treino: performance estratificada por fase
- Se performance divergir muito (Δ Recall > 0.15), considerar modelos separados em fases futuras

**Exclusões**:
- Alunos sem dados completos do ano t (missing crítico em >30% das features)
- {{Confirmar: regras de elegibilidade do programa que impactam população}}

---

## Restrições e Colunas Proibidas

**Proibido usar como features**:
- IDs diretos (estudante, turma, escola) → risco de overfitting
- Informações do ano t+1 (vazamento temporal)
- Variáveis derivadas do target (ex: se houver flag "indicador_risco_calculado")
- {{Adicionar: colunas específicas do dicionário após revisão}}

**Privacidade**:
- Não usar nome, CPF, endereço completo, dados familiares sensíveis
- Features socioeconômicas agregadas permitidas (ex: nível de vulnerabilidade categorizado)

---

## Assunções e Riscos

**Assunções**:
- Dados 2022–2024 são representativos do comportamento futuro
- Critério de defasagem (moderada/severa) permanece estável no tempo
- Features disponíveis no momento de predição não mudam estruturalmente
- {{Confirmar: processo de coleta de dados é consistente entre anos}}

**Riscos**:
- **Data drift**: características da população podem mudar (ex: pós-pandemia)
- **Label noise**: classificação de defasagem pode ter inconsistências
- **Selection bias**: alunos que permanecem no programa podem diferir dos que saem
- **Desbalanceamento**: classe minoritária pode ter poucos exemplos para treino
- **Multicolinearidade**: features do PEDE podem ter alta correlação entre si
- {{Adicionar após EDA: riscos específicos identificados nos dados}}

---

## Impacto no Endpoint `/predict`

- Input: JSON com features do estudante no ano t (schema definido no data contract)
- Output: `{"score": float, "classe_predita": 0/1, "versao_modelo": string}`
- Threshold padrão: 0.5 (ajustável por configuração)
- Latência target: <500ms (modelo deve ser suficientemente leve)

---

## Estratégia de Validação Inicial

- **Split temporal**: treino em 2022–2023, validação em 2024
- Não usar random split (violaria premissa t→t+1)
- Validação cruzada temporal se múltiplos anos (walk-forward)
- Holdout final: últimos 20% dos dados de 2024 para teste
