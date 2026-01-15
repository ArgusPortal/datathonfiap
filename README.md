# Datathon FIAP - Modelo de Risco de Defasagem Escolar

**Projeto**: Predição de risco de defasagem escolar para estudantes da Associação Passos Mágicos  
**Período**: 2022–2024  
**Status**: Fase 0 (Diagnóstico e Setup)

---

## Visão Geral

Modelo de Machine Learning para identificar estudantes em risco de defasagem escolar (moderada ou severa) usando dados históricos do programa Passos Mágicos. O score permite intervenção preventiva antes da defasagem se consolidar.

**Target**: predição binária t → t+1 (usar dados do ano t para predizer risco no ano t+1)  
**Métrica principal**: Recall da classe positiva ≥ 0.75  
**População**: Fases 0–7 do programa

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
# Estrutura esperada: data/raw/dataset_2022_2024.csv
# Schema: ver docs/data_contract.md
```

### 3. Treinar Modelo (Placeholder)

```bash
python -m src.train --data data/raw/dataset_2022_2024.csv --output models/
```

### 4. Executar API

```bash
uvicorn app.main:app --reload --port 8000
```

Acessar: http://localhost:8000/docs (Swagger UI)

### 5. Rodar Testes

```bash
pytest --cov=src --cov=app --cov-report=html
```

Relatório de cobertura: `htmlcov/index.html`

---

## Estrutura do Projeto

```
datathonfiap/
├── app/                    # API FastAPI
│   ├── main.py            # Endpoints
│   └── model/             # Artefatos do modelo
│       └── model_metadata.json
├── src/                   # Código-fonte do pipeline
│   ├── config.py          # Configurações
│   ├── preprocessing.py   # Limpeza e transformação
│   ├── feature_engineering.py  # Criação de features
│   ├── train.py           # Treino do modelo
│   └── evaluate.py        # Avaliação e métricas
├── tests/                 # Testes automatizados
│   └── test_smoke.py      # Testes básicos
├── notebooks/             # Jupyter notebooks para EDA
├── docs/                  # Documentação técnica
│   ├── product_brief.md   # Contexto e objetivo
│   ├── decision_log.md    # Decisões técnicas (D1-D4)
│   └── data_contract.md   # Schema e regras de qualidade
├── data/                  # Datasets (não versionado)
│   ├── raw/              # Dados originais
│   ├── processed/        # Dados processados
│   └── .gitkeep
├── models/                # Modelos treinados (não versionado)
│   └── .gitkeep
├── requirements.txt       # Dependências Python
├── pytest.ini            # Configuração pytest
├── Dockerfile            # Containerização
└── README.md             # Este arquivo
```

---

## Comandos Principais

| Comando | Descrição |
|---------|-----------|
| `python -m src.train` | Treinar modelo |
| `uvicorn app.main:app --reload` | Subir API (dev) |
| `pytest --cov` | Rodar testes com cobertura |
| `black src/ app/ tests/` | Formatar código |
| `flake8 src/ app/` | Linter |
| `docker build -t datathon-api .` | Build Docker image |

---

## Documentação Técnica

- **[Product Brief](docs/product_brief.md)**: contexto, objetivo, critérios de sucesso
- **[Decision Log](docs/decision_log.md)**: decisões técnicas (target, horizonte, métrica, população)
- **[Data Contract](docs/data_contract.md)**: schema, features, regras de qualidade, leakage watchlist

---

## API Endpoints

### `POST /predict`

Prediz risco de defasagem escolar para um estudante.

**Request**:
```json
{
  "estudante_id": "{{EXAMPLE_ID}}",
  "ano_base": 2024,
  "features": {
    "inde_ano_t": 5.2,
    "ian_ano_t": 3.8,
    "taxa_presenca_ano_t": 0.85,
    "fase_programa": 3,
    "{{OUTRAS_FEATURES}}": "{{VALORES}}"
  }
}
```

**Response**:
```json
{
  "score": 0.72,
  "classe_predita": 1,
  "threshold": 0.5,
  "versao_modelo": "v0.1.0",
  "timestamp": "2026-01-15T10:30:00Z"
}
```

### `GET /health`

Verifica status da API.

**Response**:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "version": "0.1.0"
}
```

---

## Desenvolvimento

### Adicionar Nova Feature

1. Implementar em `src/feature_engineering.py`
2. Atualizar `docs/data_contract.md` (seção Features Candidatas)
3. Adicionar testes em `tests/test_feature_engineering.py`
4. Validar não-vazamento na Leakage Watchlist

### Alterar Modelo

1. Modificar `src/train.py`
2. Re-treinar: `python -m src.train`
3. Avaliar: `python -m src.evaluate`
4. Atualizar metadata em `app/model/model_metadata.json`
5. Verificar testes não quebram

### CI/CD (Futuro)

{{TODO: configurar GitHub Actions para rodar pytest em PRs}}
{{TODO: configurar deployment automático da API}}

---

## Roadmap

### Fase 0 (Atual): Diagnóstico ✅
- [x] Product Brief
- [x] Decision Log (D1–D4)
- [x] Data Contract
- [x] Skeleton do repo
- [x] Testes básicos (pytest)

### Fase 1: EDA e Limpeza
{{TODO: análise exploratória completa}}
{{TODO: tratamento de missing values}}
{{TODO: validação de qualidade dos dados}}

### Fase 2: Feature Engineering
{{TODO: features longitudinais}}
{{TODO: agregações temporais}}
{{TODO: validação anti-vazamento}}

### Fase 3: Modelagem
{{TODO: baseline model}}
{{TODO: tuning de hiperparâmetros}}
{{TODO: validação temporal}}

### Fase 4: Avaliação e Interpretabilidade
{{TODO: análise de erros}}
{{TODO: SHAP/feature importance}}
{{TODO: fairness check por grupos}}

### Fase 5: Deploy e Monitoramento
{{TODO: containerização completa}}
{{TODO: logging estruturado}}
{{TODO: monitoramento de drift}}

---

## Contato e Suporte

**Equipe**: {{NOME_EQUIPE}}  
**Repositório**: {{REPO_URL}}  
**Stakeholder**: Associação Passos Mágicos  
**Datathon**: FIAP 2026

---

## Licença

{{TODO: definir licença apropriada com stakeholders}}
