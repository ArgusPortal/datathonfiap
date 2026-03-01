---
applyTo: "Dockerfile*,docker-compose*.yml,.github/workflows/**"
---

# Docker & CI/CD — Convenções Passos Mágicos

- Dockerfile.fullstack: 3 stages (node → python builder → python runtime)
- Sempre passar `--build-arg GIT_SHA=$(git rev-parse --short HEAD)`
- Nginx serve frontend + proxy /api → uvicorn
- Supervisor gerencia nginx + uvicorn
- CI: pytest ≥80% coverage, Black, Flake8, Mypy, frontend type-check
- Não rodar containers como root
- Limpar caches pip/npm no final de cada stage
- Health probes: `/health` (liveness), `/ready` (readiness)
