# Datathon FIAP - Modelo de Risco de Defasagem Escolar

**Projeto**: Predição de risco de defasagem escolar para estudantes da Associação Passos Mágicos  
**Período**: 2022–2024  
**Status**: Fase 4 (MVP Operável) ✅

---

## Visão Geral

Modelo de Machine Learning para identificar estudantes em risco de defasagem escolar (moderada ou severa) usando dados históricos do programa Passos Mágicos. O score permite intervenção preventiva antes da defasagem se consolidar.

**Target**: predição binária t → t+1 (usar dados do ano t para predizer risco no ano t+1)  
**Métrica principal**: Recall da classe positiva ≥ 0.75  
**População**: Fases 0–7 do programa  
**Modelo Atual**: Random Forest calibrado (v1.1.0), threshold otimizado 0.040

---

## Quickstart

### 1. Setup do Ambiente

```bash
# Clonar repositório
git clone {{REPO_URL}}
cd datathonfiap

# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements.txt
```

### 2. Preparar Dados

```bash
# Colocar arquivo de dados em data/
# Estrutura esperada: data/raw/PEDE_PASSOS_DATASET_FIAP.csv
# Schema: ver docs/data_contract.md
```

### 3. Executar Pipeline de Dados

```bash
# Processar dados brutos
python -m src.make_dataset

# Saídas:
# - data/processed/dataset_train_2023.parquet
# - data/processed/dataset_val_2024.parquet
```

### 4. Treinar Modelo

```bash
# Treinar modelo v1 (com múltiplos candidatos)
python -m src.train --config configs/train_v1.yaml

# Artefatos gerados em artifacts/:
# - model_v1.joblib
# - model_metadata_v1.json
# - model_signature_v1.json
# - model_report_v1.md
```

### 5. Executar API

```bash
# Desenvolvimento
uvicorn app.main:app --reload --port 8000

# Produção
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Acessar: http://localhost:8000/docs (Swagger UI)

### 6. Deploy com Docker

```bash
# Build da imagem
docker build -t datathon-api:v1 .

# Executar container
docker run -d -p 8000:8000 --name datathon-api datathon-api:v1

# Verificar logs
docker logs -f datathon-api

# Verificar saúde
curl http://localhost:8000/health
```

### 7. Rodar Testes

```bash
# Todos os testes com cobertura
pytest --cov=src --cov=app --cov-report=html

# Apenas testes rápidos (sem integração)
pytest tests/ -k "not integration" --tb=short

# Verificar cobertura mínima
pytest --cov-fail-under=80
```

Relatório de cobertura: `htmlcov/index.html`

---

## Estrutura do Projeto

```
datathonfiap/
├── app/                    # API FastAPI
│   ├── main.py            # Endpoints (health, metadata, predict)
│   ├── config.py          # Configurações de ambiente
│   ├── logging_config.py  # Logging estruturado JSON
│   ├── model_loader.py    # Carregamento de modelo
│   ├── drift_store.py     # Monitoramento de drift
│   └── schema.py          # Schemas Pydantic
├── src/                   # Código-fonte do pipeline
│   ├── config.py          # Configurações globais
│   ├── make_dataset.py    # Pipeline de dados
│   ├── data_quality.py    # Checks de qualidade
│   ├── preprocessing.py   # Limpeza e transformação
│   ├── feature_engineering.py  # Criação de features
│   ├── train.py           # Treino do modelo
│   ├── evaluate.py        # Avaliação e métricas
│   ├── model_card.py      # Geração de model card
│   └── utils.py           # Utilitários
├── tests/                 # Testes automatizados (156 testes, 85% coverage)
│   ├── test_smoke.py      # Testes de smoke básicos
│   ├── test_api_integration.py  # Testes de integração da API
│   ├── test_model_loader.py     # Testes do carregador de modelo
│   ├── test_drift_store.py      # Testes de drift monitoring
│   ├── test_schema.py           # Testes de validação
│   ├── test_logging.py          # Testes de logging
│   └── ...
├── artifacts/             # Artefatos do modelo
│   ├── model_v1.joblib    # Modelo serializado
│   ├── model_metadata_v1.json  # Metadata (versão, threshold, métricas)
│   ├── model_signature_v1.json # Assinatura de features
│   └── model_report_v1.md      # Relatório de avaliação
├── data/                  # Datasets (não versionado)
│   ├── raw/              # Dados originais
│   ├── processed/        # Dados processados
│   └── reports/          # Relatórios de qualidade
├── logs/                  # Logs de execução
│   └── drift_events.jsonl # Eventos de drift (sem PII)
├── docs/                  # Documentação técnica
├── notebooks/             # Jupyter notebooks para EDA
├── Dockerfile            # Containerização
├── .dockerignore         # Exclusões do Docker
├── requirements.txt      # Dependências Python
└── pytest.ini            # Configuração pytest
```

---

## API Endpoints

### `GET /health`

Verifica status da API e modelo carregado.

**Response** (200):
```json
{
  "status": "healthy",
  "model_loaded": true,
  "version": "v1.1.0"
}
```

### `GET /metadata`

Retorna metadata do modelo (sem informações sensíveis).

**Response** (200):
```json
{
  "model_version": "v1.1.0",
  "threshold": 0.040221,
  "expected_features": ["fase_2023", "iaa_2023", "ian_2023", ...],
  "feature_count": 15
}
```

### `POST /predict`

Prediz risco de defasagem escolar para um ou mais estudantes.

**Request**:
```json
{
  "instances": [
    {
      "fase_2023": 3.0,
      "iaa_2023": 6.5,
      "ian_2023": 7.2,
      "ida_2023": 5.8,
      "idade_2023": 14,
      "ieg_2023": 6.0,
      "instituicao_2023": 1,
      "ipp_2023": 7.5,
      "ips_2023": 8.0,
      "ipv_2023": 6.2,
      "max_indicador": 8.0,
      "media_indicadores": 6.8,
      "min_indicador": 5.0,
      "range_indicadores": 3.0,
      "std_indicadores": 0.9
    }
  ]
}
```

**Response** (200):
```json
{
  "predictions": [
    {
      "risk_score": 0.72,
      "risk_label": 1,
      "threshold_used": 0.040221
    }
  ],
  "model_version": "v1.1.0",
  "processing_time_ms": 12.5,
  "request_id": "abc123"
}
```

**Notas**:
- `risk_score`: probabilidade de defasagem (0.0 a 1.0)
- `risk_label`: 1 = em risco, 0 = sem risco (baseado no threshold)
- Campos de ID (ra, nome, student_id) são ignorados automaticamente
- Máximo 1000 instâncias por request

---

## Configuração

### Variáveis de Ambiente

| Variável | Default | Descrição |
|----------|---------|-----------|
| `MODEL_PATH` | `artifacts/model_v1.joblib` | Caminho do modelo |
| `METADATA_PATH` | `artifacts/model_metadata_v1.json` | Caminho dos metadados |
| `SIGNATURE_PATH` | `artifacts/model_signature_v1.json` | Caminho da assinatura |
| `PORT` | `8000` | Porta da API |
| `LOG_LEVEL` | `INFO` | Nível de logging |
| `DEFAULT_THRESHOLD` | `0.040` | Threshold padrão |
| `EXTRA_FEATURE_POLICY` | `reject` | Política para features extras |
| `DRIFT_LOG_PATH` | `logs/drift_events.jsonl` | Caminho do log de drift |

### Exemplo .env

```bash
MODEL_PATH=artifacts/model_v1.joblib
METADATA_PATH=artifacts/model_metadata_v1.json
LOG_LEVEL=DEBUG
PORT=8080
```

---

## Docker

### Build

```bash
docker build -t datathon-api:v1 .
```

### Run

```bash
# Modo básico
docker run -p 8000:8000 datathon-api:v1

# Com variáveis de ambiente
docker run -p 8000:8000 \
  -e LOG_LEVEL=DEBUG \
  -e DEFAULT_THRESHOLD=0.05 \
  datathon-api:v1

# Com volume para logs persistentes
docker run -p 8000:8000 \
  -v $(pwd)/logs:/app/logs \
  datathon-api:v1
```

### Health Check

O container inclui health check automático:
```bash
curl http://localhost:8000/health
```

### Docker Compose (exemplo)

```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - LOG_LEVEL=INFO
    volumes:
      - ./logs:/app/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

---

## Logging e Monitoramento

### Formato de Logs

Logs estruturados em JSON para fácil ingestão:

```json
{
  "timestamp": "2026-01-15T10:30:00Z",
  "level": "INFO",
  "logger": "app.main",
  "message": "Prediction request completed",
  "request_id": "abc123",
  "processing_time_ms": 12.5,
  "batch_size": 1
}
```

### Drift Monitoring

Eventos de drift são registrados em `logs/drift_events.jsonl` sem PII:

```json
{
  "timestamp": "2026-01-15T10:30:00Z",
  "event_type": "batch_prediction",
  "batch_size": 10,
  "prediction_summary": {
    "mean_score": 0.45,
    "positive_rate": 0.30
  },
  "feature_stats": {
    "fase_2023": {"mean": 3.2, "std": 1.1}
  }
}
```

---

## Comandos Principais

| Comando | Descrição |
|---------|-----------|
| `python -m src.make_dataset` | Processar dados brutos |
| `python -m src.train` | Treinar modelo |
| `uvicorn app.main:app --reload` | API (desenvolvimento) |
| `pytest --cov` | Rodar testes com cobertura |
| `docker build -t datathon-api .` | Build Docker image |
| `docker run -p 8000:8000 datathon-api` | Run container |

---

## Documentação Técnica

- **[Product Brief](docs/product_brief.md)**: contexto, objetivo, critérios de sucesso
- **[Decision Log](docs/decision_log.md)**: decisões técnicas (target, horizonte, métrica, população)
- **[Data Contract](docs/data_contract.md)**: schema, features, regras de qualidade, leakage watchlist
- **[Model Report](artifacts/model_report_v1.md)**: métricas, comparação de modelos, análise de calibração

---

## Métricas do Modelo (v1.1.0)

| Métrica | Valor |
|---------|-------|
| Recall (classe 1) | 0.75+ |
| Precision (classe 1) | ~0.40 |
| ROC-AUC | ~0.80 |
| Brier Score | ~0.15 |
| Threshold Otimizado | 0.040 |

**Modelo**: Random Forest (100 trees) + Calibração Sigmoid  
**Features**: 15 indicadores educacionais e compostos

---

## Roadmap

### ✅ Fase 0: Diagnóstico
- [x] Product Brief
- [x] Decision Log
- [x] Data Contract
- [x] Skeleton do repo

### ✅ Fase 1: EDA e Limpeza
- [x] Pipeline de dados (`make_dataset.py`)
- [x] Checks de qualidade (`data_quality.py`)
- [x] Validação anti-vazamento

### ✅ Fase 2: Feature Engineering
- [x] Features compostas (agregações de indicadores)
- [x] Normalização de colunas
- [x] Validação de features por ano

### ✅ Fase 3: Modelagem
- [x] Baseline models (LogReg, HistGB, RF)
- [x] Calibração de probabilidades
- [x] Seleção de threshold com constraints
- [x] Model card automático

### ✅ Fase 4: MVP Operável
- [x] API FastAPI com endpoints completos
- [x] Docker containerização
- [x] Logging estruturado (JSON)
- [x] Drift monitoring (sem PII)
- [x] Testes 85%+ coverage (156 testes)
- [x] Documentação atualizada

### 🔜 Fase 5: Produção
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Monitoring dashboard
- [ ] A/B testing framework
- [ ] Fairness analysis por grupos

---

## Desenvolvimento

### Adicionar Nova Feature

1. Implementar em `src/feature_engineering.py`
2. Atualizar `docs/data_contract.md`
3. Adicionar testes em `tests/test_feature_engineering.py`
4. Validar não-vazamento na Leakage Watchlist
5. Re-treinar modelo

### Atualizar Modelo

1. Modificar `src/train.py`
2. Re-treinar: `python -m src.train`
3. Verificar métricas em `artifacts/model_report_v1.md`
4. Atualizar versão em metadata
5. Rebuild Docker image

---

## Contato e Suporte

**Equipe**: {{NOME_EQUIPE}}  
**Repositório**: {{REPO_URL}}  
**Stakeholder**: Associação Passos Mágicos  
**Datathon**: FIAP 2026

---

## Licença

{{TODO: definir licença apropriada com stakeholders}}
