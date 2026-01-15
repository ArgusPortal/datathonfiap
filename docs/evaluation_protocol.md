# Evaluation Protocol: Validação Temporal

**Projeto**: Datathon FIAP - Passos Mágicos  
**Fase**: 1 - Data Product v1  
**Data**: Janeiro 2026

---

## Split Temporal

| Dataset | Features | Label | Uso |
|---------|----------|-------|-----|
| Treino | 2022 + 2023 | Defasagem 2024 | Treino do modelo |
| Teste (Holdout) | 2023 | Defasagem 2024 | Avaliação final única |

**Nota**: Não usar random split. A natureza temporal do problema exige validação que respeite a ordem cronológica.

## Métricas de Avaliação

### Métrica Principal
**Recall (classe positiva, em_risco=1)**
- Target MVP: Recall ≥ 0.75
- Justificativa: custo de não identificar aluno em risco > custo de falso alarme

### Métricas Secundárias
- **PR-AUC** (Precision-Recall Area Under Curve)
  - Mais informativa que ROC-AUC em classes desbalanceadas
- **Precision @ Recall=0.75**
  - Entender quantos falsos positivos no ponto de operação
- **F2-Score**
  - Balanceia recall e precision com peso 2x em recall

## Seleção de Threshold

1. **Default**: threshold = 0.5
2. **Operacional**: ajustar para maximizar Recall respeitando Precision mínima
3. **Método**:
   - Gerar curva Precision-Recall no conjunto de validação
   - Escolher threshold que maximize F2 ou atinja Recall ≥ 0.75
   - Aplicar threshold escolhido no teste final

## Regras de Validação

### ⚠️ NÃO TUNAR NO TESTE

O conjunto de teste (holdout) deve ser usado **apenas uma vez** para avaliação final.

**Processo correto**:
1. Desenvolver features e modelo usando apenas dados de treino
2. Se necessário, usar validação cruzada temporal dentro do treino
3. Selecionar hiperparâmetros usando validação (não teste)
4. Avaliar modelo final no teste apenas no final do desenvolvimento

### Validação Cruzada Temporal (opcional)

Se precisar tunar hiperparâmetros dentro do treino:

```
Fold 1: Treino 2022 → Validação 2023 (parcial)
Fold 2: Treino 2022-2023(parcial) → Validação 2023(resto)
```

## Implementação

```python
def create_temporal_split(df: pd.DataFrame, test_size: float = 0.2):
    """
    Cria split temporal para validação.
    
    Args:
        df: DataFrame com coluna 'ra' como chave
        test_size: proporção de alunos para teste
        
    Returns:
        train_ras, test_ras: listas de RAs para cada split
    """
    # Alunos que aparecem em 2023 E 2024
    ras_validos = df['ra'].unique()
    
    # Split aleatório de alunos (não de registros)
    n_test = int(len(ras_validos) * test_size)
    
    np.random.seed(42)
    test_ras = np.random.choice(ras_validos, size=n_test, replace=False)
    train_ras = [ra for ra in ras_validos if ra not in test_ras]
    
    return train_ras, test_ras
```

---

## Checklist de Validação

- [ ] Split é por aluno (RA), não por registro
- [ ] Nenhuma informação do teste vazou para treino
- [ ] Teste usado apenas uma vez para avaliação final
- [ ] Threshold escolhido antes de ver resultados no teste
- [ ] Métricas reportadas incluem intervalos de confiança (se possível)
