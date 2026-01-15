# Rollback Policy

## Quando fazer rollback

1. **Drift crítico** (PSI > 0.25) em feature principal sem explicação
2. **Erro de produção** (5xx > 1% por 10 min)
3. **Queda de performance** (recall < 0.70 quando labels disponíveis)
4. **Bug em nova versão** detectado pós-deploy

## Como executar

```bash
# 1. Identificar versão anterior
python -m src.registry list --registry models/registry

# 2. Executar rollback
python -m src.registry rollback --version vX.Y.Z --reason "descrição curta"

# 3. Reiniciar API (ou redeploy Docker)
docker restart datathon-api
# ou
docker run -d -p 8000:8000 -e MODEL_VERSION=champion datathon-api:v1
```

## Tempo esperado

- Rollback: < 2 minutos
- Verificação: /health + /predict teste

## Responsabilidades

- **Quem decide**: Tech Lead ou On-call
- **Quem executa**: Engenheiro de plantão
- **Quem valida**: QA ou segundo engenheiro
