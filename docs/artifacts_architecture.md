# 📦 Arquitetura de Artifacts - Sistema de Versionamento

**Projeto:** Predição de Risco de Defasagem Escolar - Passos Mágicos  
**Última atualização:** 15/01/2026

---

## 📋 Visão Geral

O projeto utiliza uma arquitetura de **duplo armazenamento** de artifacts para separar ambientes de desenvolvimento e produção:

```
Development (artifacts/)     →     Production (models/registry/)
     ↓                                        ↓
  _v1 suffix                            Normalized names
```

---

## 🗂️ Estrutura de Diretórios

### 📁 Development: `artifacts/`

Artifacts gerados pelo pipeline de treinamento (`src/train.py`).

```
artifacts/
├── model_v1.joblib              # Modelo serializado
├── model_metadata_v1.json       # Metadados do modelo
├── model_signature_v1.json      # Schema de input/output
├── metrics_v1.json              # Métricas de avaliação
├── model_comparison.json        # Comparação entre modelos
└── model_report.md              # Relatório de treinamento
```

**Características:**
- ✅ Sufixo `_v1` em todos os artifacts
- ✅ Usado durante desenvolvimento e testes
- ✅ Atualizado a cada execução de `python -m src.train`
- ✅ Referenciado por `app/config.py` (paths padrão)

---

### 📁 Production: `models/registry/`

Artifacts versionados e registrados para produção.

```
models/registry/
├── champion.json                 # Aponta para versão champion
├── v1.0.0/
│   ├── model.joblib             # SEM sufixo _v1
│   ├── model_metadata.json
│   ├── model_signature.json
│   ├── metrics.json
│   └── manifest.json            # Metadata do registro
└── v1.2.0/
    ├── model.joblib
    ├── model_metadata.json
    ├── model_signature.json
    ├── metrics.json
    └── manifest.json
```

**Características:**
- ✅ Nomes **normalizados** (sem sufixo `_v1`)
- ✅ Versionamento semântico (v{MAJOR}.{MINOR}.{PATCH})
- ✅ Imutável após registro
- ✅ Usado em produção via `MODEL_VERSION=champion`

---

## 🔄 Fluxo de Versionamento

### 1️⃣ Desenvolvimento

```bash
# Treinar modelo
python -m src.train --data data/processed/modeling_dataset.parquet

# Gera em artifacts/:
# - model_v1.joblib
# - model_metadata_v1.json
# - model_signature_v1.json
# - metrics_v1.json
```

### 2️⃣ Registro

```bash
# Registrar nova versão
python -m src.registry register --version v1.2.0 --artifacts artifacts/

# Registry copia e renomeia:
# artifacts/model_v1.joblib        → models/registry/v1.2.0/model.joblib
# artifacts/model_metadata_v1.json → models/registry/v1.2.0/model_metadata.json
# artifacts/model_signature_v1.json → models/registry/v1.2.0/model_signature.json
# artifacts/metrics_v1.json        → models/registry/v1.2.0/metrics.json
```

### 3️⃣ Promoção

```bash
# Promover para champion
python -m src.registry promote --version v1.2.0

# Atualiza champion.json:
{
  "version": "v1.2.0",
  "promoted_at": "2026-01-15T10:30:00Z",
  "promoted_by": "ml_engineer"
}
```

### 4️⃣ Deploy

```bash
# API usa champion automaticamente
export MODEL_VERSION=champion
uvicorn app.main:app

# OU versão específica
export MODEL_VERSION=v1.2.0
uvicorn app.main:app
```

---

## 🔧 Mapeamento de Arquivos

O `src/registry.py` define o mapeamento:

```python
artifact_mapping = {
    # Registry Name          : [Development Names (priority order)]
    "model.joblib"           : ["model_v1.joblib", "model.joblib"],
    "model_metadata.json"    : ["model_metadata_v1.json", "model_metadata.json"],
    "model_signature.json"   : ["model_signature_v1.json", "model_signature.json"],
    "metrics.json"           : ["metrics_v1.json", "metrics.json"],
}
```

**Lógica:**
1. Registry tenta primeiro encontrar `model_v1.joblib`
2. Se não existir, tenta `model.joblib` (fallback)
3. Copia para registry com nome normalizado (sem `_v1`)

---

## 📝 Configuração de Paths

### `app/config.py` (Desenvolvimento)

```python
# Paths padrão (desenvolvimento)
MODEL_PATH = Path(os.getenv("MODEL_PATH", "artifacts/model_v1.joblib"))
METADATA_PATH = Path(os.getenv("METADATA_PATH", "artifacts/model_metadata_v1.json"))
SIGNATURE_PATH = Path(os.getenv("SIGNATURE_PATH", "artifacts/model_signature_v1.json"))

# Produção (via registry)
MODEL_VERSION = os.getenv("MODEL_VERSION", "")  # "champion" ou "v1.2.0"
REGISTRY_DIR = Path(os.getenv("REGISTRY_DIR", "models/registry"))
```

### `app/model_loader.py` (Resolução)

```python
def resolve_model_paths():
    """
    Resolve paths baseado em MODEL_VERSION:
    - "" → usa MODEL_PATH direto (desenvolvimento)
    - "champion" → lê champion.json do registry
    - "vX.Y.Z" → usa versão específica do registry
    """
    if not MODEL_VERSION:
        return MODEL_PATH, METADATA_PATH, SIGNATURE_PATH
    
    if MODEL_VERSION == "champion":
        champion_file = REGISTRY_DIR / "champion.json"
        version = json.load(champion_file)["version"]
    else:
        version = MODEL_VERSION
    
    version_dir = REGISTRY_DIR / version
    return (
        version_dir / "model.joblib",
        version_dir / "model_metadata.json",
        version_dir / "model_signature.json"
    )
```

---

## ✅ Boas Práticas

### Durante Desenvolvimento

1. **Sempre use sufixo `_v1`** ao salvar artifacts:
   ```python
   joblib.dump(model, "artifacts/model_v1.joblib")
   ```

2. **Referencie com `_v1`** em testes:
   ```python
   metadata = json.load(open("artifacts/model_metadata_v1.json"))
   ```

### Durante Deploy

1. **Use MODEL_VERSION** em vez de paths diretos:
   ```bash
   export MODEL_VERSION=champion
   docker-compose up -d
   ```

2. **Nunca edite registry manualmente**. Use comandos:
   ```bash
   python -m src.registry register --version vX.Y.Z
   python -m src.registry promote --version vX.Y.Z
   ```

### Versionamento Semântico

```
vMAJOR.MINOR.PATCH

MAJOR: Breaking changes (novo schema, features removidas)
MINOR: Novos recursos, melhorias significativas
PATCH: Bug fixes, ajustes menores
```

**Exemplos:**
- `v1.0.0` → `v1.1.0`: Feature engineering aprimorado (+9 features)
- `v1.1.0` → `v1.2.0`: HistGradientBoosting, 34 features, business rules, deltas temporais
- `v1.2.0` → `v2.0.0`: Mudança de algoritmo (possível CatBoost em produção)

---

## 🔍 Troubleshooting

### Problema: "Modelo não encontrado"

```bash
# Verificar artifacts em desenvolvimento
ls -la artifacts/

# Verificar registry
ls -la models/registry/

# Verificar champion
cat models/registry/champion.json
```

### Problema: "Versão antiga carregada"

```bash
# Verificar variável de ambiente
echo $MODEL_VERSION

# Limpar cache
docker-compose down
docker-compose up -d --force-recreate
```

### Problema: "Artifacts com nomes errados"

```bash
# Registry espera nomes normalizados
# Verificar mapeamento em src/registry.py

# Regenerar artifacts com nomes corretos
python -m src.train --data data/processed/modeling_dataset.parquet
```

---

## 📚 Referências

- [`src/train.py`](../src/train.py) - Gera artifacts com sufixo `_v1`
- [`src/registry.py`](../src/registry.py) - Gerencia versionamento
- [`app/config.py`](../app/config.py) - Configuração de paths
- [`app/model_loader.py`](../app/model_loader.py) - Resolução de versões
- [Model Changelog](model_changelog.md) - Histórico de versões
