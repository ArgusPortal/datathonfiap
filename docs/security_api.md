# API Security Documentation

## Autenticação

### API Key Authentication

A API usa autenticação via API Key para endpoints protegidos.

**Headers requeridos:**
```
X-API-Key: <your-api-key>
```

**Endpoints públicos (sem autenticação):**
- `GET /health` - Health check
- `GET /docs` - Swagger UI
- `GET /openapi.json` - OpenAPI schema
- `GET /redoc` - ReDoc documentation

**Endpoints protegidos:**
- `GET /metadata` - Model metadata
- `POST /predict` - Predictions
- `GET /metrics` - Metrics
- `GET /ready` - Readiness check

### Configuração

```bash
# Definir API keys (comma-separated para múltiplas keys)
export API_KEYS="key1,key2,key3"

# Modo desenvolvimento (sem autenticação)
export API_KEYS=""
```

### Exemplos de uso

```bash
# Health check (público)
curl http://localhost:8000/health

# Prediction (autenticado)
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"instances": [{"turnover": 0.15, "headcount": 100, ...}]}'
```

### Respostas de erro

| Código | Erro | Descrição |
|--------|------|-----------|
| 401 | UNAUTHORIZED | API key ausente ou inválida |
| 429 | RATE_LIMITED | Limite de requisições excedido |
| 413 | PAYLOAD_TOO_LARGE | Body excede limite de tamanho |

---

## Rate Limiting

### Configuração

| Parâmetro | Variável de ambiente | Default | Descrição |
|-----------|---------------------|---------|-----------|
| RPM | `RATE_LIMIT_RPM` | 60 | Requisições por minuto por API key |
| Body size | `MAX_BODY_BYTES` | 262144 | Tamanho máximo do body (256KB) |
| Timeout | `REQUEST_TIMEOUT_MS` | 3000 | Timeout de requisição (3s) |

### Headers de resposta

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
Retry-After: 60 (quando rate limited)
```

### Algoritmo

Token Bucket com reposição contínua:
- Bucket inicial: `RATE_LIMIT_RPM` tokens
- Reposição: `RPM / 60` tokens/segundo
- Cada request consome 1 token
- Rate limit aplicado por API key no endpoint `/predict`

### Escalonamento

Para deployments multi-réplica, considerar:
- Redis para estado compartilhado do rate limiter
- Load balancer com sticky sessions por API key
- Rate limiting no API Gateway (Kong, AWS API Gateway)

---

## Validação de Input

### Tamanho do body

Requisições com `Content-Length > MAX_BODY_BYTES` são rejeitadas com 413.

### Validação de features

- Features obrigatórias são validadas contra schema do modelo
- Features extras podem ser rejeitadas ou ignoradas (config: `EXTRA_FEATURE_POLICY`)
- Tipos de dados são validados (numéricos, strings categóricas)

### Batch limits

- Máximo de instâncias por request: 1000
- Tamanho total respeitando `MAX_BODY_BYTES`

---

## Headers de Segurança

Todas as respostas incluem:

```
X-Request-ID: <uuid>  # Para rastreabilidade
```

### Recomendações para proxy reverso

Adicionar headers via nginx/ALB:
```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Strict-Transport-Security: max-age=31536000
```

---

## Secrets Management

### Recomendações

1. **Nunca** commitar API keys no repositório
2. Usar variáveis de ambiente ou secret managers:
   - AWS Secrets Manager
   - HashiCorp Vault
   - Azure Key Vault
   - Kubernetes Secrets

### Docker Compose

```yaml
services:
  api:
    environment:
      - API_KEYS=${API_KEYS}  # Via .env file
```

### Kubernetes

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: api-secrets
type: Opaque
stringData:
  API_KEYS: "key1,key2,key3"
---
apiVersion: apps/v1
kind: Deployment
spec:
  template:
    spec:
      containers:
        - name: api
          envFrom:
            - secretRef:
                name: api-secrets
```

---

## Logging e Auditoria

### O que é logado

- Request ID para correlação
- Método e path
- Status code e latência
- **Hash** de API key (nunca a key completa)
- Erros e stack traces

### O que NÃO é logado

- API keys em texto claro
- Dados de entrada (features individuais)
- PII (nomes, CPF, emails)

### Audit trail

Eventos rastreados:
- `startup` / `shutdown`
- `inference` (com hash do input, output agregado)

---

## Checklist de Segurança

- [x] API Key authentication
- [x] Rate limiting por API key
- [x] Request size limiting
- [x] Non-root Docker user
- [x] Dependency vulnerability scanning
- [x] Container scanning (Trivy)
- [x] SBOM generation
- [x] Static code analysis (Bandit)
- [x] Request ID para auditoria
- [x] Logging sem PII

### TODO (produção completa)

- [ ] TLS termination (via proxy)
- [ ] CORS configurável
- [ ] IP allowlisting (via proxy)
- [ ] WAF (AWS WAF, Cloudflare)
- [ ] Redis para rate limiting distribuído
