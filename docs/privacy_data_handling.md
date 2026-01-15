# Privacy & Data Handling Policy

## Visão Geral

Esta documentação descreve as políticas de privacidade e tratamento de dados para a API de predição de risco de defasagem escolar.

## Classificação de Dados

### Dados de Entrada (Features)

| Categoria | Campos | Tratamento |
|-----------|--------|------------|
| **PII Potencial** | nome, cpf, email, telefone | NUNCA coletados pela API |
| **Demográfico** | idade, setor, area_atuacao | Agregado apenas |
| **Performance** | nota_exame, percentual_meta | Agregado apenas |
| **Organizacional** | turnover, headcount | Agregado apenas |

### Dados de Saída

- `risk_score`: Probabilidade numérica (0-1)
- `risk_label`: Classificação binária (0/1)
- `request_id`: UUID para rastreabilidade

---

## Política de Retenção

### Configuração

```bash
export RETENTION_DAYS=30  # Default: 30 dias
export PRIVACY_MODE=aggregate_only
```

### Dados retidos

| Tipo | Retenção | Propósito |
|------|----------|-----------|
| Inference logs | 30 dias | Monitoramento de drift |
| Audit records | 30 dias | Compliance |
| Metrics | Em memória | Observabilidade |

### Script de limpeza

```bash
# Dry run
python monitoring/retention.py --dry-run

# Executar limpeza
python monitoring/retention.py --days 30

# Limpeza com logs antigos
python monitoring/retention.py --days 30 --include-logs
```

### Automação

Adicionar ao cron:
```bash
# Diariamente às 3h
0 3 * * * cd /app && python monitoring/retention.py --days 30
```

---

## Sanitização de Dados

### Padrões PII detectados

O módulo `app/privacy.py` detecta e sanitiza:

- **CPF**: `\d{3}\.?\d{3}\.?\d{3}-?\d{2}`
- **Email**: Padrão RFC 5322
- **Telefone**: Formato brasileiro
- **CEP**: `\d{5}-?\d{3}`
- **RG**: Formato brasileiro

### Campos bloqueados em logs

```python
PII_FIELDS = {
    "nome", "name", "cpf", "email", "telefone", "phone",
    "endereco", "address", "cep", "rg", "documento", "document",
    "senha", "password", "token", "api_key", "secret",
}
```

### Campos seguros para métricas

```python
SAFE_FIELDS = {
    "turnover", "headcount", "idade", "idade_empresa", "setor",
    "nota_exame", "horas_treinamento", "participou_projeto",
    "numero_avaliacoes", "promocoes_ultimos_3_anos",
    "nivel_senioridade", "nivel_escolaridade", "area_atuacao",
    "percentual_meta_batida", "pedido_demissao",
}
```

---

## Logging Seguro

### O que é logado

```json
{
  "timestamp": "2025-01-15T10:30:00Z",
  "request_id": "abc123",
  "action": "inference",
  "input_hash": "a1b2c3d4",  // Hash, não dados brutos
  "output": {
    "probability": 0.045,   // Valor agregado
  },
  "model_version": "v1.1.0",
  "latency_ms": 45.2
}
```

### O que NÃO é logado

- Valores individuais de features
- Dados que possam identificar indivíduos
- API keys
- Tokens de sessão

### Uso

```python
from app.privacy import sanitize_dict_for_logging, log_safe

# Sanitizar antes de logar
safe_data = sanitize_dict_for_logging(request_data)
logger.info("Processing request", extra=safe_data)

# Ou usar helper
log_safe(logger, logging.INFO, "Processing", data=request_data)
```

---

## Audit Trail

### Eventos rastreados

| Evento | Dados capturados |
|--------|-----------------|
| `startup` | model_version, timestamp |
| `shutdown` | timestamp, uptime |
| `inference` | request_id, input_hash, output_prob, latency |

### Formato do audit record

```json
{
  "timestamp": "2025-01-15T10:30:00Z",
  "action": "inference",
  "request_id": "abc123",
  "details": {
    "input_hash": "a1b2c3d4e5f6g7h8",
    "output": {"probability": 0.045},
    "model": {"version": "v1.1.0"},
    "performance": {"latency_ms": 45.2, "success": true}
  },
  "git_sha": "abc123def456"
}
```

---

## Compliance

### LGPD (Lei Geral de Proteção de Dados)

A API está em conformidade com LGPD:

1. **Minimização**: Apenas features necessárias são processadas
2. **Finalidade**: Dados usados apenas para predição
3. **Retenção limitada**: 30 dias por padrão
4. **Segurança**: Criptografia em trânsito (TLS), sanitização

### Direitos do titular

Para exercer direitos LGPD (acesso, retificação, exclusão):
- Contatar DPO da organização
- Fornecer request_id para rastreamento

### Checklist LGPD

- [x] Não coleta PII
- [x] Logging sem dados pessoais
- [x] Retenção configurável
- [x] Script de exclusão (retention.py)
- [x] Audit trail
- [ ] Consentimento (responsabilidade do cliente)
- [ ] DPO designado (responsabilidade da organização)

---

## Configuração de Privacidade

### Variáveis de ambiente

```bash
# Modo de privacidade
export PRIVACY_MODE=aggregate_only  # aggregate_only, anonymized, full

# Retenção
export RETENTION_DAYS=30

# Desabilitar audit (não recomendado)
export AUDIT_ENABLED=false
```

### Modos de privacidade

| Modo | Descrição |
|------|-----------|
| `aggregate_only` | Apenas métricas agregadas em logs |
| `anonymized` | Features com hash/pseudonimização |
| `full` | Logging completo (dev only) |

---

## Recomendações

### Para desenvolvimento

```bash
export PRIVACY_MODE=full
export AUDIT_ENABLED=true
export RETENTION_DAYS=7
```

### Para produção

```bash
export PRIVACY_MODE=aggregate_only
export AUDIT_ENABLED=true
export RETENTION_DAYS=30
export API_KEYS="<secure-keys>"
```

### Checklist de deploy

- [ ] TLS habilitado
- [ ] API keys configuradas
- [ ] Logs em volume persistente
- [ ] Retention cron configurado
- [ ] Backup de audit trail
