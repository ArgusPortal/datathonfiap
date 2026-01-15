# Predição de Risco de Defasagem Escolar — Passos Mágicos

**Datathon FIAP 2026** | Modelo ML + API + Docker + Monitoramento

---

## 1. Visão Geral

### Problema
Crianças atendidas pela ONG Passos Mágicos podem entrar em **defasagem escolar** (atraso moderado/severo). Identificar esse risco antecipadamente permite intervenção preventiva.

### Solução
Pipeline de Machine Learning que:
- Treina modelo com dados históricos (2022–2023) para predizer risco em t+1
- Expõe API REST para integração com sistemas da ONG
- Monitora drift em produção para garantir qualidade contínua

### Stack
- **Linguagem**: Python 3.11+
- **ML**: scikit-learn, pandas, numpy, joblib
- **API**: FastAPI, uvicorn, pydantic
- **Testes**: pytest, pytest-cov (84% coverage)
- **Deploy**: Docker
- **Monitoramento**: logs JSON, inference store, drift report HTML

---

## 2. Estrutura do Projeto

```
datathonfiap/
├── app/                 # API FastAPI (/health, /metadata, /predict)
├── src/                 # Pipeline ML (make_dataset, train, evaluate)
├── tests/               # 200 testes automatizados
├── artifacts/           # Modelo e metadados (model_v1.joblib)
├── monitoring/          # Baseline, inference store, drift report
├── data/                # Dados brutos e processados (não versionado)
├── docs/                # Documentação técnica e runbooks
├── Dockerfile           # Containerização
└── requirements.txt     # Dependências
```

---

## 3. Como Rodar (Local)

```bash
# 1. Setup
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt

# 2. Treinar modelo (opcional, artefatos já existem)
python -m src.make_dataset
python -m src.train

# 3. Subir API
uvicorn app.main:app --port 8000
```

Acesse: http://localhost:8000/docs

---

## 4. Como Rodar (Docker)

```bash
# Build
docker build -t datathon-api:v1 .

# Run
docker run -d -p 8000:8000 --name datathon-api datathon-api:v1

# Verificar
curl http://localhost:8000/health
```

---

## 5. Endpoints e Exemplos

### GET /health
```bash
curl http://localhost:8000/health
```
```json
{"status":"healthy","model_loaded":true,"model_version":"v1.1.0"}
```

### GET /metadata
```bash
curl http://localhost:8000/metadata
```
```json
{"model_version":"v1.1.0","threshold":0.040221,"expected_features":["fase_2023","iaa_2023",...]}
```

### POST /predict (single)
```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"instances":[{"fase_2023":3,"iaa_2023":6.5,"ian_2023":7.2,"ida_2023":5.8,"idade_2023":14,"ieg_2023":6,"instituicao_2023":1,"ipp_2023":7.5,"ips_2023":8,"ipv_2023":6.2,"max_indicador":8,"media_indicadores":6.8,"min_indicador":5,"range_indicadores":3,"std_indicadores":0.9}]}'
```
```json
{"predictions":[{"risk_score":0.757,"risk_label":1,"model_version":"v1.1.0"}],"request_id":"abc123","processing_time_ms":12.5}
```

### POST /predict (batch)
```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"instances":[{"fase_2023":3,"iaa_2023":6.5,"ian_2023":7.2,"ida_2023":5.8,"idade_2023":14,"ieg_2023":6,"instituicao_2023":1,"ipp_2023":7.5,"ips_2023":8,"ipv_2023":6.2,"max_indicador":8,"media_indicadores":6.8,"min_indicador":5,"range_indicadores":3,"std_indicadores":0.9},{"fase_2023":2,"iaa_2023":5,"ian_2023":5,"ida_2023":5,"idade_2023":12,"ieg_2023":5,"instituicao_2023":1,"ipp_2023":5,"ips_2023":5,"ipv_2023":5,"max_indicador":6,"media_indicadores":5,"min_indicador":4,"range_indicadores":2,"std_indicadores":0.5}]}'
```

---

## 6. Pipeline de ML

1. **Ingest**: leitura do dataset PEDE + normalização de colunas
2. **Target**: construção do target binário (defasagem t+1)
3. **Features**: 15 indicadores educacionais + agregações
4. **Split**: validação temporal (treino 2023, validação 2024)
5. **Treino**: Random Forest + calibração sigmoid
6. **Threshold**: otimizado para recall ≥ 0.75 (threshold = 0.040)
7. **Serialização**: joblib + metadata JSON

---

## 7. Qualidade (Testes)

```bash
pytest tests/ --cov=src --cov=app --cov=monitoring --cov-report=term-missing
```

**Resultado**: 200 testes, 84% cobertura

| Métrica | Valor |
|---------|-------|
| Testes totais | 200 |
| Cobertura | 84% |
| Meta mínima | 80% |

---

## 8. Monitoramento e Drift

### Logs Estruturados
- Formato: JSON
- Campos: timestamp, request_id, latency_ms, status_code
- **Não logamos**: IDs pessoais (ra, nome, student_id)

### Inference Store
- Local: `monitoring/inference_store/`
- Formato: Parquet (partições diárias)
- Modo: aggregate_only (sem dados brutos)

### Baseline
```bash
python -m monitoring.build_baseline \
  --model_version v1.1.0 \
  --signature artifacts/model_signature_v1.json \
  --source data/processed/dataset_train_2023.parquet
```

### Drift Report
```bash
python -m monitoring.drift_report --model_version v1.1.0 --last_n_days 7
# Abre: monitoring/reports/drift_report_YYYYMMDD.html
```

| Status | PSI | Ação |
|--------|-----|------|
| 🟢 Verde | < 0.10 | Normal |
| 🟡 Amarelo | 0.10–0.25 | Investigar |
| 🔴 Vermelho | > 0.25 | Considerar retrain |

---

## 9. Link da API

**Deploy local**: `http://localhost:8000`

Para testar:
```bash
docker run -d -p 8000:8000 datathon-api:v1
curl http://localhost:8000/health
```

> **Nota**: API cloud não configurada. Use Docker para deploy em ambiente de produção.

---

## 10. Licença e Privacidade

- Dados fornecidos pela Passos Mágicos exclusivamente para o Datathon
- **Não armazenamos PII** (nomes, RAs, IDs)
- Logs contêm apenas estatísticas agregadas
- Inference store opera em modo `aggregate_only`
- Modelo não deve ser usado fora do contexto autorizado
- Respeitar LGPD e políticas da instituição

---

## Métricas do Modelo (v1.1.0)

| Métrica | Valor |
|---------|-------|
| Recall (classe 1) | ≥ 0.75 |
| Precision | ~0.40 |
| ROC-AUC | ~0.80 |
| Threshold | 0.040 |

---

## 11. Operação Contínua (Fase 7 — MLOps)

### Model Registry
Versionamento folder-based em `models/registry/vX.Y.Z/`:
```bash
# Registrar nova versão
python -m src.registry register --version v1.2.0 \
  --model artifacts/model.joblib \
  --metadata artifacts/metadata.json \
  --signature artifacts/signature.json

# Promover para champion
python -m src.registry promote --version v1.2.0

# Rollback para versão anterior
python -m src.registry rollback --version v1.1.0

# Listar versões
python -m src.registry list
```

### Retraining
```bash
# Treinar novo challenger e comparar com champion
python -m src.retrain --new_version v1.2.0 \
  --data data/processed/dataset_2024.parquet \
  --registry models/registry

# Guardrails automáticos: recall delta ≤ 2%, precision delta ≤ 5%
```

### CI/CD (GitHub Actions)
- **CI** (`.github/workflows/ci.yml`): pytest + coverage ≥ 80%
- **CD** (`.github/workflows/cd.yml`): Docker build + push GHCR

```bash
# Rodar CI local
pytest tests/ --cov=src --cov=app --cov=monitoring --cov-fail-under=80
```

### Schema Validation
```bash
# Validar dados de inferência
python -c "from src.schema_validation import validate_inference_batch; validate_inference_batch(df)"

# Validar dados de treino
python -c "from src.schema_validation import validate_training_data; validate_training_data(df)"
```

### Performance Drift (com Labels)
```bash
# Gera relatório de performance quando labels disponíveis (lag ~90 dias)
python -m monitoring.performance_drift --window 30
```

### Documentação Adicional
- [Data Contract v2](docs/data_contract_v2.md) — Schema com validações
- [Retraining Policy](docs/retraining_policy.md) — Triggers e processo
- [Labels Ingestion](docs/labels_ingestion.md) — Como ingerir ground truth
- [Ops Runbook v2](docs/ops_runbook_v2.md) — Procedimentos operacionais

---

## Documentação

- [Product Brief](docs/product_brief.md)
- [Data Contract](docs/data_contract.md)
- [Decision Log](docs/decision_log.md)
- [Model Report](artifacts/model_report_v1.md)
- [Monitoring Runbook](docs/monitoring_runbook.md)
- [Demo Runbook](docs/demo_runbook.md)
- [Video Script](docs/video_script.md)

---

**Equipe**: {{TEAM_NAME}}  
**Repositório**: {{GITHUB_REPO_URL}}  
**Datathon FIAP 2026** — Associação Passos Mágicos
