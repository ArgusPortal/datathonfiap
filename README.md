<div align="center">

# 🎓 Predição de Risco de Defasagem Escolar

### Sistema de Machine Learning para Identificação Precoce de Alunos em Risco

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)](https://scikit-learn.org)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)

[![Tests](https://img.shields.io/badge/Tests-382%20passed-success?style=flat-square)](tests/)
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

### 📈 Métricas do Modelo (test)

| Métrica | Valor |
|:--------|:-----:|
| **Recall** | 93.5% |
| **F2-Score** | 0.876 |
| **Precision** | 69.9% |
| **PR-AUC** | 0.830 |
| **Brier** | 0.132 |
| **Threshold** | 0.350 |

### 🏗️ Stack

| Camada | Tecnologia |
|:-------|:-----------|
| ML | scikit-learn, HistGB |
| API | FastAPI |
| Deploy | Docker |
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

### 🐳 Com Docker

```bash
# Build da imagem
docker build -t datathon-api:v1 .

# Execute o container
docker run -d -p 8000:8000 --name datathon-api datathon-api:v1

# Verifique
curl http://localhost:8000/health
```

<div align="center">

**🌐 Acesse a documentação interativa:** http://localhost:8000/docs

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
│   │  PEDE    │     │    ML    │     │  v1.1.0  │     │ FastAPI  │          │
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
│   ├── security.py           # Auth & Rate Limiting
│   ├── privacy.py            # PII handling
│   └── metrics.py            # Observability
├── 📁 src/                    # Pipeline ML
│   ├── make_dataset.py       # Ingestão de dados
│   ├── train.py              # Treinamento
│   ├── evaluate.py           # Avaliação
│   ├── business_rules.py     # Validação regras INDE/PEDE
│   ├── feature_engineering.py# Feature engineering
│   ├── registry.py           # Model Registry
│   └── retrain.py            # Retraining pipeline
├── 📁 monitoring/             # Monitoramento
│   ├── drift_report.py       # Relatório de drift
│   ├── inference_store.py    # Armazenamento
│   └── retention.py          # Política de retenção
├── 📁 tests/                  # 382 testes automatizados
├── 📁 docs/                   # Documentação completa
├── 📁 artifacts/              # Modelo serializado (dev)
│   ├── model_v1.joblib
│   ├── model_metadata_v1.json
│   ├── model_signature_v1.json
│   └── metrics_v1.json
├── 📁 models/registry/        # Versões registradas
│   ├── champion.json
│   └── v1.2.0/
│       ├── model.joblib       # Normalizado (sem _v1)
│       ├── model_metadata.json
│       ├── model_signature.json
│       └── metrics.json
├── 🐳 Dockerfile              # Container hardened
└── 📄 requirements.txt        # Dependências
```

---

## 📡 API Reference

### Endpoints Principais

| Método | Endpoint | Descrição | Auth |
|:------:|:---------|:----------|:----:|
| `GET` | `/health` | Health check | ❌ |
| `GET` | `/ready` | Readiness probe | ❌ |
| `GET` | `/metadata` | Info do modelo | ❌ |
| `POST` | `/predict` | Predição | ✅ |
| `GET` | `/metrics` | Métricas | ✅ |
| `GET` | `/slo` | Status SLOs | ✅ |

### 🔮 Exemplo de Predição

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sua-chave" \
  -d '{
    "instances": [{
      "fase_2023": 3,
      "iaa_2023": 6.5,
      "ian_2023": 7.2,
      "ida_2023": 5.8,
      "idade_2023": 14,
      "ieg_2023": 6,
      "instituicao_2023": 1,
      "ipp_2023": 7.5,
      "ips_2023": 8,
      "ipv_2023": 6.2,
      "genero_2023": 1,
      "ano_ingresso_2023": 2020,
      "anos_pm_2023": 3,
      "delta_ian_2022_2023": 0.5,
      "delta_ida_2022_2023": 0.3,
      "delta_ieg_2022_2023": -0.2,
      "delta_iaa_2022_2023": 0.1,
      "delta_ips_2022_2023": 0.4,
      "delta_ipv_2022_2023": 0.0,
      "has_prev_year_data": 1,
      "media_indicadores": 6.8,
      "min_indicador": 5,
      "max_indicador": 8,
      "std_indicadores": 0.9,
      "range_indicadores": 3,
      "fase_x_media": 20.4
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
│  PEDE   │    │ t + 1   │    │  34 feat │    │ HistGB  │    │  API    │
└─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘
```

</div>

### Etapas do Pipeline

| Etapa | Descrição |
|:------|:----------|
| **1. Ingest** | Leitura do dataset PEDE + normalização |
| **2. Target** | Construção do target binário (defasagem t+1) |
| **3. Features** | 34 features: indicadores educacionais + deltas temporais + flags de missing + agregações |
| **4. Split** | Validação temporal (treino 2023 → validação 2024) |
| **5. Train** | HistGradientBoosting + calibração sigmoid |
| **6. Threshold** | Otimizado para max F2 com recall ≥ 0.75 (threshold=0.35) |
| **7. Deploy** | Serialização joblib + API FastAPI |

### 📊 Features do Modelo

| Feature | Descrição |
|:--------|:----------|
| `fase_2023` | Fase escolar (1-9) |
| `iaa_2023` | Índice de Autoavaliação |
| `ian_2023` | Índice de Adequação ao Nível |
| `ida_2023` | Índice de Desenvolvimento Acadêmico |
| `idade_2023` | Idade do aluno |
| `ieg_2023` | Índice de Engajamento |
| `ipp_2023` | Índice de Performance Pedagógica |
| `ips_2023` | Índice de Performance Social |
| `ipv_2023` | Índice de Ponto de Virada |
| `instituicao_2023` | Instituição de ensino (código) |
| `genero_2023` | Gênero do aluno |
| `ano_ingresso_2023` | Ano de ingresso no programa |
| `anos_pm_2023` | Tempo no programa Passos Mágicos |
| `delta_ian_2022_2023` | Variação IAN entre 2022→2023 |
| `delta_ida_2022_2023` | Variação IDA entre 2022→2023 |
| `delta_ieg_2022_2023` | Variação IEG entre 2022→2023 |
| `delta_iaa_2022_2023` | Variação IAA entre 2022→2023 |
| `delta_ips_2022_2023` | Variação IPS entre 2022→2023 |
| `delta_ipv_2022_2023` | Variação IPV entre 2022→2023 |
| `has_prev_year_data` | Flag: aluno tem dados do ano anterior |
| `*_missing` | Flags de missing para cada indicador |
| `media_indicadores` | Média dos indicadores |
| `min_indicador` | Valor mínimo entre indicadores |
| `max_indicador` | Valor máximo entre indicadores |
| `std_indicadores` | Desvio padrão dos indicadores |
| `range_indicadores` | Range (max - min) dos indicadores |
| `fase_x_media` | Interação fase × média |

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
| **Testes** | 382 | ✅ |
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
docker run --rm aquasec/trivy image datathon-api:v1
```

</details>

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
