# Product Brief: Modelo de Risco de Defasagem Escolar

**Projeto**: Datathon FIAP - Passos Mágicos  
**Data**: Janeiro 2026  
**Versão**: 0.1 (MVP)

## Contexto e Objetivo

- Predizer risco de defasagem escolar (moderada + severa) para estudantes da Passos Mágicos usando dados históricos 2022–2024
- Permitir intervenção preventiva antes da defasagem se consolidar
- Priorizar identificação correta de casos em risco (minimizar falsos negativos)

## Quem Usa e Qual Ação

- **Time pedagógico/coordenação**: consome score no momento de decisões de matrícula e alocação de recursos
- **Ação disparada**: priorização para programas de reforço, mentorias intensivas, acompanhamento familiar
- Score alto (>0.7) → aluno entra em lista de prioridade para intervenções preventivas

## Momento de Uso no Funil

{{TODO: confirmar etapas exatas do fluxo inscrição→matrícula→acompanhamento}}

- Aplicação primária: **pós-inscrição, pré-matrícula definitiva** (usar dados do ano t para predizer risco em t+1)
- Permite ajustar alocação de vagas em programas especiais antes do início do ano letivo
- {{Verificar se há momento intermediário de reavaliação durante o ano}}

## Preferência de Erro e Métrica

- **Custo de FN > custo de FP**: não identificar aluno em risco é mais grave que falso alarme
- **Métrica principal**: Recall da classe positiva (em risco) ≥ 0.75 no MVP
- **Métrica secundária**: PR-AUC para avaliar trade-off precision/recall
- Threshold ajustável operacionalmente conforme capacidade de intervenção

## Critérios de Sucesso MVP

- Modelo treinável com dados 2022–2024 sem vazamento de informação
- API `/predict` retorna score de risco [0,1] com latência <500ms
- Recall ≥ 0.75 em conjunto de validação (split temporal t→t+1)
- Data contract e watchlist de vazamento documentados
- Testes automatizados (pytest) cobrindo pipeline e API
- Repo executável por novo dev em <15min

## Pendências de Produto (resolver nas próximas fases)

{{TODO: confirmar capacidade operacional de intervenção (quantos alunos por ciclo)}}
{{TODO: validar momento exato de coleta de features (quais dados já existem na inscrição)}}
{{TODO: definir plano de monitoramento pós-deploy (drift, performance)}}
