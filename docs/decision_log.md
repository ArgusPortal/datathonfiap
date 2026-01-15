# Decision Log: Modelo de Risco de Defasagem Escolar

**Projeto**: Datathon FIAP - Passos Mágicos  
**Data**: Janeiro 2026  
**Versão**: 0.2 (Fase 1 completa)  
**Status**: Data Product v1 pronto

---

## D1: Target (Variável Resposta)

**Definição MVP**: variável binária `em_risco` (0/1)
- `em_risco = 1`: estudante com Defasagem < 0 no ano t+1
- `em_risco = 0`: estudante com Defasagem ≥ 0 no ano t+1

**Implementação (Fase 1)**:
```python
em_risco = (defasagem < 0).astype(int)
```

**Distribuição no dataset de modelagem (2023→2024)**:
- em_risco=1: 308 (40.3%)
- em_risco=0: 457 (59.7%)
- Total: 765 alunos

**Rationale**:
- Defasagem negativa indica aluno atrás da fase ideal
- Distribuição relativamente balanceada (~40/60), bom para modelagem

---

## D2: Horizonte Temporal

**Escolha MVP**: predição **t → t+1** (features 2023 → label 2024)

**Implementação (Fase 1)**:
- Features extraídas de PEDE2023
- Labels extraídos de PEDE2024 (Defasagem → em_risco)
- Join por RA: 765 alunos com match

**Restrições implementadas**:
- BLOCKED_COLUMNS: defasagem, ponto_virada, pedra, destaque_*, rec_*
- Essas colunas são resultado do ano t+1 e causariam leakage

---

## D3: Métrica de Avaliação

**Métrica principal**: **Recall da classe positiva** (em risco)
- Target MVP: Recall ≥ 0.75
- Justifica: custo de falso negativo > custo de falso positivo

**Protocolo de validação** (docs/evaluation_protocol.md):
- Treino: features 2022+2023 → labels 2024
- Teste (holdout): split por RA, 20% dos alunos
- Threshold: ajustar para maximizar F2 ou atingir Recall ≥ 0.75

---

## D4: População e Recorte

**Dataset de modelagem (Fase 1)**:
- 765 alunos (RAs com dados em 2023 E 2024)
- 10 features disponíveis após anti-leakage
- Features: indicadores INDE, IAN, IDA, IEG, IAA, IPS, IPP, IPV, IPM + fase

**Exclusões**:
- Alunos sem RA em 2023 ou 2024
- Colunas com >30% missing (warning, não bloqueante)

---

## D5: Features Disponíveis (NOVO - Fase 1)

**ALLOWED_FEATURE_COLUMNS**:
- Identificação: ra, nome, instituicao, idade, genero
- Fase/Tempo: fase, anos_pm, bolsista
- Indicadores: inde, ian, ida, ieg, iaa, ips, ipp, ipv, ipm
- Nutricional: indicador_nutricional

**BLOCKED_COLUMNS** (causam leakage):
- defasagem, fase_ideal
- ponto_virada, pedra
- destaque_inde, destaque_ida, destaque_ieg
- rec_ava, rec_inde

---

## Restrições e Colunas Proibidas

**Proibido usar como features**:
- IDs diretos (estudante, turma, escola) → risco de overfitting
- Informações do ano t+1 (vazamento temporal)
- Colunas listadas em BLOCKED_COLUMNS

**Verificação automática**:
- `DataQualityChecker.check_leakage()` valida antes de salvar
- Pipeline falha se detectar leakage

---

## Assunções e Riscos

**Assunções validadas (Fase 1)**:
- ✅ Dados 2022–2024 disponíveis em PEDE2024.xlsx
- ✅ Colunas normalizáveis entre anos (com tratamento de tipos mistos)
- ✅ RA é chave única por ano (sem duplicatas)

**Riscos identificados**:
- Missing values alto em algumas colunas (23 colunas >30% em 2023)
- Tipos de dados inconsistentes entre anos (tratados com conversão automática)
- Apenas 765 alunos no dataset final (pode limitar poder estatístico)

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
