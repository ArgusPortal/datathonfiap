# Data Contract v2

## Schema de Features (Inferência e Treino)

### Features Base do Modelo (13 indicadores educacionais)

| Feature | Tipo | Range | Obrigatório |
|---------|------|-------|-------------|
| `fase_2023` | float | [0, 8] | Sim |
| `iaa_2023` | float | [0, 10] | Sim |
| `ian_2023` | float | [0, 10] | Sim |
| `ida_2023` | float | [0, 10] | Sim |
| `idade_2023` | float | [5, 25] | Sim |
| `ieg_2023` | float | [0, 10] | Sim |
| `instituicao_2023` | object | categorical | Sim |
| `ipp_2023` | float | [0, 10] | Sim |
| `ips_2023` | float | [0, 10] | Sim |
| `ipv_2023` | float | [0, 10] | Sim |
| `genero_2023` | float | [0, 1] | Sim |
| `ano_ingresso_2023` | float | [2016, 2025] | Sim |
| `anos_pm_2023` | float | [0, 10] | Sim |

### Features de Variação Temporal (deltas 2022→2023)

| Feature | Tipo | Range | Obrigatório |
|---------|------|-------|-------------|
| `delta_ian_2022_2023` | float | [-10, 10] | Sim |
| `delta_ida_2022_2023` | float | [-10, 10] | Sim |
| `delta_ieg_2022_2023` | float | [-10, 10] | Sim |
| `delta_iaa_2022_2023` | float | [-10, 10] | Sim |
| `delta_ips_2022_2023` | float | [-10, 10] | Sim |
| `delta_ipv_2022_2023` | float | [-10, 10] | Sim |

### Features de Missing e Agregação

| Feature | Tipo | Range | Obrigatório |
|---------|------|-------|-------------|
| `has_prev_year_data` | float | [0, 1] | Sim |
| `ida_2023_missing` | float | [0, 1] | Sim |
| `ieg_2023_missing` | float | [0, 1] | Sim |
| `iaa_2023_missing` | float | [0, 1] | Sim |
| `ips_2023_missing` | float | [0, 1] | Sim |
| `ipp_2023_missing` | float | [0, 1] | Sim |
| `ipv_2023_missing` | float | [0, 1] | Sim |
| `media_indicadores` | float | [0, 10] | Sim |
| `min_indicador` | float | [0, 10] | Sim |
| `max_indicador` | float | [0, 10] | Sim |
| `std_indicadores` | float | [0, 5] | Sim |
| `range_indicadores` | float | [0, 10] | Sim |
| `fase_x_media` | float | [0, 80] | Sim |

**Total: 34 features**

## Target (apenas treino)

| Campo | Tipo | Valores |
|-------|------|---------|
| `em_risco_2024` | int | 0 (sem risco), 1 (em risco) |

## Regras de Validação

### Inferência
- 34 features obrigatórias conforme schema acima
- Features extras: aceitas (policy configurável via `EXTRA_FEATURE_POLICY`)
- Missing values: preenchidos com mediana do treino (SimpleImputer)
- Tipos: convertidos automaticamente para numérico
- Validação de regras de negócio via `src/business_rules.py`

### Treino
- Mesmas 34 features + target
- Bloqueio temporal: dados do ano t não podem usar target do ano t (vazamento)
- Split: treino em 2023, validação em 2024 (80/20 por aluno)
- Preprocessing: SimpleImputer(median) + OneHotEncoder + StandardScaler

## Campos Proibidos (PII)

Nunca usar em features ou logs:
- `ra`, `nome`, `student_id`, `email`, `telefone`, `endereco`

## Regras de Negócio (Indicadores PEDE)

Validação implementada em `src/business_rules.py`:
- **IAN**: Calculado pela defasagem (10 se D≥0, 5 se -2<D<0, 2.5 se D≤-2)
- **IDA**: Média de Matemática, Português e Inglês
- **INDE**: Ponderação dos indicadores (pesos diferenciados Fase 8 vs demais)
- **Faixas de Pedra**: Quartzo (3-6.1), Ágata (6.1-7.2), Ametista (7.2-8.2), Topázio (8.2-10)

## Compatibilidade

- **v1.2.0**: 34 features conforme lista acima (schema atual)
- **v1.1.0**: 24 features (sem deltas temporais, sem flags de missing completas)
- **v1.0.0**: 13 features base
- Mudança de schema = nova versão major do modelo
