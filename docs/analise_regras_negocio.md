# 📋 Análise de Conformidade: Regras de Negócio vs Implementação

**Projeto**: Datathon FIAP - Passos Mágicos  
**Data da Análise**: Janeiro 2026  
**Documento de Referência**: Modelo de Mensuração INDE (Índice de Desenvolvimento Educacional)

---

## 📊 Resumo Executivo

| Aspecto | Status | Observação |
|---------|--------|------------|
| **Estrutura de Indicadores** | ✅ Parcialmente Implementado | Indicadores presentes mas sem validação de cálculo |
| **Cálculo do IAN** | ⚠️ Divergente | Simplificado para binário ao invés de escala 10/5/2.5 |
| **Cálculo do IDA** | ❓ Não Verificável | Usado como feature, mas fórmula não implementada |
| **Cálculo do INDE** | ❌ Não Implementado | Ponderação por fase não existe no código |
| **Classificação Pedras** | 🔒 Bloqueado | Corretamente tratado como leakage |
| **Diferenciação Fase 8** | ❌ Não Implementado | Mesma lógica para todas as fases |
| **Target (Defasagem)** | ✅ Implementado | Conforme regra D < 0 → em_risco |

---

## 1. Análise por Indicador

### 1.1 IAN — Indicador de Adequação de Nível

#### 📜 Regra de Negócio (Documento)
```
D = Fase_Efetiva − Fase_Ideal

Se D ≥ 0  → "Em fase"   → IAN = 10
Se 0 > D > −2 → "Moderada" → IAN = 5
Se D ≤ −2 → "Severa"   → IAN = 2.5
```

#### 💻 Implementação Atual

**Arquivo**: [src/make_dataset.py](../src/make_dataset.py)

O IAN é recebido **pré-calculado** do arquivo Excel (`PEDE2024.xlsx`) e usado diretamente como feature:
- Range válido configurado: `(0, 10)` em [src/data_quality.py](../src/data_quality.py#L42)
- Usado como feature `ian_2023` no modelo

**⚠️ GAP IDENTIFICADO:**
- O código **não implementa** a lógica de cálculo do IAN
- Depende do valor vindo do Excel sem validar a fórmula
- Não há conversão da escala discreta (10/5/2.5) → assume valor contínuo

**📝 Recomendação:**
```python
def compute_ian(defasagem: float) -> float:
    """Calcula IAN conforme regra de negócio."""
    if defasagem >= 0:
        return 10.0  # Em fase
    elif defasagem > -2:
        return 5.0   # Moderada
    else:
        return 2.5   # Severa
```

---

### 1.2 IDA — Indicador de Desempenho Acadêmico

#### 📜 Regra de Negócio (Documento)
```
IDA = (Nota_Matemática + Nota_Português + Nota_Inglês) / 3
```
Para Fase 8: média geral universitária

#### 💻 Implementação Atual

**Status**: Não implementado como cálculo

O projeto tem acesso às notas individuais no Excel:
- `mat` / `matem` - Matemática
- `por` / `portug` - Português  
- `ing` / `ingles` - Inglês (alto missing: ~68%)

Mas o IDA é recebido **pré-calculado** e usado diretamente:
- Range: `(0, 10)` em data_quality.py
- Feature: `ida_2023`

**❓ GAP IDENTIFICADO:**
- Não há validação de que `IDA = média(mat, por, ing)`
- Notas individuais **não são usadas** como features separadas
- Lógica diferenciada para Fase 8 **não existe**

**📝 Recomendação:**
1. Validar no pipeline que `IDA ≈ mean(mat, por, ing)` (tolerância ±0.5)
2. Considerar usar notas individuais como features adicionais
3. Implementar flag para Fase 8 com cálculo diferenciado

---

### 1.3 IEG — Indicador de Engajamento

#### 📜 Regra de Negócio (Documento)
```
IEG = Soma(pontuações_tarefas) / N_tarefas
```
Inclui: tarefas de casa, atividades acadêmicas, voluntariado

#### 💻 Implementação Atual

- Recebido pré-calculado do Excel
- Range: `(0, 10)`
- Feature: `ieg_2023`

**Status**: ✅ Compatível (valor agregado usado corretamente)

---

### 1.4 IAA — Indicador de Autoavaliação

#### 📜 Regra de Negócio (Documento)
```
IAA = Soma(pontuações_respostas) / N_perguntas

Escala por fase:
- Fases 0-2: A=100%, B=70%, C=35% do valor base (10/6)
- Fases 3-8: A=100%, B=75%, C=50%, D=25% do valor base
```

#### 💻 Implementação Atual

- Recebido pré-calculado
- Range: `(0, 10)`
- Feature: `iaa_2023`

**⚠️ GAP IDENTIFICADO:**
- Não há validação da escala diferenciada por faixa etária
- Código não distingue se aluno é Fase 0-2 vs Fase 3-8

---

### 1.5 IPS — Indicador Psicossocial

#### 📜 Regra de Negócio
```
IPS = Média(avaliações_psicólogas)
```

#### 💻 Implementação Atual
- Feature: `ips_2023`
- Range: `(0, 10)`

**Status**: ✅ Compatível

---

### 1.6 IPP — Indicador Psicopedagógico

#### 📜 Regra de Negócio
```
IPP = Média(avaliações_pedagógicas)
```

#### 💻 Implementação Atual
- Feature: `ipp_2023`
- Range: `(0, 10)`

**Status**: ✅ Compatível

---

### 1.7 IPV — Indicador do Ponto de Virada

#### 📜 Regra de Negócio
Indicador **longitudinal e integrador** - avalia evolução sustentada do aluno.

#### 💻 Implementação Atual
- Feature: `ipv_2023`
- Range: `(0, 10)`
- Coluna `ponto_virada` / `atingiu_pv` está **bloqueada** (leakage)

**⚠️ Observação:** O IPV do ano anterior é usado corretamente, mas a coluna booleana de "atingiu ponto de virada" é tratada como leakage (correto!).

---

## 2. Cálculo do INDE (Ponderação)

### 📜 Regra de Negócio

**Fases 0-7:**
```
INDE = IAN×0.1 + IDA×0.2 + IEG×0.2 + IAA×0.1 + IPS×0.1 + IPP×0.1 + IPV×0.2
```

**Fase 8 (Universitários):**
```
INDE = IAN×0.1 + IDA×0.4 + IEG×0.2 + IAA×0.1 + IPS×0.2
// IPP e IPV não entram!
```

### 💻 Implementação Atual

**❌ NÃO IMPLEMENTADO**

O código:
1. Recebe INDE pré-calculado do Excel (`inde_2023`, `inde_22`)
2. **Não valida** a fórmula de ponderação
3. **Não diferencia** Fase 8 das demais
4. Usa INDE apenas como referência, não como target

**Evidência** ([src/data_quality.py](../src/data_quality.py)):
```python
INDICATOR_RANGES = {
    'inde': (0, 10),  # Apenas range, sem cálculo
    ...
}
```

**📝 Recomendação CRÍTICA:**
```python
def compute_inde(row: pd.Series, fase: int) -> float:
    """Calcula INDE conforme ponderação oficial."""
    if fase == 8:
        # Fase universitária
        return (
            row['ian'] * 0.1 +
            row['ida'] * 0.4 +
            row['ieg'] * 0.2 +
            row['iaa'] * 0.1 +
            row['ips'] * 0.2
        )
    else:
        # Fases 0-7
        return (
            row['ian'] * 0.1 +
            row['ida'] * 0.2 +
            row['ieg'] * 0.2 +
            row['iaa'] * 0.1 +
            row['ips'] * 0.1 +
            row['ipp'] * 0.1 +
            row['ipv'] * 0.2
        )
```

---

## 3. Classificação em Pedras (Faixas)

### 📜 Regra de Negócio
| Faixa | Range INDE | Significado |
|-------|------------|-------------|
| Quartzo | 3.0 - 6.1 | Maior risco |
| Ágata | 6.1 - 7.2 | Risco moderado |
| Ametista | 7.2 - 8.2 | Bom desempenho |
| Topázio | 8.2 - 9.4 | Excelente |

### 💻 Implementação Atual

**🔒 Corretamente Bloqueado como Leakage**

Arquivo [src/make_dataset.py](../src/make_dataset.py#L113):
```python
BLOCKED_COLUMNS = [
    'defasagem', 'fase_ideal', 'ponto_virada', 'pedra',  # ← Bloqueado!
    'destaque_inde', 'destaque_ida', 'destaque_ieg',
    ...
]
```

**Status**: ✅ Correto - pedra é derivada do INDE do mesmo ano, seria vazamento.

---

## 4. Target: Definição de Risco

### 📜 Regra de Negócio (IAN)
```
D = Fase_Efetiva - Fase_Ideal
D < 0 → Defasagem (aluno atrasado)
```

### 💻 Implementação Atual

**✅ IMPLEMENTADO CORRETAMENTE**

Arquivo [src/make_dataset.py](../src/make_dataset.py#L321):
```python
def compute_target(defasagem: pd.Series) -> pd.Series:
    """Computa target binário baseado na defasagem."""
    return (defasagem < 0).astype(int)
```

Documentação [docs/target_definition.md](../docs/target_definition.md):
```
Defasagem = Fase_Efetiva - Fase_Ideal
Se Defasagem < 0: em_risco = 1
Senão: em_risco = 0
```

**Status**: ✅ Conforme especificação

---

## 5. Gaps Críticos Identificados

### 🔴 Alta Prioridade

| # | Gap | Impacto | Arquivo |
|---|-----|---------|---------|
| 1 | INDE não é calculado, apenas importado | Não validamos fórmula oficial | src/make_dataset.py |
| 2 | Ponderação Fase 8 não diferenciada | Universitários tratados igual | src/make_dataset.py |
| 3 | IAN escala 10/5/2.5 não validada | Pode haver inconsistência | src/data_quality.py |

### 🟡 Média Prioridade

| # | Gap | Impacto | Arquivo |
|---|-----|---------|---------|
| 4 | IDA não validado vs notas individuais | Possível inconsistência | - |
| 5 | IAA escala por idade não validada | Comparabilidade | - |
| 6 | Notas individuais não usadas | Perda de informação | src/feature_engineering.py |

### 🟢 Baixa Prioridade

| # | Gap | Impacto | Arquivo |
|---|-----|---------|---------|
| 7 | IPV conceitual não operacionalizado | Funciona como caixa preta | - |

---

## 6. Recomendações de Implementação

### 6.1 Validador de Regras de Negócio

Criar `src/business_rules.py`:

```python
"""Validador de regras de negócio dos indicadores PEDE."""

import pandas as pd
import numpy as np
from typing import Tuple, List


class INDEValidator:
    """Valida e calcula indicadores conforme regras oficiais."""
    
    WEIGHTS_STANDARD = {
        'ian': 0.1, 'ida': 0.2, 'ieg': 0.2, 'iaa': 0.1,
        'ips': 0.1, 'ipp': 0.1, 'ipv': 0.2
    }
    
    WEIGHTS_FASE8 = {
        'ian': 0.1, 'ida': 0.4, 'ieg': 0.2, 'iaa': 0.1, 'ips': 0.2
    }
    
    IAN_SCALE = {
        'em_fase': 10.0,      # D >= 0
        'moderada': 5.0,       # -2 < D < 0
        'severa': 2.5          # D <= -2
    }
    
    PEDRA_RANGES = [
        ('Quartzo', 3.0, 6.1),
        ('Ágata', 6.1, 7.2),
        ('Ametista', 7.2, 8.2),
        ('Topázio', 8.2, 9.4)
    ]
    
    @staticmethod
    def compute_ian(defasagem: float) -> float:
        """Calcula IAN a partir da defasagem."""
        if pd.isna(defasagem):
            return np.nan
        if defasagem >= 0:
            return 10.0
        elif defasagem > -2:
            return 5.0
        else:
            return 2.5
    
    @staticmethod
    def compute_ida(mat: float, por: float, ing: float) -> float:
        """Calcula IDA como média das notas."""
        notas = [n for n in [mat, por, ing] if pd.notna(n)]
        if not notas:
            return np.nan
        return sum(notas) / len(notas)
    
    @classmethod
    def compute_inde(cls, row: pd.Series, fase: int = None) -> float:
        """Calcula INDE com ponderação por fase."""
        if fase is None:
            fase = row.get('fase', 0)
        
        weights = cls.WEIGHTS_FASE8 if fase == 8 else cls.WEIGHTS_STANDARD
        
        inde = 0.0
        for ind, weight in weights.items():
            value = row.get(ind, 0)
            if pd.notna(value):
                inde += value * weight
        
        return inde
    
    @classmethod
    def classify_pedra(cls, inde: float) -> str:
        """Classifica INDE em faixa de pedra."""
        if pd.isna(inde):
            return None
        for pedra, low, high in cls.PEDRA_RANGES:
            if low <= inde < high:
                return pedra
        if inde >= 9.4:
            return 'Topázio'
        return 'Quartzo'
    
    @classmethod
    def validate_inde(cls, df: pd.DataFrame, tolerance: float = 0.5) -> pd.DataFrame:
        """Valida INDE calculado vs esperado."""
        results = []
        for idx, row in df.iterrows():
            fase = row.get('fase', 0)
            inde_excel = row.get('inde')
            inde_calc = cls.compute_inde(row, fase)
            
            diff = abs(inde_excel - inde_calc) if pd.notna(inde_excel) and pd.notna(inde_calc) else np.nan
            valid = diff <= tolerance if pd.notna(diff) else None
            
            results.append({
                'ra': row.get('ra'),
                'fase': fase,
                'inde_excel': inde_excel,
                'inde_calculated': inde_calc,
                'difference': diff,
                'valid': valid
            })
        
        return pd.DataFrame(results)
```

### 6.2 Adicionar Validação no Pipeline

Em `src/make_dataset.py`, adicionar:

```python
from business_rules import INDEValidator

def validate_business_rules(df: pd.DataFrame) -> dict:
    """Valida conformidade com regras de negócio."""
    results = {
        'inde_validation': None,
        'ian_validation': None,
        'warnings': []
    }
    
    # Valida INDE
    if all(c in df.columns for c in ['inde', 'ian', 'ida', 'ieg', 'iaa', 'ips', 'ipp', 'ipv']):
        validation = INDEValidator.validate_inde(df)
        pct_valid = validation['valid'].mean()
        results['inde_validation'] = {
            'pct_valid': pct_valid,
            'n_invalid': (~validation['valid']).sum()
        }
        if pct_valid < 0.95:
            results['warnings'].append(
                f"⚠️ {(1-pct_valid)*100:.1f}% dos INDE divergem da fórmula oficial"
            )
    
    return results
```

---

## 7. Checklist de Conformidade

- [x] Target binário baseado em defasagem < 0
- [x] Indicadores na escala 0-10
- [x] Pedra bloqueada como leakage
- [x] Features do ano anterior (t) para predizer ano (t+1)
- [ ] Cálculo INDE com ponderação oficial
- [ ] Diferenciação Fase 8 (universitários)
- [ ] Validação IAN escala discreta
- [ ] Validação IDA = média(mat, por, ing)
- [ ] IAA escala por faixa etária
- [ ] Notas individuais como features

---

## 8. Conclusão

O projeto implementa corretamente:
1. **Target de defasagem** conforme regra D < 0
2. **Bloqueio de leakage** (pedra, ponto_virada)
3. **Uso de indicadores** na escala 0-10

**Gaps principais:**
1. **Cálculo do INDE não implementado** - depende do Excel
2. **Fase 8 não diferenciada** - deveria ter pesos diferentes
3. **IAN escala discreta não validada** - assumido contínuo

**Impacto nos resultados:**
Se os dados do Excel estiverem corretos, o impacto é baixo. Porém, não há garantia de que a fórmula oficial está sendo aplicada nos dados de origem.

**Próximos passos sugeridos:**
1. Implementar `business_rules.py` para validação
2. Adicionar check de conformidade no pipeline
3. Criar feature derivada `is_fase_8` para tratamento diferenciado
4. Considerar usar notas individuais (mat, por, ing) como features
