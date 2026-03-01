---
description: "Adicionar testes pytest para um módulo existente"
mode: "agent"
tools:
  - search
  - codebase
  - editFiles
  - runInTerminal
---

Adicione testes pytest para o módulo especificado, seguindo o padrão do projeto:

1. Identifique o módulo alvo e analise suas funções/classes públicas
2. Crie/atualize `tests/test_{modulo}.py`
3. Para cada função pública, crie testes para:
   - **Happy path**: Input válido → output esperado
   - **Edge cases**: Listas vazias, None, valores limítrofes (0, 10)
   - **Erros**: Inputs inválidos → exceção esperada
4. Use markers: `@pytest.mark.unit`, `@pytest.mark.smoke`, `@pytest.mark.integration`
5. Para API endpoints: use `httpx.AsyncClient` com `ASGITransport`
6. Para ML: use seed=42 para reprodutibilidade
7. Rode os testes: `pytest tests/test_{modulo}.py -v`
8. Verifique coverage: `pytest tests/test_{modulo}.py --cov=src --cov=app -v`

Meta: coverage ≥ 80% para o módulo.
