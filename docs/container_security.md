# Container Security Guide

## Dockerfile Hardening

### Práticas implementadas

1. **Multi-stage build**: Separa build de runtime
2. **Non-root user**: `appuser:appgroup` (UID/GID 1000)
3. **Minimal base image**: `python:3.11-slim`
4. **Fixed UID/GID**: Evita conflitos de permissão
5. **No shell login**: `--shell /bin/false`
6. **Health check**: Kubernetes-ready

### Dockerfile atual

```dockerfile
# Multi-stage build
FROM python:3.11-slim AS builder
# ... build dependencies

FROM python:3.11-slim
# ... runtime only

# Non-root user
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/false --no-create-home appuser

USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1
```

---

## Supply Chain Security

### Dependency Scanning

**Ferramentas utilizadas:**
- `safety`: Vulnerabilidades conhecidas
- `pip-audit`: Base de dados PyPI
- `Trivy`: Scanner de container

**Workflow CI:**
```yaml
# .github/workflows/security_scan.yml
- name: Run safety check
  run: safety check -r requirements.txt

- name: Run pip-audit
  run: pip-audit -r requirements.txt

- name: Run Trivy
  uses: aquasecurity/trivy-action@master
```

### Política de vulnerabilidades

| Severidade | Ação | SLA |
|------------|------|-----|
| CRITICAL | Bloqueia CI | Imediato |
| HIGH | Alerta | 7 dias |
| MEDIUM | Backlog | 30 dias |
| LOW | Monitorar | Próxima release |

### SBOM (Software Bill of Materials)

Gerado automaticamente em cada build:

```bash
# Gerar SBOM manualmente
pip install cyclonedx-bom
cyclonedx-py environment -o sbom.json --format json

# Ver árvore de dependências
pipdeptree --json > dependency-tree.json
```

---

## Vulnerability Scanning

### Container scanning com Trivy

```bash
# Instalar Trivy
brew install aquasecurity/trivy/trivy  # macOS
# ou
apt-get install trivy  # Debian/Ubuntu

# Scan da imagem
trivy image datathon-api:latest

# Scan com severidade mínima
trivy image --severity HIGH,CRITICAL datathon-api:latest

# Exportar resultados
trivy image --format sarif -o trivy.sarif datathon-api:latest
```

### Code scanning com Bandit

```bash
# Instalar
pip install bandit

# Scan de código Python
bandit -r app/ src/ -f json -o bandit-report.json

# Configurar exceções (.bandit)
[bandit]
exclude_dirs = tests,venv
skips = B101  # assert statements
```

---

## Registry Security

### Docker Hub (público)

```bash
# Build e push
docker build -t datathon-fiap/defasagem-api:v1.0.0 .
docker push datathon-fiap/defasagem-api:v1.0.0

# Sempre usar tags específicas (nunca :latest em prod)
```

### AWS ECR (privado)

```bash
# Login
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin 123456789.dkr.ecr.us-east-1.amazonaws.com

# Tag e push
docker tag datathon-api:latest 123456789.dkr.ecr.us-east-1.amazonaws.com/datathon-api:v1.0.0
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/datathon-api:v1.0.0
```

### Image signing (Cosign)

```bash
# Instalar cosign
brew install sigstore/tap/cosign

# Gerar keypair
cosign generate-key-pair

# Assinar imagem
cosign sign --key cosign.key datathon-api:v1.0.0

# Verificar assinatura
cosign verify --key cosign.pub datathon-api:v1.0.0
```

---

## Runtime Security

### Kubernetes Pod Security

```yaml
apiVersion: v1
kind: Pod
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    runAsGroup: 1000
    fsGroup: 1000
  containers:
    - name: api
      securityContext:
        allowPrivilegeEscalation: false
        readOnlyRootFilesystem: true
        capabilities:
          drop:
            - ALL
      resources:
        limits:
          cpu: "1"
          memory: "512Mi"
        requests:
          cpu: "100m"
          memory: "256Mi"
```

### Network Policies

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-network-policy
spec:
  podSelector:
    matchLabels:
      app: datathon-api
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: ingress-nginx
      ports:
        - port: 8000
  egress:
    - to: []  # Deny all egress (API não precisa de saída)
```

---

## CI/CD Integration

### GitHub Actions Workflow

```yaml
name: Security Scan

on: [push, pull_request]

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Build image
        run: docker build -t app:scan .
      
      - name: Run Trivy
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: 'app:scan'
          exit-code: '1'
          severity: 'CRITICAL'
```

### Pre-commit hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: ['-r', 'app/', 'src/']
```

---

## Checklist de Segurança

### Build time

- [x] Multi-stage build
- [x] Minimal base image
- [x] Non-root user
- [x] Fixed UID/GID
- [x] HEALTHCHECK directive
- [x] No secrets no Dockerfile

### CI/CD

- [x] Dependency scanning (safety, pip-audit)
- [x] Container scanning (Trivy)
- [x] SBOM generation
- [x] Static analysis (Bandit)
- [x] Blocking on CRITICAL

### Runtime

- [x] Non-root execution
- [ ] Read-only filesystem (opcional)
- [ ] Capabilities dropped
- [ ] Network policies
- [ ] Resource limits

### Registry

- [ ] Private registry
- [ ] Image signing
- [ ] Vulnerability scanning no registry
- [ ] Immutable tags

---

## Troubleshooting

### Container não inicia

```bash
# Verificar logs
docker logs <container_id>

# Verificar permissões
docker exec -it <container_id> ls -la /app

# Verificar usuário
docker exec -it <container_id> whoami
```

### Vulnerabilidades encontradas

```bash
# Ver detalhes da vulnerabilidade
trivy image --severity HIGH app:latest

# Atualizar dependência específica
pip install --upgrade <package>

# Rebuild e re-scan
docker build --no-cache -t app:latest .
trivy image app:latest
```

### Health check falhando

```bash
# Testar manualmente
docker exec -it <container_id> curl http://localhost:8000/health

# Verificar portas
docker port <container_id>

# Verificar logs do app
docker logs --tail 100 <container_id>
```
