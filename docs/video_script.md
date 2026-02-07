# Roteiro do Vídeo — Datathon FIAP 2026

**Duração total**: 4:30–5:00  
**Apresentador(es)**: {{VIDEO_PRESENTER}}  
**Requisito**: pelo menos 1 integrante aparece em tela

---

## Bloco 1: Problema (0:00–0:30)

**Fala (bullets)**:
- Passos Mágicos: ONG que transforma vidas de crianças via educação
- Desafio: identificar alunos em risco de defasagem escolar ANTES de acontecer
- Defasagem = atraso moderado ou severo no aprendizado
- Hoje: identificação tardia, intervenção reativa

**Tela**: slide com logo PM + estatística de defasagem

---

## Bloco 2: O que construímos (0:30–1:20)

**Fala (bullets)**:
- Pipeline ML completo: dados → features → modelo → API → monitoramento
- Modelo HistGradientBoosting calibrado, threshold otimizado (0.35)
- 34 features incluindo deltas temporais e flags de missing
- Validação de regras de negócio INDE/PEDE
- API REST (FastAPI) pronta para integração
- Docker para deploy em qualquer ambiente
- Monitoramento de drift para garantir qualidade contínua

**Tela**: diagrama de arquitetura (data → train → API → drift)

---

## Bloco 3: Resultado/Métricas (1:20–2:10)

**Fala (bullets)**:
- Recall 93.5%: capturamos quase todos os alunos em risco
- Trade-off consciente: threshold 0.35 equilibra recall e precision
- Precision ~70%: redução significativa de falsos positivos
- PR-AUC 0.83: excelente discriminação precision-recall
- Brier Score 0.13: probabilidades bem calibradas
- 11 modelos comparados em end-to-end analysis

**Tela**: tabela de métricas + gráfico ROC ou confusion matrix

---

## Bloco 4: Produção (2:10–3:20)

**Fala (bullets)**:
- API funcionando: /health, /metadata, /predict
- Demonstração ao vivo: chamada curl com resultado real
- Docker: build + run em segundos
- Link cloud: {{API_LINK}} (ou localhost:8000 se local)

**Tela**: terminal com curl executando → resposta JSON

**Demonstração obrigatória**:
```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"instances":[{"fase_2023":3,"iaa_2023":6.5,...}]}'
```
→ Mostrar resposta: `{"predictions":[{"risk_score":0.75,"risk_label":1}]}`

---

## Bloco 5: Confiabilidade e Operação (3:20–4:30)

**Fala (bullets)**:
- 382 testes automatizados, cobertura 81%
- Logs estruturados JSON (sem PII)
- Inference Store: armazena estatísticas agregadas
- Drift Report: HTML com PSI por feature
- Runbook de operação para time de dados
- Security: API Key auth, rate limiting, privacy controls

**Tela 1**: terminal com `pytest --cov` → resultado 382 passed, 81%

**Tela 2**: drift_report HTML aberto no browser

**Demonstração obrigatória**: mostrar HTML do drift report com cores verde/amarelo

---

## Bloco 6: Próximos Passos (4:30–5:00)

**Fala (bullets)**:
- CI/CD com GitHub Actions
- Dashboard de monitoramento em tempo real
- Análise de fairness por grupos demográficos
- Feedback loop com educadores

**Tela**: slide com roadmap visual

---

## Checklist de Demonstrações

- [ ] 1 chamada /predict ao vivo (terminal)
- [ ] 1 tela do drift_report HTML
- [ ] 1 evidência de pytest --cov (200 passed, 84%)
- [ ] Pelo menos 1 integrante aparece em tela
