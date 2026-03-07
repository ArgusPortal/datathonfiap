<div align="center">

# 🎓 Predição de Risco de Defasagem Escolar

### Sistema de Machine Learning para Identificação Precoce de Alunos em Risco

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)](https://scikit-learn.org)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)

[![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=white)](https://react.dev)
[![Tests](https://img.shields.io/badge/Tests-510%20passed-success?style=flat-square)](tests/)
[![Coverage](https://img.shields.io/badge/Coverage-81%25-brightgreen?style=flat-square)](htmlcov/)
[![License](https://img.shields.io/badge/License-Academic-blue?style=flat-square)](#-licença)

<br>

**🏆 Projeto Final | Especialização em Machine Learning Engineering | FIAP 2025**

*Em parceria com a ONG [Passos Mágicos](https://passosmagicos.org.br/)*

<br>

[Começar](#-quick-start) •
[Documentação](#-documentação) •
[API](#-api-reference) •
[Arquitetura](#-arquitetura)

</div>

---

## 📋 Sumário

- [Sobre o Projeto](#-sobre-o-projeto)
- [Quick Start](#-quick-start)
- [Arquitetura](#-arquitetura)
- [API Reference](#-api-reference)
- [Pipeline de ML](#-pipeline-de-ml)
- [Monitoramento](#-monitoramento)
- [Qualidade](#-qualidade)
- [Governança](#-governança)
- [Documentação](#-documentação)
- [Frontend](#%EF%B8%8F-frontend)
- [Autor](#-autor)

---

## 🎯 Sobre o Projeto

<table>
<tr>
<td width="60%">

### O Problema

Crianças atendidas pela **ONG Passos Mágicos** podem entrar em **defasagem escolar** — um atraso que compromete seu desenvolvimento educacional. Identificar esse risco **antes** que aconteça permite intervenções preventivas mais eficazes.

### A Solução

Um sistema completo de **Machine Learning** que:

- 🔮 **Prediz** risco de defasagem com antecedência
- 🚀 **Expõe** API REST para integração
- 📊 **Monitora** qualidade em produção
- 🔄 **Suporta** retraining automatizado
- 🛡️ **Garante** privacidade (LGPD)

</td>
<td width="40%">

### 📈 Métricas do Modelo v1.2.0

| Métrica | Valor |
|:--------|:-----:|
| **Recall** | 91.9% |
| **F2-Score** | 0.864 |
| **Precision** | 69.5% |
| **PR-AUC** | 0.830 |
| **Brier** | 0.132 |
| **Threshold** | 0.281 |

### 🏗️ Stack

| Camada | Tecnologia |
|:-------|:-----------|
| ML | scikit-learn, RandomForest |
| API | FastAPI |
| Frontend | React 18 + Tailwind + Nivo |
| Deploy | Docker (fullstack) |
| CI/CD | GitHub Actions |

</td>
</tr>
</table>

---

## 🚀 Quick Start

### Pré-requisitos

```
✅ Python 3.11+
✅ Docker (opcional)
✅ Git
```

### 💻 Instalação Local

```bash
# 1️⃣ Clone o repositório
git clone https://github.com/ArgusPortal/datathonfiap.git
cd datathonfiap

# 2️⃣ Crie e ative o ambiente virtual
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 3️⃣ Instale as dependências
pip install -r requirements.txt

# 4️⃣ Suba a API
uvicorn app.main:app --port 8000
```

### 🐳 Com Docker (Fullstack — Frontend + API)

```bash
# Build da imagem fullstack (React + FastAPI + Nginx)
docker build -f Dockerfile.fullstack \
  --build-arg GIT_SHA=$(git rev-parse --short HEAD) \
  -t passos-magicos-fullstack .

# Execute o container
docker run -d -p 8080:80 --name passos-magicos passos-magicos-fullstack

# Verifique
curl http://localhost:8080/api/health
```

<div align="center">

**🌐 Acesse a aplicação:** http://localhost:8080

**📡 API docs:** http://localhost:8080/api/docs

</div>

---

## 🏛️ Arquitetura

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              ARQUITETURA DO SISTEMA                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐          │
│   │  Dados   │────▶│ Pipeline │────▶│  Modelo  │────▶│   API    │          │
│   │  PEDE    │     │    ML    │     │  v1.2.0  │     │ FastAPI  │          │
│   └──────────┘     └──────────┘     └──────────┘     └────┬─────┘          │
│                                                           │                 │
│                    ┌──────────────────────────────────────┼────────────┐   │
│                    │              MONITORAMENTO           │            │   │
│                    │  ┌─────────┐  ┌─────────┐  ┌────────▼───────┐   │   │
│                    │  │  Drift  │  │  Logs   │  │   Inference    │   │   │
│                    │  │ Report  │  │  JSON   │  │     Store      │   │   │
│                    │  └─────────┘  └─────────┘  └────────────────┘   │   │
│                    └─────────────────────────────────────────────────┘   │
│                                                                          │
│   ┌──────────────────────────────────────────────────────────────────┐   │
│   │                         GOVERNANÇA                                │   │
│   │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │   │
│   │  │ Registry │  │ Retrain  │  │   KPIs   │  │  Action  │        │   │
│   │  │  Models  │  │ Pipeline │  │  Impact  │  │  Matrix  │        │   │
│   │  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │   │
│   └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### 📁 Estrutura do Projeto

```
datathonfiap/
├── 📁 app/                    # API FastAPI
│   ├── main.py               # Endpoints principais
│   ├── schema.py             # Pydantic models
│   ├── security.py           # Auth & Rate Limiting
│   ├── privacy.py            # PII handling
│   ├── metrics.py            # Observability & SLOs
│   ├── audit.py              # Audit trail (JSONL persistido)
│   ├── drift_store.py        # PSI drift detection
│   └── observability.py      # Structured logging
├── 📁 frontend/               # React 18 + TypeScript + Vite
│   └── src/
│       ├── pages/            # 7 páginas (Dashboard, Model, Monitoring, etc.)
│       ├── components/       # Charts (Nivo, Recharts), shared, layout, ui
│       ├── services/api.ts   # Cliente HTTP tipado
│       └── types/index.ts    # Interfaces TS
├── 📁 src/                    # Pipeline ML
│   ├── make_dataset.py       # Ingestão de dados
│   ├── feature_engineering.py# Feature engineering (11 features)
│   ├── train.py              # Treinamento (RF + Calibração)
│   ├── evaluate.py           # Avaliação (F2, recall, calibração)
│   ├── registry.py           # Model Registry versionado
│   └── retrain.py            # Retraining pipeline
├── 📁 tests/                  # 510 testes automatizados
├── 📁 docs/                   # 30+ documentos
├── 📁 artifacts/              # Modelo serializado
├── 📁 models/registry/        # Versões registradas
├── 📁 logs/                   # drift_events.jsonl, audit, metrics
├── 🐳 Dockerfile.fullstack    # Multi-stage (Node + Python + Nginx)
├── 🐳 Dockerfile              # API-only container
└── 📄 requirements.txt        # Dependências Python
```

---

## 📡 API Reference

### Endpoints Principais

| Método | Endpoint | Descrição | Auth |
|:------:|:---------|:----------|:----:|
| `GET` | `/health` | Health check | ❌ |
| `GET` | `/ready` | Readiness probe | ❌ |
| `GET` | `/metadata` | Info do modelo | ❌ |
| `POST` | `/predict` | Predição (single ou batch) | ✅ |
| `GET` | `/metrics` | Métricas Prometheus/JSON | ✅ |
| `GET` | `/metrics/history` | Histórico de snapshots | ✅ |
| `GET` | `/slo` | Status SLOs | ✅ |
| `GET` | `/drift/status` | PSI drift por feature | ✅ |
| `GET` | `/audit/recent` | Audit trail | ✅ |
| `GET` | `/inference/history` | Histórico de inferências | ✅ |
| `GET` | `/artifacts/metrics` | Comparação de modelos | ❌ |
| `GET` | `/artifacts/fairness` | Análise de fairness | ❌ |

### 🔮 Exemplo de Predição

```bash
curl -X POST http://localhost:8080/api/predict \
  -H "Content-Type: application/json" \
  -d '{
    "instances": [{
      "ian_2023": 7.2,
      "ida_2023": 5.8,
      "ipp_2023": 7.5,
      "ips_2023": 8.0,
      "idade_2023": 14,
      "delta_iaa_2022_2023": 0.1,
      "delta_ian_2022_2023": 0.5,
      "delta_ieg_2022_2023": -0.2,
      "delta_ipv_2022_2023": 0.0,
      "media_indicadores": 6.8,
      "std_indicadores": 0.9
    }]
  }'
```

**Resposta:**
```json
{
  "predictions": [{
    "risk_score": 0.757,
    "risk_label": 1,
    "model_version": "v1.2.0"
  }],
  "request_id": "abc123",
  "processing_time_ms": 12.5
}
```

---

## 🔬 Pipeline de ML

<div align="center">

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│ INGEST  │───▶│ TARGET  │───▶│FEATURES │───▶│  TRAIN  │───▶│ DEPLOY  │
│  PEDE   │    │ t + 1   │    │ 11 feat │    │   RF    │    │  API    │
└─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘
```

</div>

### Etapas do Pipeline

| Etapa | Descrição |
|:------|:----------|
| **1. Ingest** | Leitura do dataset PEDE + normalização |
| **2. Target** | Construção do target binário (defasagem t+1) |
| **3. Features** | 11 features selecionadas por ablation: 4 PEDE + idade + 4 deltas + 2 derivadas |
| **4. Split** | Validação temporal (treino 2023 → validação 2024) |
| **5. Train** | RandomForestClassifier + CalibratedClassifierCV (isotonic) |
| **6. Threshold** | Otimizado para max F2 com recall ≥ 0.75 (threshold=0.2814) |
| **7. Deploy** | Serialização joblib + API FastAPI + Frontend React |

### 📊 Features do Modelo (v1.2.0 — 11 features)

Selecionadas via **ablation experiment** (VOLATILE_ONLY — maior poder preditivo individual):

| Grupo | Feature | Descrição | Range |
|:------|:--------|:----------|:-----:|
| **PEDE** | `ian_2023` | Adequação ao Nível | 0–10 |
| | `ida_2023` | Desenvolvimento Acadêmico | 0–10 |
| | `ipp_2023` | Performance Psicopedagógica | 0–10 |
| | `ips_2023` | Performance Psicossocial | 0–10 |
| **Demo** | `idade_2023` | Idade do aluno | 6–20 |
| **Deltas** | `delta_iaa_2022_2023` | Δ Autoavaliação 2022→2023 | -10–10 |
| | `delta_ian_2022_2023` | Δ Adequação ao Nível | -10–10 |
| | `delta_ieg_2022_2023` | Δ Engajamento | -10–10 |
| | `delta_ipv_2022_2023` | Δ Ponto de Virada | -10–10 |
| **Derivadas** | `media_indicadores` | Média dos 7 indicadores PEDE | 0–10 |
| | `std_indicadores` | Desvio padrão dos indicadores | 0–5 |

---

## 📊 Monitoramento

### 🔍 Drift Detection

```bash
# Gerar relatório de drift
python -m monitoring.drift_report --model_version v1.2.0 --last_n_days 7
```

| Status | PSI | Ação Recomendada |
|:------:|:---:|:-----------------|
| 🟢 Verde | < 0.10 | Normal |
| 🟡 Amarelo | 0.10–0.25 | Investigar |
| 🔴 Vermelho | > 0.25 | Considerar retrain |

### 📈 SLOs Configurados

| Métrica | Target | Crítico |
|:--------|:------:|:-------:|
| Latência P95 | ≤ 300ms | > 500ms |
| Error Rate | ≤ 1% | > 5% |
| Availability | 99.5% | < 99% |

---

## ✅ Qualidade

<div align="center">

| Métrica | Valor | Status |
|:--------|:-----:|:------:|
| **Testes** | 510 | ✅ |
| **Cobertura** | 81% | ✅ |
| **Meta** | 80% | ✅ |

</div>

```bash
# Executar testes com cobertura
pytest tests/ --cov=src --cov=app --cov=monitoring --cov-report=term-missing
```

### 🔒 Segurança

| Recurso | Implementação |
|:--------|:--------------|
| 🔐 **Autenticação** | API Key via header `X-API-Key` |
| ⏱️ **Rate Limiting** | 60 req/min por chave |
| 🛡️ **PII Detection** | CPF, email, telefone redatados |
| 📦 **Container Hardened** | Non-root user, multi-stage build |
| 🔍 **Security Scanning** | Bandit, Safety, pip-audit |

---

## 🏛️ Governança

### 👥 Papéis e Responsabilidades

| Papel | Responsabilidade |
|:------|:-----------------|
| 👔 **PO Score** | Decisão de uso, thresholds, aprovações |
| 🔧 **Owner Técnico** | Pipeline, API, monitoramento |
| 📋 **Data Steward** | Contrato de dados, qualidade |
| 🚨 **SRE** | Disponibilidade, incidentes |

### 🎯 Matriz de Ação

| Risco | Score | Ação | SLA |
|:-----:|:-----:|:-----|:---:|
| 🔴 **Alto** | ≥ 0.70 | Tutoria reforçada + Plano individual | 7 dias |
| 🟡 **Médio** | 0.30–0.69 | Monitoramento + Checkin semanal | 14 dias |
| 🟢 **Baixo** | < 0.30 | Acompanhamento padrão | — |

### 🔄 Feedback Loop

```
Score → Intervenção → Desfecho → Retraining
              ↓            ↓
        intervention   outcomes_log → labels para próximo treino
```

---

## 📚 Documentação

<details>
<summary><b>🔧 Técnica</b></summary>

| Documento | Descrição |
|:----------|:----------|
| [Análise Regras Negócio](docs/analise_regras_negocio.md) | Validação INDE/PEDE |
| [Data Contract v2](docs/data_contract_v2.md) | Schema com validações |
| [Model Card](docs/model_card.md) | Documentação completa do modelo |
| [Model Changelog](docs/model_changelog.md) | Histórico de versões |
| [Artifacts Architecture](docs/artifacts_architecture.md) | Sistema de versionamento |
| [Retraining Policy](docs/retraining_policy.md) | Triggers e processo |

</details>

<details>
<summary><b>🔒 Segurança & Privacy</b></summary>

| Documento | Descrição |
|:----------|:----------|
| [API Security](docs/security_api.md) | Auth, rate limit, validation |
| [Privacy & Data Handling](docs/privacy_data_handling.md) | LGPD, retenção |
| [Container Security](docs/container_security.md) | Hardening, scanning |

</details>

<details>
<summary><b>📈 Operação</b></summary>

| Documento | Descrição |
|:----------|:----------|
| [SRE Runbook](docs/sre_runbook.md) | Incident response |
| [Ops Playbook](docs/ops_playbook.md) | Checklist de saúde |
| [Monitoring Runbook](docs/monitoring_runbook.md) | Procedimentos |

</details>

<details>
<summary><b>🏛️ Governança</b></summary>

| Documento | Descrição |
|:----------|:----------|
| [Model Governance](docs/model_governance.md) | Papéis, ritos, políticas |
| [KPIs & Baseline](docs/kpis_and_baseline.md) | Métricas de impacto |
| [Action Matrix](docs/action_matrix_and_feedback_loop.md) | Score → ação → feedback |
| [Dashboards Spec](docs/dashboards_spec.md) | Especificação de dashboards |

</details>

<details>
<summary><b>📋 Outros</b></summary>

| Documento | Descrição |
|:----------|:----------|
| [Product Brief](docs/product_brief.md) | Visão do produto |
| [Decision Log](docs/decision_log.md) | Decisões arquiteturais |
| [Demo Runbook](docs/demo_runbook.md) | Roteiro de demonstração |
| [Video Script](docs/video_script.md) | Script do vídeo |

</details>

---

## 🛠️ Comandos Úteis

<details>
<summary><b>🧪 Testes</b></summary>

```bash
# Todos os testes
pytest tests/ -v

# Com cobertura
pytest tests/ --cov=src --cov=app --cov=monitoring --cov-fail-under=80

# Apenas um módulo
pytest tests/test_api_integration.py -v
```

</details>

<details>
<summary><b>🔄 MLOps</b></summary>

```bash
# Registrar nova versão (copia artifacts dev → registry)
python -m src.registry register --version v1.3.0 --artifacts artifacts/

# Artifacts em dev usam sufixo _v1:
# - model_v1.joblib → copiado como model.joblib
# - model_metadata_v1.json → copiado como model_metadata.json
# - model_signature_v1.json → copiado como model_signature.json
# - metrics_v1.json → copiado como metrics.json

# Promover para champion
python -m src.registry promote --version v1.3.0

# Rollback
python -m src.registry rollback --version v1.2.0

# Retraining
python -m src.retrain --new_version v1.3.0 --data data/processed/dataset_2024.parquet
```

</details>

<details>
<summary><b>📊 Monitoramento</b></summary>

```bash
# Drift report
python -m monitoring.drift_report --model_version v1.2.0 --last_n_days 7

# Build baseline
python -m monitoring.build_baseline --model_version v1.2.0

# Retenção de dados
python monitoring/retention.py --days 30 --dry-run
```

</details>

<details>
<summary><b>🔒 Segurança</b></summary>

```bash
# Scan de dependências
safety check -r requirements.txt
pip-audit -r requirements.txt

# Análise estática
bandit -r app/ src/

# Scan de container
docker run --rm aquasec/trivy image passos-magicos-fullstack
```

</details>

---

## 🖥️ Frontend

Interface web completa com **7 páginas** para visualização, predição e monitoramento:

| Página | Descrição |
|:-------|:----------|
| **Dashboard** | Visão geral, métricas do modelo, distribuição de risco |
| **Modelo** | Model card, performance, features, ética, fairness, governança |
| **Monitoramento** | SLO compliance, drift PSI, latência, audit trail |
| **Predição** | Formulário de predição individual + batch CSV + preenchimento aleatório |
| **Alunos** | Tabela de inferências históricas |
| **Análise** | EDA com visualizações interativas (Nivo) |
| **Sobre** | ODS, equipe, contexto do projeto |

**Stack frontend:** React 18 · TypeScript · Vite · Tailwind CSS · shadcn/ui · Nivo · Recharts · Lucide icons

```bash
# Desenvolvimento local
cd frontend && npm install && npm run dev
```

---

## 📜 Licença

Este projeto foi desenvolvido exclusivamente para fins acadêmicos como parte da **Especialização em Machine Learning Engineering da FIAP**.

| Item | Descrição |
|:-----|:----------|
| 📊 **Dados** | Fornecidos pela Passos Mágicos exclusivamente para o Datathon |
| 🔒 **PII** | Não armazenamos dados pessoais identificáveis |
| 📝 **Compliance** | Respeita LGPD e políticas da instituição |
| ⚠️ **Uso** | Restrito ao contexto acadêmico autorizado |

---

## 👤 Autor

<div align="center">

<img src="https://avatars.githubusercontent.com/u/ArgusPortal" width="120px" style="border-radius: 50%;" alt="Argus Portal"/>

### **Argus Portal**

[![GitHub](https://img.shields.io/badge/GitHub-ArgusPortal-181717?style=for-the-badge&logo=github)](https://github.com/ArgusPortal)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0A66C2?style=for-the-badge&logo=linkedin)](https://linkedin.com/in/argusportal)

*Machine Learning Engineer*

</div>

---

<div align="center">

### 🎓 FIAP — Especialização em Machine Learning Engineering

**Projeto Final | Datathon 2025**

*Em parceria com a ONG [Passos Mágicos](https://passosmagicos.org.br/)*

<br>

[![Ver no GitHub](https://img.shields.io/badge/Ver%20no%20GitHub-181717?style=for-the-badge&logo=github)](https://github.com/ArgusPortal/datathonfiap)

<br>

---

<sub>Desenvolvido com ❤️ para transformar educação através de dados</sub>

</div>
