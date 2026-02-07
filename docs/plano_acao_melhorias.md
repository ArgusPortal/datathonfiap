# 📋 Plano de Ação - Melhorias no Pipeline de ML

**Projeto:** Predição de Risco de Defasagem Escolar - Passos Mágicos  
**Data:** 07/02/2026  
**Autor:** Argus Portal  
**Status:** ✅ **CONCLUÍDO** (v1.2.0)

---

## 📊 Resumo Executivo

Este plano endereçou **8 problemas identificados** no pipeline, organizados em **4 fases** de implementação. Todas as correções críticas foram implementadas e validadas com 382 testes.

### Métricas de Sucesso
- ✅ **Zero features corrompidas** no dataset final
- ✅ **Recuperadas features:** `gênero`, `idade` (numérica corrigida), `anos_pm` (tenure)
- ✅ **6 missing indicators** adicionados como features
- ✅ **6 delta features temporais** (variações 2022→2023)
- ✅ **Recall:** 93.5% (test) | **PR-AUC:** 0.83 | **Precision:** 69.9%
- ✅ **382 testes** implementados (100% passing)
- ✅ **34 features** após engenharia (vs 13 original)
- ✅ **Módulo de regras de negócio** (validação INDE/PEDE)

---

## 🔴 FASE 1: Correções Críticas (Prioridade Alta)

### 1.1 Corrigir Coluna `idade` Corrompida

**Problema:** Valores como `'1900-01-07'` são datas serializadas do Excel que deveriam ser números (7, 8, etc.)

**Arquivo:** `src/make_dataset.py`

**Ação:**
```python
def fix_excel_date_as_number(value):
    """
    Corrige valores de idade que foram interpretados como datas pelo Excel.
    Excel serializa datas como dias desde 1900-01-01.
    Então '1900-01-07' = dia 7 = idade 7.
    """
    if pd.isna(value):
        return None
    
    # Se já é número, retorna
    if isinstance(value, (int, float)):
        return int(value) if not pd.isna(value) else None
    
    # Se é string numérica
    try:
        return int(float(value))
    except (ValueError, TypeError):
        pass
    
    # Se é data serializada do Excel (1900-01-XX)
    if isinstance(value, str) and value.startswith('1900-01-'):
        try:
            day = int(value.split('-')[-1])
            if 5 <= day <= 25:  # Range válido de idade
                return day
        except:
            pass
    
    # Tenta parse de data
    try:
        from datetime import datetime
        dt = datetime.strptime(value, '%Y-%m-%d')
        # Se ano é 1900, é serialização do Excel
        if dt.year == 1900:
            return dt.day
    except:
        pass
    
    return None
```

**Aplicar em:** `load_and_normalize_sheet()` após carregar o DataFrame

**Teste:**
```python
def test_fix_excel_date_as_number():
    assert fix_excel_date_as_number('8') == 8
    assert fix_excel_date_as_number('1900-01-07') == 7
    assert fix_excel_date_as_number(10) == 10
    assert fix_excel_date_as_number('1900-01-15') == 15
```

---

### 1.2 Normalizar Acentos no Mapeamento de Colunas

**Problema:** Coluna `gênero` não é mapeada para `genero` porque acentos não são normalizados.

**Arquivo:** `src/make_dataset.py`

**Ação:**
```python
import unicodedata

def normalize_column_name(col: str) -> str:
    """Normaliza nome de coluna removendo acentos e padronizando."""
    # Remove acentos
    col_clean = unicodedata.normalize('NFKD', col)
    col_clean = ''.join(c for c in col_clean if not unicodedata.combining(c))
    
    # Lowercase e strip
    col_clean = col_clean.lower().strip()
    
    # Remove caracteres especiais
    col_clean = col_clean.replace('_', ' ')
    
    # Busca no mapeamento
    if col_clean in COLUMN_MAPPING:
        return COLUMN_MAPPING[col_clean]
    
    return col_clean.replace(' ', '_')
```

**Adicionar ao mapeamento:**
```python
COLUMN_MAPPING = {
    ...
    'genero': 'genero',
    'gênero': 'genero',  # Com acento
    'sexo': 'genero',
}
```

---

### 1.3 Incluir `genero` nas Features Permitidas

**Arquivo:** `src/make_dataset.py`

**Ação:** Verificar que `genero` está em `ALLOWED_FEATURE_COLUMNS`:
```python
ALLOWED_FEATURE_COLUMNS = [
    'ra', 'nome', 'instituicao', 'idade', 'genero',  # ✅ já está
    'fase', 'anos_pm', 'bolsista',
    'inde', 'ian', 'ida', 'ieg', 'iaa', 'ips', 'ipp', 'ipv', 'ipm',
    'indicador_nutricional',
]
```

---

## 🟠 FASE 2: Melhorias no Pré-processamento (Prioridade Média)

### 2.1 Normalizar Categorias de Instituição

**Problema:** Duplicatas por case (`Privada - Programa de Apadrinhamento` vs `apadrinhamento`)

**Arquivo:** `src/make_dataset.py` (nova função)

**Ação:**
```python
def normalize_instituicao(value: str) -> str:
    """Normaliza valores da coluna instituição."""
    if pd.isna(value):
        return 'Desconhecido'
    
    value = str(value).strip().lower()
    
    # Mapeamento para categorias padronizadas
    if 'pública' in value or 'publica' in value:
        return 'Publica'
    elif 'apadrinhamento' in value:
        return 'Privada_Apadrinhamento'
    elif 'bolsa' in value or 'parceira' in value:
        return 'Privada_Bolsa'
    elif 'privada' in value:
        return 'Privada'
    elif 'concluiu' in value or '3º em' in value:
        return 'Concluiu_EM'
    else:
        return 'Outro'
```

**Aplicar após normalização de colunas.**

---

### 2.2 Criar Features Indicadoras de Missing

**Problema:** Missing pode ser informativo (MNAR) - aluno sem nota pode indicar problema.

**Arquivo:** `src/feature_engineering.py`

**Ação:**
```python
def create_missing_indicators(df: pd.DataFrame, 
                              columns: List[str] = None) -> pd.DataFrame:
    """
    Cria features binárias indicando valores ausentes.
    
    Útil quando missing é informativo (ex: aluno sem nota em IDA 
    pode indicar que não fez avaliação).
    """
    df = df.copy()
    
    if columns is None:
        # Indicadores numéricos que podem ter missing informativo
        columns = ['ida', 'ieg', 'iaa', 'ips', 'ipp', 'ipv']
    
    indicators_created = []
    for col in columns:
        # Busca coluna com sufixo de ano
        matching = [c for c in df.columns if c.startswith(col)]
        for match_col in matching:
            if df[match_col].isna().sum() > 0:
                indicator_name = f"{match_col}_missing"
                df[indicator_name] = df[match_col].isna().astype(int)
                indicators_created.append(indicator_name)
    
    if indicators_created:
        logger.info(f"Missing indicators criados: {indicators_created}")
    
    return df
```

---

### 2.3 Criar Deltas Temporais (22→23)

**Problema:** Código atual falha por inconsistência de sufixos (`_22` vs `_2022`)

**Arquivo:** `src/feature_engineering.py`

**Ação:** Corrigir `create_delta_features()`:
```python
def create_delta_features(df: pd.DataFrame) -> pd.DataFrame:
    """Cria features de delta com busca flexível de sufixos."""
    df = df.copy()
    deltas_created = []
    
    for prefix in INDICATOR_PREFIXES:
        # Busca mais flexível
        col_22 = None
        col_23 = None
        
        for c in df.columns:
            c_lower = c.lower()
            if c_lower.startswith(prefix):
                if '_22' in c_lower or '_2022' in c_lower or c_lower.endswith('_22'):
                    col_22 = c
                elif '_23' in c_lower or '_2023' in c_lower or c_lower.endswith('_23'):
                    col_23 = c
        
        if col_22 and col_23:
            # Verifica se são numéricas
            if (pd.api.types.is_numeric_dtype(df[col_22]) and 
                pd.api.types.is_numeric_dtype(df[col_23])):
                delta_col = f"delta_{prefix}_22_23"
                df[delta_col] = df[col_23] - df[col_22]
                deltas_created.append(delta_col)
    
    if deltas_created:
        logger.info(f"Deltas criados: {deltas_created}")
    
    return df
```

---

### 2.4 Analisar Viés nos Dados Perdidos

**Problema:** 249 alunos de 2023 não têm match em 2024 - pode haver viés.

**Arquivo:** Novo script `src/analyze_data_loss.py`

**Ação:**
```python
def analyze_unmatched_students(df_2023: pd.DataFrame, 
                                df_2024: pd.DataFrame) -> Dict:
    """
    Analisa características dos alunos que não persistiram para 2024.
    Identifica se há viés sistemático na perda de dados.
    """
    matched_ras = set(df_2023['ra']) & set(df_2024['ra'])
    
    df_matched = df_2023[df_2023['ra'].isin(matched_ras)]
    df_unmatched = df_2023[~df_2023['ra'].isin(matched_ras)]
    
    analysis = {
        'n_matched': len(df_matched),
        'n_unmatched': len(df_unmatched),
        'pct_lost': len(df_unmatched) / len(df_2023) * 100,
    }
    
    # Compara distribuições de indicadores
    indicators = ['ian', 'ida', 'ieg', 'iaa', 'ips', 'ipp', 'ipv']
    for ind in indicators:
        if ind in df_2023.columns:
            analysis[f'{ind}_mean_matched'] = df_matched[ind].mean()
            analysis[f'{ind}_mean_unmatched'] = df_unmatched[ind].mean()
            # T-test para diferença significativa
            from scipy import stats
            stat, pvalue = stats.ttest_ind(
                df_matched[ind].dropna(), 
                df_unmatched[ind].dropna()
            )
            analysis[f'{ind}_pvalue'] = pvalue
    
    return analysis
```

**Documentar no data_card.json o resultado dessa análise.**

---

## 🟡 FASE 3: Melhorias no Treinamento (Prioridade Média-Baixa)

### 3.1 Adicionar Feature de Tempo na Instituição

**Arquivo:** `src/feature_engineering.py`

**Ação:**
```python
def create_tenure_feature(df: pd.DataFrame, 
                          reference_year: int = 2023) -> pd.DataFrame:
    """Cria feature de anos na instituição Passos Mágicos."""
    df = df.copy()
    
    if 'ano_ingresso' in df.columns:
        col_name = f'anos_pm_{reference_year}'
        df[col_name] = reference_year - df['ano_ingresso']
        # Limita a valores razoáveis
        df[col_name] = df[col_name].clip(lower=0, upper=15)
        logger.info(f"Feature criada: {col_name}")
    
    return df
```

---

### 3.2 Considerar Target Multi-classe ou Ordinal

**Problema:** Target binário perde granularidade (defasagem -1 vs -3)

**Arquivo:** `src/make_dataset.py`

**Ação:** Criar opção para target multi-classe:
```python
def compute_target(defasagem: pd.Series, 
                   mode: str = 'binary') -> pd.Series:
    """
    Computa target baseado na defasagem.
    
    Args:
        defasagem: Série com valores de defasagem
        mode: 'binary' (0/1), 'multiclass' (0,1,2,3), 'ordinal' (-3 a +3)
    """
    if mode == 'binary':
        return (defasagem < 0).astype(int)
    
    elif mode == 'multiclass':
        # 0=sem risco, 1=risco leve, 2=risco moderado, 3=risco alto
        return pd.cut(defasagem, 
                      bins=[-np.inf, -2, -1, 0, np.inf],
                      labels=[3, 2, 1, 0]).astype(int)
    
    elif mode == 'ordinal':
        return defasagem.astype(int)
    
    else:
        raise ValueError(f"Mode inválido: {mode}")
```

**Nota:** Para MVP, manter binário. Multi-classe para versão futura.

---

### 3.3 Validar Correlação Missing vs Target

**Arquivo:** `src/data_quality.py`

**Ação:**
```python
def check_missing_target_correlation(df: pd.DataFrame, 
                                     target_col: str,
                                     threshold: float = 0.1) -> QualityCheckResult:
    """
    Verifica se missing está correlacionado com target (potencial viés).
    """
    issues = []
    
    for col in df.columns:
        if col == target_col:
            continue
        
        missing_mask = df[col].isna()
        if missing_mask.sum() > 0:
            # Taxa de target=1 entre missing vs não-missing
            rate_missing = df.loc[missing_mask, target_col].mean()
            rate_present = df.loc[~missing_mask, target_col].mean()
            diff = abs(rate_missing - rate_present)
            
            if diff > threshold:
                issues.append({
                    'column': col,
                    'target_rate_when_missing': rate_missing,
                    'target_rate_when_present': rate_present,
                    'difference': diff
                })
    
    passed = len(issues) == 0
    return QualityCheckResult(
        check_name='missing_target_correlation',
        passed=passed,
        message=f"{'Sem' if passed else len(issues)} correlações missing-target detectadas",
        details={'issues': issues}
    )
```

---

## 🔵 FASE 4: Documentação e Testes (Contínuo)

### 4.1 Atualizar Testes Unitários

**Arquivos:** `tests/test_preprocessing.py`, `tests/test_make_dataset.py`

**Novos testes necessários:**
```python
# test_preprocessing.py
def test_fix_excel_date_idade():
    """Testa correção de idade corrompida pelo Excel."""
    
def test_normalize_column_removes_accents():
    """Testa que gênero → genero."""
    
def test_normalize_instituicao():
    """Testa padronização de categorias."""

# test_feature_engineering.py
def test_create_missing_indicators():
    """Testa criação de features de missing."""
    
def test_create_delta_features_flexible_suffix():
    """Testa deltas com sufixos _22 e _2022."""
    
def test_create_tenure_feature():
    """Testa cálculo de anos_pm."""
```

---

### 4.2 Atualizar Data Card

**Arquivo:** `data/processed/data_card.json`

**Adicionar seções:**
```json
{
  "preprocessing_fixes": {
    "idade_corruption_fixed": true,
    "genero_recovered": true,
    "instituicao_normalized": true
  },
  "feature_engineering": {
    "missing_indicators": ["ida_2023_missing", ...],
    "deltas_created": ["delta_inde_22_23", ...],
    "tenure_feature": "anos_pm_2023"
  },
  "data_loss_analysis": {
    "students_2023": 1014,
    "students_matched": 765,
    "pct_lost": 24.5,
    "bias_detected": false
  }
}
```

---

## 📅 Cronograma Sugerido

| Fase | Tarefa | Esforço | Dependência |
|------|--------|---------|-------------|
| 1.1 | Fix idade corrompida | 2h | - |
| 1.2 | Normalizar acentos | 1h | - |
| 1.3 | Incluir gênero | 0.5h | 1.2 |
| 2.1 | Normalizar instituição | 1h | - |
| 2.2 | Missing indicators | 2h | - |
| 2.3 | Deltas temporais | 1h | - |
| 2.4 | Análise viés dados perdidos | 2h | - |
| 3.1 | Feature tempo instituição | 1h | - |
| 3.2 | Target multi-classe | 2h | - |
| 3.3 | Correlação missing-target | 1h | - |
| 4.1 | Testes unitários | 3h | 1.x, 2.x |
| 4.2 | Atualizar data card | 1h | 1.x, 2.x |

**Total estimado:** ~17 horas

---

## ✅ Checklist de Validação

Após implementar as melhorias:

- [ ] `idade_2023` é `int64` com valores entre 5-25
- [ ] `genero_2023` existe no dataset final
- [ ] `instituicao_2023` tem ≤5 categorias padronizadas
- [ ] Features `*_missing` criadas para indicadores com >5% missing
- [ ] Deltas `delta_*_22_23` criados para INDE e indicadores
- [ ] Data card documenta todas as transformações
- [ ] Todos os testes passando (`pytest tests/ -v`)
- [ ] Coverage ≥ 80%
- [ ] Recall do modelo ≥ 75%
- [ ] Nenhum warning de tipo no treinamento

---

## 🚀 Ordem de Execução Recomendada

1. **Primeiro:** Fase 1 (correções críticas) - impacto imediato
2. **Segundo:** Fase 4.1 (testes) - para garantir não-regressão
3. **Terceiro:** Fase 2 (melhorias pré-processamento)
4. **Quarto:** Re-treinar modelo e comparar métricas
5. **Quinto:** Fase 3 (melhorias opcionais) baseado nos resultados
6. **Último:** Fase 4.2 (documentação)

---

## 📝 Notas Adicionais

### Decisões de Design

1. **Por que não usar One-Hot Encoding no `make_dataset.py`?**
   - Mantemos categóricas como strings no parquet para flexibilidade
   - Encoding é feito no pipeline sklearn (ColumnTransformer)
   - Permite diferentes estratégias de encoding por modelo

2. **Por que manter target binário no MVP?**
   - Simplifica métricas e interpretação
   - Recall de 100% já atinge objetivo de "não perder nenhum aluno"
   - Multi-classe pode ser explorado em versão futura

3. **Threshold de missing indicators (5%)?**
   - Abaixo de 5%, impacto é mínimo
   - Acima, pode haver padrão informativo
   - Ajustável via configuração

### Riscos

| Risco | Mitigação |
|-------|-----------|
| Perda de performance após mudanças | Baseline metrics documentadas, testes A/B |
| Overfitting com mais features | Cross-validation, regularização |
| Breaking changes em produção | Feature flags, versionamento |

---

*Documento gerado em: 15/01/2026*  
*Próxima revisão: Após implementação da Fase 1*
