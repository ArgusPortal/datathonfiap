---
description: "Criar novo endpoint FastAPI completo com schema, testes e integração frontend"
mode: "agent"
tools:
  - search
  - codebase
  - editFiles
  - runInTerminal
---

Crie um novo endpoint FastAPI seguindo o padrão do projeto Passos Mágicos:

1. **Schema** (`app/schema.py`): Adicione os modelos Pydantic de request/response
2. **Route** (`app/main.py`): Implemente o endpoint com:
   - Documentação OpenAPI (summary, description, tags)
   - Error handling com HTTPException
   - Logging via `observability.py`
   - Métricas via `metrics.py`
3. **Tipos TS** (`frontend/src/types/index.ts`): Adicione interfaces matching
4. **Cliente API** (`frontend/src/services/api.ts`): Adicione método no cliente
5. **Teste** (`tests/test_main.py`): Adicione teste com httpx.AsyncClient

Siga as convenções: Black 120 chars, type hints, docstrings Google style.
