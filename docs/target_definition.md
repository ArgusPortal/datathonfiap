# Target Definition: Risco de Defasagem Escolar

**Projeto**: Datathon FIAP - Passos Mágicos  
**Fase**: 1 - Data Product v1  
**Data**: Janeiro 2026

---

## Target Escolhido (MVP)

**Nome**: `em_risco` (binário: 0 ou 1)

## Regra de Cálculo

```
Defasagem = Fase_Efetiva - Fase_Ideal

Se Defasagem < 0:
    em_risco = 1  (aluno em defasagem/atrasado)
Senão:
    em_risco = 0  (aluno em fase adequada ou avançado)
```

**Observações**:
- `Defasagem < 0`: aluno está ABAIXO da fase ideal para sua idade
- `Defasagem = 0`: aluno está na fase adequada
- `Defasagem > 0`: aluno está ACIMA da fase ideal (avançado)

## Tratamento de Casos Especiais

| Situação | Tratamento |
|----------|------------|
| Defasagem > 0 (avançado) | `em_risco = 0` (não considerado em risco) |
| Defasagem = NaN/missing | Excluir do dataset de modelagem |
| Fase Ideal = NaN | Excluir do dataset de modelagem |
| Fase = NaN | Excluir do dataset de modelagem |

## Distribuição Observada (PEDE 2024)

| Defasagem | Count | Target |
|-----------|-------|--------|
| -3 | 3 | em_risco=1 |
| -2 | 90 | em_risco=1 |
| -1 | 441 | em_risco=1 |
| 0 | 485 | em_risco=0 |
| +1 | 119 | em_risco=0 |
| +2 | 16 | em_risco=0 |
| +3 | 2 | em_risco=0 |

**Distribuição do target**: ~46% em risco (534/1156), ~54% adequado/avançado (622/1156)

## Justificativa

- **Simplicidade**: binário é mais fácil de comunicar e usar operacionalmente
- **Acionabilidade**: qualquer defasagem negativa merece atenção preventiva
- **Balanceamento**: classes relativamente balanceadas (~46% vs ~54%)
- **Alinhamento**: consistente com objetivo de identificar alunos que precisam intervenção
- **Extensibilidade**: pode evoluir para multiclasse (leve/moderada/severa) em fases futuras

## Alternativa (Multiclasse) - NÃO IMPLEMENTADA NO MVP

```
Se Defasagem >= 0:
    classe = "adequado_avancado"
Se Defasagem == -1:
    classe = "defasagem_leve"
Se Defasagem <= -2:
    classe = "defasagem_severa"
```

---

## Implementação

Função em `src/make_dataset.py`:
```python
def compute_target(defasagem: pd.Series) -> pd.Series:
    """Calcula target binário a partir da defasagem."""
    return (defasagem < 0).astype(int)
```
