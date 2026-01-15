# RUNBOOK - Comandos de Execução

## Fase 0: Diagnóstico - Projeto Datathon FIAP

Este documento contém os comandos para executar todas as operações do projeto.

---

## Setup Inicial

### 1. Criar Ambiente Virtual
```bash
py -m venv venv
```

### 2. Ativar Ambiente Virtual

**Windows (CMD):**
```bash
venv\Scripts\activate
```

**Windows (PowerShell):**
```bash
venv\Scripts\Activate.ps1
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 3. Instalar Dependências
```bash
pip install -r requirements.txt
```

---

## Testes

### Rodar Todos os Testes
```bash
pytest -v
```

### Rodar Testes com Cobertura
```bash
pytest --cov=src --cov=app --cov-report=html
```

Relatório de cobertura: abrir `htmlcov/index.html`

### Rodar Teste Específico
```bash
pytest tests/test_smoke.py::test_api_health_endpoint -v
```

---

## API (FastAPI)

### Iniciar API em Modo Desenvolvimento
```bash
uvicorn app.main:app --reload --port 8000
```

### Acessar Documentação Interativa
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Testar Endpoint de Health Check
```bash
curl http://localhost:8000/health
```

### Testar Endpoint de Predição
```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "estudante_id": "test_001",
    "ano_base": 2024,
    "features": {
      "inde_ano_t": 5.5,
      "ian_ano_t": 4.8,
      "taxa_presenca_ano_t": 0.85,
      "fase_programa": 3
    }
  }'
```

---

## Treino de Modelo

### Fase 1: Gerar Dataset de Modelagem
```bash
python -m src.make_dataset --input "data/raw/PEDE_PASSOS_DATASET_FIAP.xlsx" --output data/processed/
```

Artefatos gerados:
- `data/processed/modeling_dataset.parquet`
- `data/processed/data_quality_report.json`

### Fase 2: Treinar Modelo com Baselines
```bash
python -m src.train --data data/processed/modeling_dataset.parquet --artifacts artifacts/
```

Artefatos gerados:
- `artifacts/model.joblib` - Pipeline sklearn serializado
- `artifacts/metrics.json` - Métricas de todos os baselines
- `artifacts/model_metadata.json` - Metadados do modelo (versão, seed, features)
- `artifacts/model_signature.json` - Schema de entrada/saída para API

### Avaliar Modelo
```bash
python -m src.evaluate --model artifacts/model.joblib --data data/processed/modeling_dataset.parquet
```

---

## Docker

### Build da Imagem
```bash
docker build -t datathon-api:latest .
```

### Executar Container
```bash
docker run -p 8000:8000 datathon-api:latest
```

### Executar com Volume (para desenvolvimento)
```bash
docker run -p 8000:8000 -v $(pwd)/models:/app/models datathon-api:latest
```

---

## Qualidade de Código

### Formatar Código com Black
```bash
black src/ app/ tests/
```

### Verificar com Flake8
```bash
flake8 src/ app/
```

### Verificar Tipos com MyPy
```bash
mypy src/ app/
```

---

## Estrutura de Dados

### Verificar Estrutura Esperada
Ver [docs/data_contract.md](docs/data_contract.md)

### Colocar Dados no Projeto
```bash
# Colocar arquivo CSV em:
data/raw/dataset_2022_2024.csv
```

---

## Jupyter Notebooks

### Iniciar Jupyter Lab
```bash
jupyter lab
```

### Iniciar Jupyter Notebook
```bash
jupyter notebook
```

Os notebooks devem ser salvos em `notebooks/`

---

## Git

### Inicializar Repositório (se necessário)
```bash
git init
git add .
git commit -m "Initial commit - Phase 0 setup"
```

### Criar Branch para Nova Feature
```bash
git checkout -b feature/nova-feature
```

---

## Troubleshooting

### Problema: Módulo não encontrado
**Solução:** Certifique-se que o venv está ativo
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### Problema: Porta 8000 já em uso
**Solução:** Use outra porta
```bash
uvicorn app.main:app --reload --port 8001
```

### Problema: Testes falhando
**Solução:** Verifique se todas as dependências foram instaladas
```bash
pip install -r requirements.txt
```

---

## Verificação Rápida (Smoke Test)

Execute este comando para verificar se tudo está funcionando:

```bash
pytest tests/test_smoke.py -v && echo "✓ Projeto configurado corretamente!"
```

---

## Status da Fase 0

- [x] Product Brief criado
- [x] Decision Log (D1-D4) documentado
- [x] Data Contract definido
- [x] Skeleton do repositório criado
- [x] Requirements.txt configurado
- [x] README.md completo
- [x] API FastAPI funcionando
- [x] Pytest rodando (14/14 testes passando)
- [x] Cobertura de testes: 53%
- [ ] Dados reais carregados (aguardando dataset)
- [ ] Modelo treinado (aguardando dados)

---

## Status da Fase 1

- [x] Dataset PEDE_PASSOS carregado
- [x] Data Quality Checks implementados (anti-leakage)
- [x] Target `em_risco_2024` definido (defasagem < 0)
- [x] Pipeline `make_dataset.py` funcional
- [x] 35 testes passando

---

## Status da Fase 2

- [x] Preprocessing com ColumnTransformer (sklearn)
- [x] Feature Engineering (media_indicadores, min_indicador, std_indicadores)
- [x] 3 Baselines comparados (Naive, Logistic, RF)
- [x] Threshold selection (max_recall)
- [x] Artefatos serializados (model.joblib, metrics.json, ...)
- [x] **52 testes passando, 79% cobertura**

---

## Status da Fase 3

- [x] Múltiplos candidatos comparados (logreg, hist_gb, rf)
- [x] Calibração sigmoid com CalibratedClassifierCV
- [x] Threshold selecionado em validação interna
- [x] model_v1.joblib pronto para API
- [x] model_report.md gerado automaticamente
- [x] **69 testes passando, 81% cobertura**

**Métricas do Modelo v1 (RandomForest calibrado):**

| Métrica | Validação | Teste |
|---------|-----------|-------|
| **Recall** | 1.00 | **1.00** ✅ |
| Precision | 0.40 | 0.41 |
| F2 | 0.77 | 0.77 |
| PR-AUC | 0.85 | 0.85 |
| Brier | - | 0.11 |
| **Threshold** | - | **0.040** |

### Comandos Fase 3:

```bash
# Treinar modelo v1 com calibração
python -m src.train --data data/processed/modeling_dataset.parquet --artifacts artifacts/ --calibration sigmoid

# Rodar todos os testes
pytest tests/ -v --tb=short

# Verificar artefatos
ls artifacts/model_v1.joblib artifacts/metrics_v1.json artifacts/model_report.md
```

---

## Próximos Passos (Fase 4)

1. Integrar model_v1.joblib na API FastAPI
2. Implementar endpoint /predict usando model_signature_v1.json
3. Adicionar validação de input com Pydantic
4. Deploy Docker com modelo embarcado

---

**Última Atualização:** Janeiro 2026 (Fase 3)
