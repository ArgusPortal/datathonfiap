# Feature Availability: Anti-Vazamento

**Projeto**: Datathon FIAP - Passos Mágicos  
**Fase**: 1 - Data Product v1  
**Data**: Janeiro 2026

---

## Horizonte Temporal

- **Predição**: t → t+1 (usar dados do ano t para predizer risco no ano t+1)
- **Momento do score**: final do ano t, antes de iniciar ano t+1
- **MVP**: features 2023 → label 2024

## Features Permitidas (ALLOWED)

Features disponíveis no momento do score (final do ano t):

### Identificação
- `ra` - Registro do Aluno (chave única)

### Demográficas (estáticas ou conhecidas no ano t)
- `genero`
- `ano_ingresso`
- `idade_{ano}` - idade no ano t
- `instituicao_ensino_{ano}`

### Indicadores de Performance (ano t e anteriores)
- `inde_{ano}` - Índice de Desenvolvimento Educacional
- `iaa_{ano}` - Indicador de Auto Avaliação
- `ieg_{ano}` - Indicador de Engajamento
- `ips_{ano}` - Indicador Psicossocial
- `ipp_{ano}` - Indicador Psicopedagógico
- `ida_{ano}` - Indicador de Aprendizagem
- `ipv_{ano}` - Indicador de Ponto de Virada
- `ian_{ano}` - Indicador de Adequação ao Nível

### Notas (ano t e anteriores)
- `nota_mat_{ano}` - Matemática
- `nota_por_{ano}` - Português
- `nota_ing_{ano}` - Inglês

### Histórico de Classificação
- `pedra_{ano}` - Classificação (Quartzo/Ágata/Ametista/Topázio)
- `cg_{ano}` - Classificação Geral
- `cf_{ano}` - Classificação na Fase
- `ct_{ano}` - Classificação na Turma

### Engajamento
- `ponto_virada_{ano}` - Se atingiu ponto de virada (booleano)
- `num_avaliacoes_{ano}` - Quantidade de avaliações
- `indicado_bolsa_{ano}` - Se foi indicado para bolsa

### Fase/Turma (ano t)
- `fase_{ano}` - Fase atual no programa
- `turma_{ano}` - Turma atual

### Features Derivadas Permitidas (calcular a partir de anos anteriores)
- `delta_inde` - Variação INDE entre anos
- `delta_ian` - Variação IAN entre anos
- `tempo_no_programa` - Anos desde ingresso
- `historico_pedras` - Evolução de classificação

---

## Features BLOQUEADAS (BLOCKED)

**CRÍTICO**: Estas colunas do ano t+1 (2024) NÃO podem ser usadas como features!

### Vazamento Direto do Target
- `defasagem_{ano_target}` - É a base do target!
- `fase_ideal_{ano_target}` - Componente do cálculo do target
- `fase_{ano_target}` - Componente do cálculo do target

### Indicadores do Ano Futuro
- `inde_{ano_target}` - Calculado no próprio ano do target
- `ian_{ano_target}` - Calculado no próprio ano do target
- `iaa_{ano_target}`, `ieg_{ano_target}`, `ips_{ano_target}`, etc.
- `pedra_{ano_target}` - Derivada do INDE do ano target

### Avaliações do Ano Futuro
- `rec_av*_{ano_target}` - Recomendações de avaliadores
- `rec_psicologia_{ano_target}` - Recomendação psicológica
- `ponto_virada_{ano_target}` - Status no ano futuro

### Status do Ano Futuro
- `ativo_inativo_{ano_target}` - Status no ano target
- `indicado_bolsa_{ano_target}` - Indicação no ano target

---

## Nota sobre INDE e Componentes

O INDE é calculado como ponderação de: IAN, IDA, IEG, IAA, IPS, IPP, IPV

**Regra**: 
- ✅ INDE/IAN/etc do ano t (2023) → PERMITIDO como feature
- ❌ INDE/IAN/etc do ano t+1 (2024) → BLOQUEADO (vazamento)

O IAN especificamente mede "adequação ao nível" e pode estar correlacionado com defasagem. No entanto, se calculado no ano anterior (t), representa a situação passada do aluno e é informação legítima para predição.

---

## Implementação

```python
# src/make_dataset.py

BLOCKED_FEATURES_PATTERNS = [
    'defasagem',
    'fase_ideal',
    'inde_2024', 'ian_2024', 'iaa_2024', 'ieg_2024',
    'ips_2024', 'ipp_2024', 'ida_2024', 'ipv_2024',
    'pedra_2024',
    'rec_av', 'rec_psicologia_2024',
    'ponto_virada_2024',
    'ativo_inativo',
]

def check_leakage(df: pd.DataFrame, blocked_patterns: list) -> None:
    """Falha se encontrar colunas bloqueadas no dataset."""
    for col in df.columns:
        for pattern in blocked_patterns:
            if pattern.lower() in col.lower():
                raise ValueError(f"VAZAMENTO: coluna '{col}' contém padrão bloqueado '{pattern}'")
```

---

## Checklist Anti-Vazamento

- [ ] Nenhuma coluna do ano 2024 nas features (exceto RA para join)
- [ ] Target calculado apenas a partir de Defasagem_2024
- [ ] Todas features são do ano 2023 ou anteriores
- [ ] Função `check_leakage()` executada antes de salvar dataset
