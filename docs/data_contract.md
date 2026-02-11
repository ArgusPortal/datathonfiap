# Data Contract v1: Modelo de Risco de Defasagem Escolar

> **⚠️ SUPERSEDED — Este documento foi substituído pelo [Data Contract v2](data_contract_v2.md)**
>
> O v1 foi o documento de planejamento inicial criado antes da análise exploratória.
> Após a EDA, todas as especificações foram consolidadas no v2 com as 34 features
> reais, tipos validados, ranges conferidos e regras de qualidade implementadas.
> Este arquivo é mantido apenas como registro histórico da evolução do projeto.

**Projeto**: Datathon FIAP - Passos Mágicos  
**Data**: Janeiro 2026  
**Versão**: 0.1 (MVP) — **Superseded by v2**

---

## 1. Escopo do Dataset e Granularidade

- **Granularidade**: uma linha por estudante por ano (estudante_id, ano)
- **Período**: 2022–2024 (3 anos de dados históricos)
- **Chave composta**: `(estudante_id, ano)`

---

## 2. Chaves e Identificadores

**IDs obrigatórios** (não usar como features):
- `estudante_id`: identificador único do estudante (RA)
- `ano`: ano letivo (2022, 2023, 2024)

**IDs derivados** (construir durante preprocessing):
- `index_temporal`: índice sequencial para ordenação (estudante + ano)

---

## 3. Features Candidatas (por Grupos)

> **Nota**: As features finais foram definidas no [Data Contract v2](data_contract_v2.md).
> Abaixo está o levantamento inicial que guiou a exploração.

### 3.1 Indicadores Acadêmicos (PEDE)
- `iaa_2023`: Índice de Autoavaliação [0-10]
- `ian_2023`: Índice de Adequação ao Nível [0-10]
- `ida_2023`: Índice de Desenvolvimento Acadêmico [0-10]
- `ieg_2023`: Índice de Engajamento [0-10]
- `ipp_2023`: Índice de Performance Pedagógica [0-10]
- `ips_2023`: Índice de Performance Social [0-10]
- `ipv_2023`: Índice de Ponto de Virada [0-10]

### 3.2 Contexto do Estudante
- `fase_2023`: fase do estudante no programa (1–8)
- `idade_2023`: idade do aluno (7–20)
- `genero_2023`: gênero (0/1)
- `instituicao_2023`: instituição de ensino (0–5)
- `ano_ingresso_2023`: ano de ingresso no programa (2016–2023)
- `anos_pm_2023`: tempo no programa Passos Mágicos (1–8)

### 3.3 Features Temporais (deltas 2022→2023)
- `delta_iaa_2022_2023`, `delta_ian_2022_2023`, `delta_ida_2022_2023`
- `delta_ieg_2022_2023`, `delta_ips_2022_2023`, `delta_ipv_2022_2023`
- `has_prev_year_data`: flag indicando se o aluno tem dados de 2022

### 3.4 Features Agregadas (derivadas)
- `media_indicadores`, `min_indicador`, `max_indicador`
- `std_indicadores`, `range_indicadores`
- `fase_x_media`: interação fase × média dos indicadores
- `*_missing`: flags de missing para cada indicador (6 flags)

### 3.5 Target
- `em_risco_2024`: binário (0/1) — 1 se defasagem < 0 (aluno atrasado no ano seguinte)
- Calculado via: `defasagem = fase_efetiva - fase_ideal`

---

## 4. Colunas Proibidas

**IDs e identificadores diretos** (removidos no preprocessing):
- `nome`, `cpf`, `endereco_completo` — dados pessoais (LGPD)
- `turma_id`, `escola_id`, `professor_id` — alta cardinalidade, overfitting

**Variáveis do futuro** (ano t+1):
- Qualquer coluna com sufixo `_2024` exceto o target `em_risco_2024`
- `fase_2024`, `inde_2024`, `ian_2024` — dados do próprio período a prever
- Colunas de status de matrícula no ano de predição

---

## 5. Leakage Watchlist

**Colunas com ALTO RISCO de vazamento** (tratadas no pipeline):

- `fase_2024` / indicadores `_2024`: informação do ano a ser previsto — removidas
- `ponto_virada_2023`: validado como calculado apenas com dados até 2023 — **seguro para uso**
- `inde_2023`: validado como agregação dos indicadores PEDE do ano corrente — **seguro**

**Regra de ouro**: se a coluna só estaria disponível DEPOIS do evento que queremos predizer, NÃO USAR.

**Mitigações implementadas**:
- `src/preprocessing.py` remove colunas proibidas antes do treino
- `src/data_quality.py` valida ausência de colunas futuras no dataset final
- Testes unitários verificam que nenhuma feature `_2024` entra no modelo

---

## 6. Disponibilidade por Etapa

| Feature Group | Final do Ano t (treino) | Momento da Predição (produção) |
|---------------|------------------------|-------------------------------|
| IDs obrigatórios | ✅ Disponível | ✅ Disponível |
| Indicadores PEDE (IAA, IAN, IDA, IEG, IPP, IPS, IPV) | ✅ Disponível | ✅ Disponível |
| Contexto (fase, idade, gênero, instituição) | ✅ Disponível | ✅ Disponível |
| Deltas temporais (2022→2023) | ✅ Disponível | ✅ Disponível |
| Features agregadas (média, std, range) | ✅ Calculadas no pipeline | ✅ Calculadas no pipeline |
| Missing flags | ✅ Geradas no pipeline | ✅ Geradas no pipeline |

**Decisão**: o modelo utiliza dados do **final do ano t** (máxima informação disponível).
A API recebe os indicadores do aluno e calcula features derivadas automaticamente.

---

## 7. Regras de Qualidade Mínimas

**Missing values** (implementado em `src/data_quality.py`):
- Features de ID e target: 0% missing
- Indicadores PEDE: até 40% missing (realidade — 23 colunas têm >30% missing)
  - Estratégia: imputação por mediana + flag `*_missing` para cada indicador
- Features de contexto: até 5% missing

**Ranges e tipos** (validados em runtime pela API):
- `fase_2023`: inteiro [1, 8]
- Indicadores PEDE (`iaa`, `ian`, `ida`, `ieg`, `ipp`, `ips`, `ipv`): float [0.0, 10.0]
- `idade_2023`: inteiro [7, 20]
- `genero_2023`: inteiro {0, 1}
- `instituicao_2023`: inteiro [0, 5]
- `em_risco_2024`: binário {0, 1}, sem nulls

**Checks automatizados** (382 testes, 81.5% cobertura):
- Schema validation: tipos corretos, 34 features obrigatórias
- Nulls check: % missing dentro dos limites
- Range check: validação de bounds no schema Pydantic da API
- Duplicatas: chave composta única
- Leakage check: nenhuma coluna `_2024` no dataset de treino
- PSI drift check: 32 features monitoradas em produção

---

## 8. Pendências Resolvidas

Todas as pendências do planejamento inicial foram resolvidas durante a implementação:

- ✅ **Dicionário de colunas**: mapeado a partir do dataset PEDE fornecido pelo Datathon
- ✅ **Cálculo de INDE/IAN/PEDE**: indicadores extraídos diretamente do dataset (escala 0-10)
- ✅ **Mapeamento temporal**: features utilizam exclusivamente dados até ano t (2023)
- ✅ **Colunas de texto livre**: não utilizadas — todas as features são numéricas
- ✅ **Dados históricos**: 2022 e 2023 disponíveis, deltas calculados para features temporais
- ✅ **Estratégia de imputação**: mediana para numéricos + flag `*_missing` (MAR assumido)
- ✅ **Validação de qualidade**: implementada em `src/data_quality.py` + schema Pydantic na API

Para os detalhes finais de implementação, consulte o [Data Contract v2](data_contract_v2.md).
