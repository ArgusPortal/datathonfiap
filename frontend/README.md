# 🎨 Frontend — Passos Mágicos: Predição de Risco Escolar

Interface moderna para o sistema de predição de risco de defasagem escolar da ONG Passos Mágicos.

## 🏗️ Stack Tecnológica

| Camada | Tecnologia | Versão |
|--------|-----------|--------|
| Framework | React + TypeScript | 18.3 / 5.6 |
| Build | Vite | 6.0 |
| Estilização | Tailwind CSS | 3.4 |
| Componentes | shadcn/ui (custom) | — |
| Gráficos | Recharts | 2.13 |
| Roteamento | React Router | 6.28 |
| Ícones | Lucide React | 0.460 |

## 📁 Estrutura do Projeto

```
frontend/
├── public/                    # Arquivos estáticos
│   └── favicon.svg
├── src/
│   ├── components/
│   │   ├── charts/            # Componentes de visualização
│   │   │   ├── LatencyChart.tsx
│   │   │   ├── MetricsCharts.tsx
│   │   │   ├── RiskGauge.tsx
│   │   │   ├── RiskPieChart.tsx
│   │   │   └── ScoreDistribution.tsx
│   │   ├── layout/
│   │   │   └── Layout.tsx     # Layout principal com sidebar
│   │   ├── shared/
│   │   │   ├── StatCard.tsx   # Card de estatística reutilizável
│   │   │   └── StatusBadge.tsx
│   │   └── ui/
│   │       └── index.tsx      # Primitivos UI (Card, Button, Badge, etc.)
│   ├── hooks/
│   │   └── index.ts           # Hooks customizados (usePolling, useTheme)
│   ├── lib/
│   │   ├── features.ts        # Metadata das features do modelo
│   │   └── utils.ts           # Utilitários (cn, formatting, risk helpers)
│   ├── pages/
│   │   ├── DashboardPage.tsx  # Visão geral do sistema
│   │   ├── ModelPage.tsx      # Model Card & performance
│   │   ├── MonitoringPage.tsx # Métricas, SLO, sistema
│   │   ├── PredictPage.tsx    # Predição individual + batch
│   │   └── StudentsPage.tsx   # Lista de alunos avaliados
│   ├── services/
│   │   └── api.ts             # Cliente HTTP para a API
│   ├── types/
│   │   └── index.ts           # TypeScript types (match backend)
│   ├── App.tsx                # Router principal
│   ├── main.tsx               # Entry point
│   └── index.css              # Tailwind + CSS customizado
├── .env.development           # Config de desenvolvimento
├── .env.production            # Config de produção
├── Dockerfile                 # Build para produção (nginx)
├── index.html                 # HTML template
├── package.json
├── tailwind.config.js
├── tsconfig.json
└── vite.config.ts
```

## 📱 Páginas

### 1. Dashboard (`/`)
- Status do sistema em tempo real (health, uptime, modelo)
- Cards de métricas: requests, latência p95, taxa de erro, predições alto risco
- Gráfico de distribuição de scores de risco (histograma)
- Gráfico de classificação por nível de risco (pizza)
- Status SLO compliance

### 2. Predição (`/predict`)
- **Individual**: Formulário completo com todas as features do modelo, agrupadas por categoria
  - Indicadores de desempenho (IAA, IAN, IDA, IEG, IPP, IPS, IPV)
  - Dados demográficos (fase, idade, instituição)
  - Features derivadas (com cálculo automático)
- **Batch (CSV)**: Upload de arquivo CSV para avaliação em massa
- Resultado com gauge visual, badge de risco e recomendação de ação
- Exportação de resultados em CSV

### 3. Alunos (`/students`)
- Lista interativa com dados demonstrativos
- Filtros por nível de risco, fase e busca textual
- Ordenação por score ou data
- Painel de detalhes com indicadores em barras de progresso
- Recomendações de ação para alunos em alto risco

### 4. Monitoramento (`/monitoring`)
- **Visão Geral**: Métricas operacionais (requests, latência, erros, predições)
- **SLOs**: Indicadores de compliance com as metas de serviço
- **Sistema**: Status de saúde, configuração da API, endpoints disponíveis
- Gráficos de latência e tráfego em tempo real

### 5. Modelo (`/model`)
- **Model Card**: Detalhes completos do modelo (algoritmo, versão, dados)
- **Performance**: Métricas (Recall, Precision, F1, PR-AUC), matriz de confusão, comparativo de modelos
- **Features**: Lista das features esperadas, importância relativa, features bloqueadas
- **Ética & LGPD**: Considerações de privacidade, decisão humana obrigatória

## 🚀 Quick Start

### Desenvolvimento

```bash
cd frontend
npm install
npm run dev
```

O frontend roda em `http://localhost:3000` e faz proxy das chamadas à API para `http://localhost:8000`.

### Pré-requisito: Backend rodando

```bash
# Na raiz do projeto
uvicorn app.main:app --reload --port 8000
```

### Build para Produção

```bash
npm run build     # Gera dist/ otimizado
npm run preview   # Preview local da build
```

## 🐳 Docker

### Frontend + Backend (Docker Compose)

```bash
# Na raiz do projeto
docker compose up --build
```

- Frontend: `http://localhost:3000`
- API: `http://localhost:8000`

### Full-stack (Container único)

```bash
docker build -f Dockerfile.fullstack -t passos-magicos-app .
docker run -p 80:80 -p 8000:8000 passos-magicos-app
```

## 🎨 Design System

- **Tema**: Light/Dark mode com toggle
- **Cores de risco**:
  - 🟢 Baixo Risco (score < 0.3): Verde
  - 🟡 Risco Moderado (0.3 ≤ score < 0.7): Âmbar
  - 🔴 Alto Risco (score ≥ 0.7): Vermelho
- **Tipografia**: Inter (Google Fonts)
- **Componentes**: shadcn/ui-inspired, customizados com Tailwind

## 🔌 Integração com API

O frontend consome os seguintes endpoints do backend:

| Endpoint | Método | Uso |
|----------|--------|-----|
| `/health` | GET | Status e uptime |
| `/ready` | GET | Readiness check |
| `/metadata` | GET | Versão, features, threshold |
| `/predict` | POST | Predição de risco |
| `/metrics` | GET | Métricas operacionais |
| `/slo` | GET | Compliance SLO |

## 🛡️ LGPD & Segurança

- Nenhum dado pessoal é armazenado no frontend
- LocalStorage usado apenas para preferência de tema
- Comunicação com API via proxy (sem exposição direta)
- Indicadores visuais de compliance LGPD em toda a interface
