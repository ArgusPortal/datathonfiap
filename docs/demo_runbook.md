# Demo Runbook — Datathon FIAP 2026

Guia rápido para demonstrar as 4 capacidades principais do projeto.

---

## Demo 1: Local (sem Docker)

```bash
# 1. Ativar ambiente
python -m venv venv && venv\Scripts\activate  # Windows
pip install -r requirements.txt

# 2. Subir API
uvicorn app.main:app --port 8000

# 3. Testar predição (novo terminal)
curl -X POST http://localhost:8000/predict ^
  -H "Content-Type: application/json" ^
  -d "{\"instances\":[{\"fase_2023\":3,\"iaa_2023\":6.5,\"ian_2023\":7.2,\"ida_2023\":5.8,\"idade_2023\":14,\"ieg_2023\":6,\"instituicao_2023\":1,\"ipp_2023\":7.5,\"ips_2023\":8,\"ipv_2023\":6.2,\"max_indicador\":8,\"media_indicadores\":6.8,\"min_indicador\":5,\"range_indicadores\":3,\"std_indicadores\":0.9}]}"
```

**Esperado**: `{"predictions":[{"risk_score":0.75,"risk_label":1,...}]}`

---

## Demo 2: Docker

```bash
# 1. Build
docker build -t datathon-api:v1 .

# 2. Run
docker run -d -p 8000:8000 --name datathon-test datathon-api:v1

# 3. Health check
curl http://localhost:8000/health

# 4. Predição
curl -X POST http://localhost:8000/predict -H "Content-Type: application/json" ^
  -d "{\"instances\":[{\"fase_2023\":3,\"iaa_2023\":6.5,\"ian_2023\":7.2,\"ida_2023\":5.8,\"idade_2023\":14,\"ieg_2023\":6,\"instituicao_2023\":1,\"ipp_2023\":7.5,\"ips_2023\":8,\"ipv_2023\":6.2,\"max_indicador\":8,\"media_indicadores\":6.8,\"min_indicador\":5,\"range_indicadores\":3,\"std_indicadores\":0.9}]}"

# 5. Cleanup
docker stop datathon-test && docker rm datathon-test
```

---

## Demo 3: Testes e Cobertura

```bash
# Rodar testes com cobertura
pytest tests/ --cov=src --cov=app --cov=monitoring --cov-report=term-missing

# Esperado: 368 passed, coverage >= 80%
```

**Evidência**: relatório mostra `TOTAL ... 81%` ou superior.

---

## Demo 4: Monitoramento e Drift

```bash
# 1. Gerar algumas inferências (com API rodando)
curl -X POST http://localhost:8000/predict -H "Content-Type: application/json" ^
  -d "{\"instances\":[{\"fase_2023\":2,\"iaa_2023\":5,\"ian_2023\":5,\"ida_2023\":5,\"idade_2023\":12,\"ieg_2023\":5,\"instituicao_2023\":1,\"ipp_2023\":5,\"ips_2023\":5,\"ipv_2023\":5,\"max_indicador\":6,\"media_indicadores\":5,\"min_indicador\":4,\"range_indicadores\":2,\"std_indicadores\":0.5}]}"

# 2. Gerar baseline (se não existir)
python -m monitoring.build_baseline --model_version v1.1.0 --signature artifacts/model_signature_v1.json --source data/processed/dataset_train_2023.parquet

# 3. Gerar drift report
python -m monitoring.drift_report --model_version v1.1.0 --last_n_days 7

# 4. Abrir HTML
start monitoring\reports\drift_report_*.html
```

**Evidência**: HTML com tabela de features, status (verde/amarelo/vermelho), PSI values.
