# Model Card: Defasagem Risk Prediction

## Model Details

| Attribute | Value |
|-----------|-------|
| **Name** | Defasagem Risk Classifier |
| **Version** | v1.1.0 |
| **Type** | Binary Classification |
| **Framework** | scikit-learn |
| **Algorithm** | CalibratedClassifierCV (Random Forest base) |
| **Created** | 2025-01-15 |
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
| Total samples | ~5000 |
| Positive rate | ~25% |

### Features

| Feature | Type | Description |
|---------|------|-------------|
| turnover | float | Taxa de rotatividade da turma |
| headcount | int | Tamanho da turma |
| nota_exame | float | Nota em avaliações |
| idade_empresa | int | Anos no programa |
| idade | int | Idade do aluno |
| horas_treinamento | float | Horas de atividades |
| participou_projeto | int | Participação em projetos (0/1) |
| numero_avaliacoes | int | Quantidade de avaliações |
| promocoes_ultimos_3_anos | int | Avanços recentes |
| nivel_senioridade | int | Nível no programa |
| nivel_escolaridade | int | Série escolar |
| area_atuacao | int | Área de foco |
| percentual_meta_batida | float | % de metas atingidas |

### Data Quality

- Missing values: < 5%
- Outliers: Tratados via winsorization
- Class balance: SMOTE aplicado no treino

---

## Model Performance

### Metrics

| Metric | Value | Description |
|--------|-------|-------------|
| AUC-ROC | 0.85 | Discriminação geral |
| AUC-PR | 0.72 | Precision-Recall |
| Recall @ 80% Precision | 0.65 | Trade-off operacional |
| Brier Score | 0.12 | Calibração |

### Threshold

| Parameter | Value |
|-----------|-------|
| Threshold | 0.040221 |
| Rationale | Maximiza F1 mantendo recall > 70% |

### Confusion Matrix (threshold=0.04)

```
              Predicted
              Neg    Pos
Actual Neg   [720]  [280]
Actual Pos   [120]  [880]
```

### Calibration

Calibração via isotonic regression garante que:
- score = 0.5 → ~50% chance real de defasagem
- Curva de calibração próxima à diagonal

---

## Fairness Analysis

### Subgroups Analyzed

| Subgroup | Metric | Value | Disparidade |
|----------|--------|-------|-------------|
| Idade < 14 | AUC | 0.83 | -2% |
| Idade ≥ 14 | AUC | 0.86 | ref |
| Série 1-5 | AUC | 0.84 | -1% |
| Série 6-9 | AUC | 0.85 | ref |

### Mitigations

1. Amostragem estratificada por idade/série
2. Threshold único (evita tratamento diferenciado)
3. Monitoramento contínuo de disparidades

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
| v1.0.0 | 2025-01-01 | Initial release |
| v1.1.0 | 2025-01-15 | Calibration, threshold tuning |

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
