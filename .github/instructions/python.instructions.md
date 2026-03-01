---
applyTo: "**/*.py"
---

# Python — Convenções Passos Mágicos

- **Python 3.11**, formatter Black (120 chars), linter Flake8, type checker Mypy
- Imports: stdlib → third-party → local (isort-compatível)
- Docstrings: Google style, português para descrições, inglês para APIs
- Env vars: via `os.getenv()` com defaults em `app/config.py`
- Logging: `logging.getLogger(__name__)`, JSON estruturado em produção
- Testes: pytest, coverage ≥ 80%, fixtures locais por arquivo
- Type hints obrigatórios em funções públicas
- Sem `print()` em código de produção — usar logger
- Seed=42 para reprodutibilidade em ML
- LGPD: nunca logar dados pessoais (RA, CPF, nome)
