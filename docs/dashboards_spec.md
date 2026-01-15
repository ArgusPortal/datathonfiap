# Especificação de Dashboards — Operação e Impacto

## 1. Dashboard de Operação (Modelo)

### Métricas Principais

| Métrica | Visualização | Granularidade |
|---------|--------------|---------------|
| **Tráfego** | Linha temporal | Hora/Dia |
| **Taxa de Erro** | Gauge + Linha | Hora/Dia |
| **Latência p95** | Gauge + Linha | Hora/Dia |
| **Distribuição risk_score** | Histograma | Dia |
| **Drift Status** | Semáforo (🟢🟡🔴) | Dia |
| **Versão do Modelo** | Texto/Timeline | Evento |

### Painéis Sugeridos

```
┌─────────────────────────────────────────────────────────┐
│  SAÚDE DO MODELO                                        │
├─────────────┬─────────────┬─────────────┬──────────────┤
│ Requests/h  │ Error Rate  │ p95 Latency │ Drift Status │
│    1,234    │    0.3%     │    127ms    │     🟢       │
├─────────────┴─────────────┴─────────────┴──────────────┤
│  [Gráfico de tráfego - últimas 24h]                    │
├────────────────────────────┬────────────────────────────┤
│  Distribuição de Scores    │  Top Features Drift        │
│  [Histograma]              │  [Barras horizontais]      │
├────────────────────────────┴────────────────────────────┤
│  Versão: v1.1.0 | Último deploy: 2025-01-10            │
└─────────────────────────────────────────────────────────┘
```

### Fontes de Dados

| Dado | Fonte | Atualização |
|------|-------|-------------|
| Tráfego, erros, latência | `GET /metrics` ou logs | Real-time/1min |
| Distribuição scores | `inference_store.jsonl` | Diária |
| Drift status | `drift_metrics.json` | Diária |
| Versão modelo | `models/registry/` | Por deploy |

---

## 2. Dashboard de Impacto

### Métricas Principais

| Métrica | Visualização | Granularidade |
|---------|--------------|---------------|
| **Taxa de Defasagem** | Linha (baseline vs atual) | Mês/Bimestre |
| **IAN Médio** | Linha (baseline vs atual) | Mês/Bimestre |
| **Taxa de Intervenção** | Gauge + Tendência | Mês |
| **Tempo até Ação** | Gauge + Tendência | Mês |
| **Cobertura de Scoring** | Gauge | Semana |

### Painéis Sugeridos

```
┌─────────────────────────────────────────────────────────┐
│  IMPACTO DO MODELO                                      │
├─────────────────────────────┬───────────────────────────┤
│  Taxa Defasagem             │  IAN Médio                │
│  Baseline: 23%              │  Baseline: 0.65           │
│  Atual: 19% (▼17%)          │  Atual: 0.71 (▲9%)        │
├─────────────────────────────┴───────────────────────────┤
│  [Gráfico comparativo baseline vs pós - por bimestre]   │
├─────────────────────────────────────────────────────────┤
│  RECORTES POR SEGMENTO                                  │
├──────────┬──────────┬──────────┬──────────┬─────────────┤
│  Fase 1-3│  Fase 4-6│  Fase 7-9│  Topázio │  Ametista   │
│   ▼12%   │   ▼18%   │   ▼21%   │   ▼15%   │    ▼19%    │
├──────────┴──────────┴──────────┴──────────┴─────────────┤
│  KPIs DE PROCESSO                                       │
├─────────────┬─────────────┬─────────────┬──────────────┤
│ Cobertura   │ Intervenção │ Tempo Ação  │ Aderência    │
│    97%      │    82%      │   5.2 dias  │    73%       │
└─────────────┴─────────────┴─────────────┴──────────────┘
```

### Fontes de Dados

| Dado | Fonte | Atualização |
|------|-------|-------------|
| Defasagem, IAN | Sistema escolar (dados cadastrais) | Bimestral |
| Intervenções | `intervention_log.csv` | Contínua |
| Desfechos | `outcomes_log.csv` | Mensal |
| Cobertura scoring | `inference_store.jsonl` | Semanal |

---

## 3. Filtros e Drill-down

### Filtros Globais
- **Período:** seletor de datas
- **Fase:** 1-9 ou grupos (1-3, 4-6, 7-9)
- **Pedra:** Topázio, Ametista, Ágata, Quartzo
- **Faixa de Risco:** alto, médio, baixo

### Drill-down Disponível
- Clique em segmento → detalhe por turma
- Clique em período → detalhe diário
- Clique em métrica → série histórica completa

---

## 4. Alertas Visuais

| Condição | Indicador |
|----------|-----------|
| Erro rate > 1% | 🔴 Vermelho |
| Latência p95 > 300ms | 🟡 Amarelo |
| Drift vermelho | 🔴 + Badge |
| Taxa intervenção < 70% | 🟡 Amarelo |
| Cobertura < 90% | 🟡 Amarelo |

---

## 5. Frequência de Atualização

| Dashboard | Frequência |
|-----------|------------|
| Operação — tempo real | 1 minuto |
| Operação — drift | Diária |
| Impacto — KPIs | Semanal |
| Impacto — baseline | Bimestral |

---

## 6. Implementação

### Opções Agnósticas
- **Simples:** Planilha com refresh manual + gráficos
- **Intermediário:** Metabase/Superset conectando em JSONs/CSVs
- **Avançado:** Grafana (operação) + BI tool (impacto)

### Dados Estruturados Disponíveis
```
monitoring/
├── inference_store.jsonl    # logs de inferência
├── drift_metrics.json       # métricas de drift
└── baseline.json            # distribuição baseline

docs/templates/
├── intervention_log.csv     # registro de intervenções
└── outcomes_log.csv         # registro de desfechos
```

---

## Referências
- KPIs definidos: `docs/kpis_and_baseline.md`
- Playbook operacional: `docs/ops_playbook.md`
