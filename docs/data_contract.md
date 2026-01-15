# Data Contract: Modelo de Risco de Defasagem Escolar

**Projeto**: Datathon FIAP - Passos Mágicos  
**Data**: Janeiro 2026  
**Versão**: 0.1 (MVP)

---

## 1. Escopo do Dataset e Granularidade

- **Granularidade**: uma linha por estudante por ano (estudante_id, ano)
- **Período**: 2022–2024 (3 anos de dados históricos)
- **Chave composta**: `(estudante_id, ano)`

---

## 2. Chaves e Identificadores

**IDs obrigatórios** (não usar como features):
- `estudante_id`: identificador único do estudante
- `ano`: ano letivo (2022, 2023, 2024)
- {{VERIFICAR: `turma_id`, `escola_id` se aplicável}}

**IDs derivados** (construir durante preprocessing):
- `index_temporal`: índice sequencial para ordenação (estudante + ano)

---

## 3. Features Candidatas (por Grupos)

### 3.1 Indicadores Acadêmicos (PEDE/IAN)
{{COLUNAS_EXEMPLO - substituir após análise do dicionário}}:
- `inde_ano_t`: Índice de Desenvolvimento Educacional do ano t
- `ian_ano_t`: Índice de Adequação de Nível do ano t
- `ponto_virada_ano_t`: indicador de ponto de virada (escala {{especificar}})
- `nota_lingua_portuguesa_t`: desempenho em português
- `nota_matematica_t`: desempenho em matemática
- {{ADICIONAR: outras métricas acadêmicas disponíveis}}

### 3.2 Engajamento e Presença
{{COLUNAS_EXEMPLO}}:
- `taxa_presenca_ano_t`: % de presença no ano t
- `numero_faltas_ano_t`: total de faltas
- `participacao_atividades_extras_t`: flag ou contagem
- {{ADICIONAR: métricas de engajamento familiar, eventos participados}}

### 3.3 Contexto do Estudante
{{COLUNAS_EXEMPLO}}:
- `fase_programa`: fase do estudante no programa (0–7)
- `tempo_no_programa`: anos desde ingresso
- `nivel_vulnerabilidade`: categorizado (baixo/médio/alto) {{confirmar escala}}
- {{ADICIONAR: variáveis socioeconômicas disponíveis}}

### 3.4 Histórico Longitudinal
{{COLUNAS_EXEMPLO - construir via feature engineering}}:
- `delta_inde_t_vs_t1`: variação do INDE entre anos
- `delta_ian_t_vs_t1`: variação do IAN entre anos
- `tendencia_notas`: slope das notas últimos N anos
- {{ADICIONAR: outras features temporais agregadas}}

### 3.5 Target
- `em_risco_t_mais_1`: binário (0/1) — defasagem moderada OU severa no ano t+1
- {{VERIFICAR: como é codificada a defasagem no dataset original (flag, categoria, score?)}}

---

## 4. Colunas Proibidas

**IDs e identificadores diretos**:
- `estudante_id`, `nome`, `cpf`, `endereco_completo`
- `turma_id`, `escola_id`, `professor_id` (risco de overfitting se cardinalidade alta)

**Informações sensíveis** (se presentes):
- Dados familiares identificáveis
- Histórico médico/psicológico não agregado

**Variáveis do futuro** (ano t+1):
- Qualquer coluna que contenha `_t_mais_1` ou `_t+1` exceto o target
- {{ADICIONAR: listar explicitamente após revisar dicionário}}

---

## 5. Leakage Watchlist

**Colunas com ALTO RISCO de vazamento** (revisar antes de usar):

- `fase_efetiva_t_mais_1` vs `fase_ideal_t_mais_1`: se derivam da defasagem em t+1, NÃO USAR
- `indicador_risco_pre_calculado`: se existe, pode ser derivado do target
- `status_matricula_t_mais_1`: informação futura
- `notas_parciais_t_mais_1`: dados do próprio ano que queremos predizer
- {{ADICIONAR: qualquer coluna com sufixo do ano futuro após análise}}

**Regra de ouro**: se a coluna só estaria disponível DEPOIS do evento que queremos predizer, NÃO USAR.

**Colunas SUSPEITAS** (validar origem):
- `ponto_virada`: confirmar se é calculado com dados apenas até ano t
- `inde_ajustado`: verificar se usa informações futuras no cálculo
- {{ADICIONAR: variáveis derivadas encontradas no dicionário}}

---

## 6. Disponibilidade por Etapa (Inscrição → Matrícula)

| Feature Group | Momento Inscrição | Momento Matrícula | Momento Avaliação Final (ano t) |
|---------------|-------------------|-------------------|---------------------------------|
| IDs obrigatórios | ✅ Existe | ✅ Existe | ✅ Existe |
| Indicadores acadêmicos (INDE, IAN) | {{INCERTO}} | {{INCERTO}} | ✅ Existe |
| Engajamento/presença ano t | ❌ Não existe | {{PARCIAL?}} | ✅ Existe |
| Contexto do estudante | {{PARCIAL}} | ✅ Existe | ✅ Existe |
| Histórico longitudinal | {{INCERTO}} | {{INCERTO}} | ✅ Existe |

**AÇÕES**:
- {{Confirmar com stakeholders: quais dados estão disponíveis em cada etapa}}
- {{Decidir: modelo único (usar apenas features disponíveis na inscrição) OU modelos múltiplos por etapa}}
- MVP usa dados do **final do ano t** (máxima informação disponível)

---

## 7. Regras de Qualidade Mínimas

**Missing values**:
- Features críticas (IDs, ano, target): 0% missing permitido
- Features acadêmicas: máximo 20% missing (imputar mediana/moda ou criar flag)
- Features de engajamento: máximo 30% missing (pode indicar não-participação)

**Ranges e tipos**:
- `ano`: inteiro, valores válidos [2022, 2023, 2024]
- `fase_programa`: inteiro, valores válidos [0, 1, 2, 3, 4, 5, 6, 7]
- `taxa_presenca_ano_t`: float [0.0, 1.0] ou int [0, 100]
- `inde_ano_t`, `ian_ano_t`: {{ESPECIFICAR ranges válidos após consultar documentação PEDE}}
- `em_risco_t_mais_1`: binário {0, 1}, sem nulls

**Consistência temporal**:
- Não existir registro do ano t+1 antes de existir registro do ano t para mesmo estudante
- Delta de tempo entre features longitudinais deve ser válido (ex: `tempo_no_programa` monotonicamente crescente)

**Checks automatizáveis (para pytest)**:
- Schema validation: tipos corretos, colunas obrigatórias presentes
- Nulls check: % missing dentro dos limites por coluna
- Range check: valores dentro de limites esperados
- Duplicatas: chave `(estudante_id, ano)` única
- Temporal consistency: ordenação correta de anos por estudante
- Leakage check: nenhuma coluna da watchlist presente no dataset de treino

---

## 8. Pendências de Dados (resolver antes de treino)

{{TODO: colar dicionário completo de colunas fornecido pelo Datathon}}
{{TODO: confirmar cálculo exato de INDE, IAN, PEDE (fórmulas e inputs)}}
{{TODO: mapear quais colunas derivam de qual momento do funil (inscrição/matrícula/avaliação)}}
{{TODO: validar se há colunas de texto livre que precisam NLP}}
{{TODO: conferir se existem dados de anos anteriores a 2022 para construir histórico longitudinal}}
{{TODO: definir estratégia de imputação por tipo de missing (MCAR vs MAR vs MNAR)}}
{{TODO: estabelecer processo de validação de qualidade dos dados na entrada (schema + testes)}}
