---
description: "Diagnosticar e resolver problema no sistema (debug completo)"
mode: "agent"
tools:
  - search
  - codebase
  - editFiles
  - runInTerminal
  - terminalLastCommand
  - problems
  - fetch
---

Diagnostique e resolva o problema reportado seguindo o fluxo:

1. **Reproduzir**: Identifique os arquivos e endpoints envolvidos
2. **Investigar**: Use search e read para entender o contexto do erro
3. **Root cause**: Analise logs (`/api/audit/recent`, `/api/metrics`), stack traces, state
4. **Fix**: Implemente a correção mínima necessária
5. **Testar**: Rode `pytest tests/ -x` para garantir que nada quebrou
6. **Verificar**: Confirme que o problema foi resolvido

Arquitetura do projeto:
- Backend: `app/` (FastAPI com modules para security, metrics, audit, drift, privacy)
- Frontend: `frontend/src/` (React + TypeScript + shadcn/ui)
- ML Pipeline: `src/` (train, evaluate, feature engineering, registry)
- Testes: `tests/` (450+ testes, coverage ≥ 80%)

Logs e diagnóstico:
- `GET /health` — Status da API
- `GET /metrics` — Contadores e latência
- `GET /slo` — SLO compliance
- `GET /drift/status` — PSI drift
- `GET /audit/recent` — Últimas inferências
