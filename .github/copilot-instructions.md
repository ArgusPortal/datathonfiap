# Passos Mágicos — Copilot Custom Instructions

## Projeto

Sistema de predição de risco de defasagem escolar para a ONG **Passos Mágicos** (Datathon FIAP 2025). Classifica alunos como em risco (`em_risco_2024 = 1`) ou não, usando indicadores educacionais PEDE/INDE.

**Stack principal**: Python 3.11 (backend/ML) + TypeScript/React (frontend) + Docker (deploy fullstack).

---

## Arquitetura

```
datathonfiap/
├── src/              # Pipeline ML (train, evaluate, feature engineering, data quality)
├── app/              # API FastAPI de inferência (production-hardened)
├── frontend/         # React + Vite + Tailwind + shadcn/ui + Nivo charts
├── tests/            # 450+ testes pytest (unit, integration, smoke)
├── artifacts/        # Modelo treinado (.joblib), metadados, métricas, assinaturas
├── data/             # raw/ → interim/ → processed/ (pipeline ETL)
├── models/           # Registry de modelos versionados
├── monitoring/       # inference_store para armazenamento de eventos
├── notebooks/        # EDA e análise de modelos (Jupyter)
├── scripts/          # seed_predictions.py, compute_fairness.py
├── docs/             # 30+ documentos (model card, runbooks, data contracts)
├── loadtest/         # Locust para testes de carga
└── .github/          # CI/CD (ci.yml, cd.yml, security_scan.yml)
```

---

## Modelo de ML

- **Algoritmo**: RandomForestClassifier + CalibratedClassifierCV
- **Versão**: v1.2.0 (11 features, threshold 0.2814)
- **Target**: `em_risco_2024` (binário)
- **Métrica primária**: F2-score (prioriza recall sobre precision)
- **Constraints**: recall ≥ 75%, precision ≥ 50%
- **Features**: 4 indicadores PEDE (ian, ida, ipp, ips) + idade + 4 deltas temporais (iaa, ian, ieg, ipv) + 2 derivadas (media, std)

### Pipeline de treinamento (`src/train.py`)

1. `src/make_dataset.py` — Carrega PEDE2024.xlsx, normaliza colunas, gera target
2. `src/feature_engineering.py` — Cria deltas temporais, features agregadas, normaliza fases
3. `src/preprocessing.py` — ColumnTransformer (StandardScaler numéricas, OneHotEncoder categóricas, SimpleImputer)
4. `src/train.py` — Treina múltiplos candidatos, calibra, seleciona threshold por F2
5. `src/evaluate.py` — Métricas (recall, precision, F1, F2, PR-AUC, Brier), calibração
6. `src/registry.py` — Versionamento: register → promote champion → rollback
7. `src/retrain.py` — Pipeline challenger vs champion com guardrails

---

## API FastAPI (`app/`)

**Endpoint principal**: `POST /predict` (single ou batch de instâncias)

| Módulo | Responsabilidade |
|--------|-----------------|
| `main.py` | Routes, lifespan, drift endpoint, artifacts endpoints |
| `config.py` | Configuração via env vars (PORT, MODEL_PATH, API_KEYS, SLO_*) |
| `schema.py` | Pydantic models (StudentFeatures, PredictRequest/Response) |
| `model_loader.py` | ModelManager — carrega modelo/metadata/signature do registry |
| `security.py` | API Key auth + rate limiting (token bucket in-memory) |
| `metrics.py` | MetricsStore — contadores persistentes, SLO check, P95 latência |
| `audit.py` | AuditTrail — registra cada inferência com hash, git SHA, lineage |
| `privacy.py` | Sanitização PII (CPF, email, telefone), anonimização |
| `drift_store.py` | DriftStore — log de estatísticas de features para PSI drift |
| `observability.py` | Structured logging per-request |
| `logging_config.py` | Request ID, JSON logger |

### Endpoints importantes

- `GET /health` — Status + model loaded + version
- `GET /ready` — Readiness probe
- `POST /predict` — Predição (aceita batch)
- `GET /metadata` — Metadados do modelo
- `GET /metrics` — Métricas Prometheus-style ou JSON
- `GET /slo` — SLO compliance (P95 latência, error rate)
- `GET /drift/status` — PSI por feature, missing rates, score drift
- `GET /audit/recent` — Trail de auditoria
- `GET /inference/history` — Histórico de inferências
- `GET /artifacts/metrics` — Métricas de comparação de modelos
- `GET /artifacts/fairness` — Análise de fairness por subgrupo

---

## Frontend React (`frontend/`)

**Tech**: React 18 + TypeScript + Vite + Tailwind CSS + shadcn/ui + Nivo + Recharts + Lucide icons

### Páginas

| Página | Arquivo | Conteúdo |
|--------|---------|----------|
| Dashboard | `DashboardPage.tsx` | Visão geral, métricas, distribuição de risco |
| Modelo | `ModelPage.tsx` | Model card, performance, features, ética, fairness, governance |
| Monitoramento | `MonitoringPage.tsx` | SLO, drift PSI, missing values, audit trail |
| Predição | `PredictPage.tsx` | Formulário de predição + resultado visual |
| Alunos | `StudentsPage.tsx` | Tabela de inferências históricas |
| Análise | `AnalysisPage.tsx` | EDA com visualizações Nivo |
| Sobre | `AboutPage.tsx` | ODS, equipe, contexto |

### Estrutura de componentes

```
frontend/src/
├── components/
│   ├── charts/       # FairnessChart, FeatureImportance, RiskGauge, ROCCurve, etc.
│   ├── shared/       # StatCard, StatusBadge, InfoTooltip, EmptyState, Glossary
│   ├── layout/       # Layout.tsx, Footer.tsx
│   └── ui/           # shadcn/ui components (Button, Card, Tabs, etc.)
├── services/api.ts   # Cliente HTTP tipado para todos os endpoints
├── types/index.ts    # Interfaces TS matching com schemas FastAPI
├── stores/           # Zustand prediction store
└── hooks/            # Custom hooks (keyboard shortcuts, etc.)
```

---

## Convenções de código

### Python

- **Formatter**: Black (120 chars)
- **Linter**: Flake8 (max-line-length=120, ignore E203,W503)
- **Type checker**: Mypy (ignore-missing-imports)
- **Testes**: pytest + pytest-cov. Meta: ≥80% coverage
- **Docstrings**: Google style em português quando descritivo, inglês em APIs
- **Imports**: isort-compatível (stdlib → third-party → local)
- **Env vars**: Sempre via `os.getenv()` com defaults sensatos em `app/config.py`
- **Logging**: `logging.getLogger(__name__)`, structured JSON em produção

### TypeScript/React

- **Build**: `tsc -b && vite build`
- **Lint**: ESLint
- **Style**: Tailwind CSS utility-first, design system shadcn/ui
- **State**: React hooks + Zustand para stores globais
- **API**: Cliente centralizado em `services/api.ts` com tipos genéricos
- **Types**: Sempre tipar explicitamente, interfaces em `types/index.ts`
- **Components**: Functional components com props tipadas, sem `any` quando possível
- **Icons**: Lucide React

### Docker

- **Fullstack** (`Dockerfile.fullstack`): 3 stages (node:20-alpine → python:3.11-slim builder → python:3.11-slim)
- Nginx serve frontend estático + proxy `/api` para uvicorn
- Supervisor gerencia nginx + uvicorn
- `GIT_SHA` passado via build-arg para auditoria
- Build: `docker build -f Dockerfile.fullstack --build-arg GIT_SHA=$(git rev-parse --short HEAD) -t passos-magicos-fullstack .`

---

## Regras de negócio importantes

1. **Indicadores PEDE**: Range 0-10 (IAN, IDA, IEG, IAA, IPS, IPP, IPV). INDE é ponderado.
2. **Fases**: 0 (Alfa) a 8, mapeadas ordinalmente. Pesos do INDE variam por fase (0-7 vs 8).
3. **Target proxy**: `em_risco_2024 = 1` quando INDE < limiar da fase OU queda significativa.
4. **Features temporais**: Deltas inter-anuais (2022→2023) capturam tendência.
5. **Gênero**: Codificado como 0/1 (genero_2023). Fairness monitorado por subgrupo.
6. **Privacidade**: RA nunca é logado em auditoria. PII sanitizada via `privacy.py`.

---

## Testes

- **450+ testes**, organizado em `tests/`
- Nomes: `test_{module}.py` com funções `test_{behavior}`
- Fixtures: `conftest.py` não existe explicitamente; tests usam setup interno
- Markers: `@pytest.mark.smoke`, `@pytest.mark.integration`, `@pytest.mark.unit`
- CI: `pytest tests/ --cov=src --cov=app --cov-fail-under=80`
- API tests: `httpx.AsyncClient` com `app` FastAPI

---

## Drift & Monitoramento

- **PSI** (Population Stability Index): Calculado por feature, baseline (1ª metade dos eventos) vs current (2ª metade)
- **Bins**: 7 bins numéricos (very_low → high) + binary (zero/one) + categorical (cat_{value})
- **Thresholds PSI**: verde (<0.1), amarelo (0.1-0.2), vermelho (>0.2)
- **Missing rates**: Compara taxas de nulos entre baseline e atual
- **Score drift**: Média e std do risk_score entre janelas

---

## Documentação relevante

- `docs/model_card.md` — Model Card oficial
- `docs/data_contract.md` / `data_contract_v2.md` — Contrato de dados
- `docs/security_api.md` — Segurança da API
- `docs/monitoring_runbook.md` — Runbook de monitoramento
- `docs/retraining_policy.md` — Política de retreinamento
- `docs/model_governance.md` — Governança do modelo
- `docs/privacy_data_handling.md` — Privacidade e LGPD

---

## Comandos úteis

```bash
# Backend
pytest tests/ -x --cov=src --cov=app          # Rodar testes
python -m src.train --data data/processed/modeling_dataset.parquet --artifacts artifacts/
python -m src.registry list                     # Listar versões
uvicorn app.main:app --reload --port 8000       # Dev server

# Frontend
cd frontend && npm run dev                      # Vite dev server
cd frontend && npm run build                    # Build produção
cd frontend && npm run type-check               # TypeScript check

# Docker
docker build -f Dockerfile.fullstack --build-arg GIT_SHA=$(git rev-parse --short HEAD) -t passos-magicos-fullstack .
docker run -p 8080:80 passos-magicos-fullstack

# Seed / Scripts
python scripts/seed_predictions.py              # Gerar 300 predições iniciais
python scripts/compute_fairness.py              # Gerar análise de fairness
```

---

## Padrões de resposta

- Ao modificar endpoints da API, atualizar simultaneamente: schema Pydantic (`app/schema.py`), types TS (`frontend/src/types/index.ts`), cliente API (`frontend/src/services/api.ts`)
- Ao adicionar features ao modelo, atualizar: `src/feature_engineering.py`, `src/schema_validation.py`, `app/schema.py`, `artifacts/model_signature.json`
- Ao criar novos componentes React, seguir padrão: shadcn/ui + Tailwind + Lucide icons + Nivo para gráficos
- Ao adicionar testes, manter coverage ≥ 80%
- Sempre considerar implicações de privacidade (LGPD) ao lidar com dados de alunos
