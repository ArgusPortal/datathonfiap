# Model Card: Defasagem Risk Prediction

## Model Details

| Attribute | Value |
|-----------|-------|
| **Name** | Defasagem Risk Classifier |
| **Version** | v1.1.0 |
| **Type** | Binary Classification |
| **Framework** | scikit-learn |
| **Algorithm** | CalibratedClassifierCV (HistGradientBoosting base) |
| **Created** | 2026-02-07 |
| **Maintainer** | Datathon FIAP Team |

---

## Intended Use

### Primary Use Case

Predição de risco de defasagem escolar para alunos do programa Passos Mágicos, permitindo intervenção precoce e alocação otimizada de recursos.

### Intended Users

- Coordenadores pedagógicos
- Assistentes sociais
- Equipe de gestão da ONG

### Out-of-Scope Uses

- Decisões automatizadas sem revisão humana
- Uso em contextos não-educacionais
- Predição para populações fora do escopo do programa

---

## Training Data

### Dataset

| Attribute | Value |
|-----------|-------|
| Source | Dados históricos Passos Mágicos |
| Period | 2020-2024 |
| Total samples | 765 |
| Positive rate | ~40.5% |
| Train size | 612 |
| Test size | 153 |

### Features

| Feature | Type | Description |
|---------|------|-------------|
| fase_2023 | float | Fase escolar do aluno (1-9) |
| iaa_2023 | float | Índice de Autoavaliação |
| ian_2023 | float | Índice de Adequação ao Nível |
| ida_2023 | float | Índice de Desenvolvimento Acadêmico |
| idade_2023 | float | Idade do aluno |
| ieg_2023 | float | Índice de Engajamento |
| instituicao_2023 | object | Instituição de ensino (código) |
| ipp_2023 | float | Índice de Performance Pedagógica |
| ips_2023 | float | Índice de Performance Social |
| ipv_2023 | float | Índice de Ponto de Virada |
| genero_2023 | float | Gênero do aluno |
| ano_ingresso_2023 | float | Ano de ingresso no programa |
| anos_pm_2023 | float | Tempo no programa Passos Mágicos |
| delta_ian_2022_2023 | float | Variação IAN 2022→2023 |
| delta_ida_2022_2023 | float | Variação IDA 2022→2023 |
| delta_ieg_2022_2023 | float | Variação IEG 2022→2023 |
| delta_iaa_2022_2023 | float | Variação IAA 2022→2023 |
| delta_ips_2022_2023 | float | Variação IPS 2022→2023 |
| delta_ipv_2022_2023 | float | Variação IPV 2022→2023 |
| has_prev_year_data | flo2at | Flag: aluno tem dados do ano anterior |
| *_missing (6) | float | Flags de missing por indicador |
| media_indicadores | float | Média dos indicadores educacionais |
| min_indicador | float | Valor mínimo entre indicadores |
| max_indicador | float | Valor máximo entre indicadores |
| std_indicadores | float | Desvio padrão dos indicadores |
| range_indicadores | float | Range (max - min) dos indicadores |
| fase_x_media | float | Interação fase × média |

### Data Quality

- Missing values: < 5%
- Outliers: Tratados via winsorization
- Class balance: SMOTE aplicado no treino

---

## Model Performance

### Metrics

| Metric | Validation | Test | Description |
|--------|-----------|------|-------------|
| Recall | 0.959 | 0.935 | Sensibilidade |
| Precision | 0.691 | 0.699 | Precisão |
| F1 | 0.803 | 0.800 | Harmonic mean |
| F2 | 0.890 | 0.876 | F2-Score (recall-weighted) |
| PR-AUC | 0.807 | 0.830 | Precision-Recall AUC |
| Brier Score | 0.134 | 0.132 | Calibração |
| Calibration Error | 0.102 | 0.106 | ECE |

### Threshold

| Parameter | Value |
|-----------|-------|
| Threshold | 0.34990 |
| Rationale | Max F2 com constraints min_recall≥0.75, min_precision≥0.50 |

### Confusion Matrix (threshold=0.35, test set)

```
              Predicted
              Neg    Pos
Actual Neg   [ 66]  [ 25]
Actual Pos   [  4]  [ 58]
```

Total: 153 samples (62 positivos, 91 negativos)

### Calibration

Calibração via sigmoid regression garante que:
- Scores distribuídos com melhor separação entre classes
- Brier Score = 0.132 (test set)
- ECE (Expected Calibration Error) = 0.106

---

## Fairness Analysis

Análise de equidade computada sobre o dataset completo (765 amostras, threshold 0.35).
Arquivo completo: `artifacts/fairness_analysis.json`.

### Por Gênero

| Grupo | N | Prevalência | Recall | Precision | F1 | F2 |
|-------|---|-------------|--------|-----------|-----|-----|
| Feminino | 415 | 35.9% | 0.987 | 0.750 | 0.852 | 0.928 |
| Masculino | 350 | 45.4% | 0.975 | 0.756 | 0.852 | 0.922 |

**Recall disparity: 0.012** — equidade excelente entre gêneros.

### Por Fase

| Grupo | N | Prevalência | Recall | Precision | F1 | F2 |
|-------|---|-------------|--------|-----------|-----|-----|
| ALFA | 174 | 75.9% | 1.000 | 0.805 | 0.892 | 0.954 |
| FASE 1 | 138 | 44.2% | 0.984 | 0.690 | 0.811 | 0.906 |
| FASE 2 | 153 | 16.3% | 0.880 | 0.449 | 0.595 | 0.738 |
| FASE 3 | 94 | 44.7% | 1.000 | 0.894 | 0.944 | 0.977 |
| FASE 4 | 67 | 37.3% | 0.960 | 0.828 | 0.889 | 0.930 |
| FASE 5 | 43 | 48.8% | 0.952 | 0.870 | 0.909 | 0.935 |
| FASE 6 | 17 | 11.8% | 1.000 | 1.000 | 1.000 | 1.000 |
| FASE 7 | 20 | 0.0% | — | — | — | — |
| FASE 8 | 59 | 0.0% | — | — | — | — |

**Recall disparity: 0.120** — FASE 2 tem menor recall (0.880), possivelmente por baixa prevalência (16.3%). FASE 7 e 8 não possuem casos positivos no dataset.

### Por Instituição

| Grupo | N | Prevalência | Recall | Precision | F1 | F2 |
|-------|---|-------------|--------|-----------|-----|-----|
| Pública | 583 | 49.1% | 0.983 | 0.741 | 0.845 | 0.923 |
| Privada | 22 | 40.9% | 1.000 | 0.900 | 0.947 | 0.978 |
| Privada (Apadrinhamento) | 90 | 14.4% | 0.923 | 1.000 | 0.960 | 0.938 |

**Recall disparity: 0.077** — performance consistente entre tipos de instituição.

### Mitigações

1. Threshold único para todos os subgrupos (evita tratamento diferenciado)
2. Monitoramento de PSI por feature demográfica (gênero, fase, instituição)
3. Revisão humana obrigatória — modelo é auxiliar, não decisório
4. Relatório de fairness atualizado a cada retrain

---

## Limitations

### Known Limitations

1. **Temporal**: Modelo treinado em dados até 2024; pode não capturar mudanças pós-pandemia
2. **Geographic**: Dados apenas de São Paulo; generalização para outras regiões não validada
3. **Class imbalance**: Performance degrada se taxa real de defasagem mudar significativamente

### Failure Modes

1. **Novos alunos**: Poucos dados históricos reduzem confiança
2. **Features extremas**: Valores muito fora da distribuição de treino
3. **Drift**: Mudanças no perfil de alunos ao longo do tempo

---

## Ethical Considerations

### Potential Harms

1. **Estigmatização**: Labels podem criar profecia autorrealizável
2. **Viés de intervenção**: Mais atenção a alunos high-risk pode enviesar dados futuros
3. **Privacidade**: Features podem revelar situação socioeconômica

### Mitigations

1. Scores não compartilhados com alunos
2. Intervenções aplicadas a todos, com intensidade variada
3. Dados anonimizados em todos os logs
4. Revisão humana obrigatória antes de decisões

---

## Deployment

### Requirements

- Python 3.11+
- RAM: 512MB
- CPU: 1 core
- Latency: < 100ms P50

### Monitoring

| Metric | Alerta |
|--------|--------|
| Feature drift | PSI > 0.2 |
| Prediction drift | Distribution shift > 10% |
| Performance drift | Precision < 70% |

### Update Frequency

| Tipo | Frequência |
|------|------------|
| Retrain completo | Semestral ou se drift detectado |
| Calibração | Trimestral |
| Threshold review | Após cada retrain |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| v1.1.0 | 2026-02-07 | HistGradientBoosting + CalibratedClassifierCV (sigmoid), 34 features, threshold 0.35, business rules validation, delta features, missing flags, fairness analysis |
| v1.0.0 | 2026-02-01 | Initial release — Random Forest baseline |

---

## References

- [Dados internos] Relatórios anuais Passos Mágicos
- [Metodologia] FIAP Datathon Guidelines 2025
- [ML Practices] ML Ops Best Practices Guide

---

## Contact

- **Technical**: datathon-team@fiap.edu.br
- **Ethical concerns**: ethics-committee@passosmagicos.org.br
- **Data requests**: dpo@passosmagicos.org.br
