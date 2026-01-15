# Data Contract v2

## Schema de Features (Inferência e Treino)

### Features do Modelo (13 obrigatórias)

| Feature | Tipo | Range | Obrigatório |
|---------|------|-------|-------------|
| `fase_2023` | float/int | [0, 8] | Sim |
| `iaa_2023` | float | [0, 10] | Sim |
| `ian_2023` | float | [0, 10] | Sim |
| `ida_2023` | float | [0, 10] | Sim |
| `idade_2023` | float/int | [5, 25] | Sim |
| `ieg_2023` | float | [0, 10] | Sim |
| `instituicao_2023` | int/str | categorical | Sim |
| `ipp_2023` | float | [0, 10] | Sim |
| `ips_2023` | float | [0, 10] | Sim |
| `ipv_2023` | float | [0, 10] | Sim |
| `media_indicadores` | float | [0, 10] | Sim |
| `min_indicador` | float | [0, 10] | Sim |
| `std_indicadores` | float | [0, 5] | Sim |

### Features Opcionais (aceitas mas não usadas pelo modelo)

| Feature | Tipo | Range | Nota |
|---------|------|-------|------|
| `max_indicador` | float | [0, 10] | Calculado mas não usado |
| `range_indicadores` | float | [0, 10] | Calculado mas não usado |

## Target (apenas treino)

| Campo | Tipo | Valores |
|-------|------|---------|
| `em_risco_2024` | int | 0 (sem risco), 1 (em risco) |

## Regras de Validação

### Inferência
- 13 features obrigatórias
- Features extras: aceitas (policy configurável via `EXTRA_FEATURE_POLICY`)
- Missing values: preenchidos com mediana do treino
- Tipos: convertidos automaticamente para numérico

### Treino
- Mesmas 13 features + target
- Bloqueio temporal: dados do ano t não podem usar target do ano t (vazamento)
- Split: treino em 2023, validação em 2024

## Campos Proibidos (PII)

Nunca usar em features ou logs:
- `ra`, `nome`, `student_id`, `email`, `telefone`, `endereco`

## Compatibilidade

- **v1.x**: 13 features conforme lista acima
- Mudança de schema = nova versão major do modelo
