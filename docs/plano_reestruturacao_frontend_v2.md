# Plano de Reestruturação Frontend v2 — Passos Mágicos

> **Contexto**: Projeto acadêmico (Datathon FIAP) — quanto mais técnico, explícito e educativo, melhor a avaliação.  
> **Data**: Fevereiro 2025  
> **Baseline**: React 18 + TypeScript + Vite 6 + Tailwind CSS + Recharts  

---

## 1. Análise do Site Oficial passosmagicos.org.br

### 1.1 Identidade Visual Extraída

| Elemento | Observação no Site Oficial |
|---|---|
| **Cor primária** | Azul escuro/royal — `#1e3a8a` a `#2563eb` (tons de azul profundo) |
| **Cor secundária** | Roxo/magenta — gradientes com tons de `#7c3aed` a `#a855f7` |
| **Cor de destaque** | Laranja/amarelo quente — usado em CTAs e destaques de impacto |
| **Tipografia** | Sans-serif moderna, com pesos bold para títulos e light para corpo |
| **Cards** | Bordas arredondadas suaves, sombra sutil, fundo branco com hover suave |
| **Layout** | Seções full-width com alternância de fundo claro/escuro |
| **Storytelling** | Depoimentos de alunos, linha do tempo, números de impacto em destaque |
| **Impacto visual** | Números grandes com ícones — ex: "1.250 crianças", "120 universitários" |
| **Seções principais** | Hero → O que fazemos → Quem somos → Transformando Vidas → Impacto → Parceiros |
| **ODS ONU** | Alinhamento explícito com ODS 1, 4, 5, 8, 10 |

### 1.2 Padrões de Design a Incorporar

1. **Hero Section com gradiente e mensagem inspiracional** — "Acreditamos em transformar vidas através da educação!"
2. **Cards de impacto** — números enormes com animação counter-up e ícone temático
3. **Depoimentos** — carousel com foto, nome, idade e texto do aluno
4. **Linha do tempo** — evolução institucional (adaptar para evolução do modelo)
5. **Parceiros** — grid de logos (FIAP como parceiro-destaque)
6. **Valores** — cards com ícones representando empatia, educação, pertencimento
7. **ODS da ONU** — badges coloridos mostrando alinhamento social do projeto

---

## 2. Diagnóstico do Frontend Atual

### 2.1 Stack Atual
```
React 18.3.1 + TypeScript 5.6
Vite 6.0.0 (bundler)
Tailwind CSS 3.4.16 (styling)
Recharts 2.13.3 (gráficos)
Radix UI (primitivos: Tabs, Dialog, Select, Tooltip, etc.)
Lucide React (ícones)
Zustand implícito (predictionStore)
```

### 2.2 Páginas Existentes (5)
| Página | Linhas | Conteúdo Atual | Gap |
|---|---|---|---|
| `DashboardPage` | 686 | KPIs, StatCards, Score Distribution, Risk Pie, Drift status | Falta hero, impacto social, storytelling |
| `PredictPage` | 632 | Form individual/batch, SHAP waterfall, business rules | Falta comparativo temporal, bulk download |
| `StudentsPage` | ~400 | Tabela de alunos com filtros | Falta perfil individual, timeline do aluno |
| `MonitoringPage` | 1010 | Latência, SLO, drift, audit trail | Falta alertas visuais mais ricos, heatmaps |
| `ModelPage` | 1423 | 6 tabs: Card, Performance, Features, Ethics, Governance, Comparison | Mais completa — falta interatividade nos gráficos |

### 2.3 Componentes de Gráfico (4)
- `MetricsCharts.tsx` — LatencyChart + MetricsTimeline (Recharts Line/Area)
- `RiskGauge.tsx` — gauge semicircular (SVG custom)
- `RiskPieChart.tsx` — pizza Recharts
- `ScoreDistribution.tsx` — histograma Recharts

### 2.4 Design System Atual
- CSS Variables via `index.css` (HSL)
- Paleta `passos` definida em `tailwind.config.js` (azuis genéricos #eff6ff → #1e3a8a)
- Glassmorphism, fade-in-up, card-hover, skeleton shimmer
- Dark mode via classe `.dark`

### 2.5 Pontos Fortes ✅
- TypeScript strict em todo o projeto
- Lazy loading com React.lazy + Suspense
- Keyboard shortcuts (g+d, g+p, g+s, g+m, g+i)
- Zustand store para predições
- Radix UI para acessibilidade
- Dark mode funcional
- API layer bem abstraída (13 endpoints)

### 2.6 Gaps Críticos ❌
1. **Identidade visual genérica** — não reflete a marca Passos Mágicos
2. **Sem storytelling** — falta contexto educacional/social
3. **Gráficos básicos** — Recharts limitado em interatividade e variedade
4. **Sem página "Sobre"** — contexto do projeto, ODS, impacto social
5. **Sem análise exploratória** — falta página de análise de dados com múltiplos gráficos
6. **Sem exportação** — relatórios em PDF/PNG para stakeholders
7. **Sem animações de dados** — números estáticos, sem counter-up
8. **Sem responsividade completa** — mobile precisa de revisão
9. **Sem i18n** — interface só em PT-BR, mas sem estrutura de internacionalização

---

## 3. Decisão de Framework de Gráficos

### 3.1 Comparativo

| Critério | Recharts (atual) | Nivo | Plotly.js | ECharts |
|---|---|---|---|---|
| **React-native** | ✅ Sim | ✅ Sim | ⚠️ Wrapper | ⚠️ Wrapper |
| **Variedade** | 12 tipos | 30+ tipos | 50+ tipos | 40+ tipos |
| **Interatividade** | Básica | Boa | Excelente | Excelente |
| **Heatmap** | ❌ | ✅ | ✅ | ✅ |
| **Radar/Spider** | ✅ | ✅ | ✅ | ✅ |
| **Sankey** | ❌ | ✅ | ✅ | ✅ |
| **Treemap** | ✅ | ✅ | ✅ | ✅ |
| **Box Plot** | ❌ | ✅ | ✅ | ✅ |
| **Waffle** | ❌ | ✅ | ❌ | ❌ |
| **Bump chart** | ❌ | ✅ | ❌ | ❌ |
| **SSR** | ❌ | ✅ | ❌ | ❌ |
| **Temas** | Manual | Built-in | Built-in | Built-in |
| **Tamanho bundle** | ~150KB | ~200KB | ~3.5MB | ~800KB |
| **Curva aprendizado** | Baixa | Média | Média | Alta |
| **Acadêmico/Científico** | ⚠️ | ✅✅ | ✅✅✅ | ✅✅ |

### 3.2 Recomendação: **Nivo** (migração principal) + manter Recharts para gráficos simples

**Justificativa técnica:**
- **Nativo React** — componentes declarativos, sem wrappers
- **30+ tipos** — heatmap, radar, sankey, waffle, bump, stream, choropleth
- **D3 por baixo** — poder do D3 sem complexidade direta
- **Temas customizáveis** — permite criar tema "Passos Mágicos"
- **SVG + Canvas** — renderização otimizada conforme necessidade
- **Bundle moderado** — tree-shakeable, importa só o que usa (~25KB por tipo)
- **Responsivo nativo** — `<ResponsiveBar>`, `<ResponsiveHeatMap>`, etc.
- **Animações built-in** — transições suaves via react-spring
- **Tooltips ricos** — customizáveis com JSX
- **Padrões (patterns) e gradientes** — diferencial visual para apresentação acadêmica

**Estratégia de migração:**
- Manter `recharts` para `LatencyChart` e `MetricsTimeline` (line/area já funcionam bem)
- Adicionar `@nivo/core`, `@nivo/bar`, `@nivo/pie`, `@nivo/heatmap`, `@nivo/radar`, `@nivo/waffle`, `@nivo/line`, `@nivo/stream`, `@nivo/bump`, `@nivo/funnel`
- Migrar gráficos de dashboard e modelo para Nivo progressivamente
- Criar tema unificado `passosTheme` para todos os gráficos Nivo

---

## 4. Nova Paleta de Cores — Alinhamento com ONG

### 4.1 Paleta Principal (inspirada no site oficial)

```css
:root {
  /* Azul institucional Passos Mágicos */
  --pm-blue-50:  #eef4ff;
  --pm-blue-100: #d9e5ff;
  --pm-blue-200: #bcd0ff;
  --pm-blue-300: #8eb4ff;
  --pm-blue-400: #5990ff;
  --pm-blue-500: #3366ff;  /* Primária */
  --pm-blue-600: #1a44f5;
  --pm-blue-700: #1433e1;
  --pm-blue-800: #172bb6;
  --pm-blue-900: #19298f;

  /* Roxo/Magenta — transformação */
  --pm-purple-50:  #f5f0ff;
  --pm-purple-100: #ede5ff;
  --pm-purple-200: #dcceff;
  --pm-purple-300: #c4a8ff;
  --pm-purple-400: #a875ff;
  --pm-purple-500: #8b3dff;  /* Secundária */
  --pm-purple-600: #7c1aff;
  --pm-purple-700: #6e0eeb;
  --pm-purple-800: #5c0ec5;
  --pm-purple-900: #4d0fa1;

  /* Laranja/Dourado — impacto, urgência, call-to-action */
  --pm-orange-50:  #fff7ed;
  --pm-orange-100: #ffedd5;
  --pm-orange-200: #fed7aa;
  --pm-orange-300: #fdba74;
  --pm-orange-400: #fb923c;
  --pm-orange-500: #f97316;  /* Destaque */
  --pm-orange-600: #ea580c;

  /* Verde — sucesso, baixo risco */
  --pm-green-500: #22c55e;
  --pm-green-600: #16a34a;

  /* Vermelho — alto risco */
  --pm-red-500: #ef4444;
  --pm-red-600: #dc2626;

  /* Amarelo — risco médio */
  --pm-yellow-500: #eab308;
}
```

### 4.2 Gradientes Temáticos
```css
/* Gradiente hero — inspirado no site PM */
.pm-hero-gradient {
  background: linear-gradient(135deg, #19298f 0%, #3366ff 40%, #8b3dff 100%);
}

/* Gradiente de cards de impacto */
.pm-impact-gradient {
  background: linear-gradient(135deg, #3366ff 0%, #8b3dff 100%);
}

/* Gradiente sutil para backgrounds de seção */
.pm-section-gradient {
  background: linear-gradient(180deg, #eef4ff 0%, #ffffff 100%);
}
```

### 4.3 Tema Nivo (passosTheme)
```typescript
export const passosNivoTheme = {
  background: 'transparent',
  text: { fontSize: 12, fill: '#374151', fontFamily: 'Inter, sans-serif' },
  axis: {
    ticks: { text: { fontSize: 11, fill: '#6b7280' } },
    legend: { text: { fontSize: 13, fill: '#374151', fontWeight: 600 } },
  },
  grid: { line: { stroke: '#e5e7eb', strokeWidth: 1 } },
  tooltip: {
    container: {
      background: '#ffffff',
      borderRadius: '8px',
      boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
      padding: '8px 12px',
      fontSize: 13,
    },
  },
  labels: { text: { fontSize: 12, fontWeight: 600 } },
}

export const passosPalette = [
  '#3366ff', '#8b3dff', '#f97316', '#22c55e',
  '#ef4444', '#06b6d4', '#ec4899', '#eab308',
  '#14b8a6', '#6366f1',
]
```

---

## 5. Nova Arquitetura de Páginas (8 páginas)

### 5.1 Mapa de Navegação

```
/                   → Dashboard (hero + KPIs + impacto social)
/analysis           → Análise Exploratória (NOVA)
/predict            → Predição (form + resultado + explicabilidade)
/students           → Alunos (tabela + perfil individual)
/monitoring         → Monitoramento (SLO + drift + audit)
/model              → Modelo (card + performance + features + ética)
/about              → Sobre o Projeto (NOVA)
```

### 5.2 Detalhamento por Página

#### 📊 Dashboard (`/`) — REESTRUTURAR
**Objetivo**: Visão executiva do sistema + impacto educacional.

**Nova estrutura:**
1. **Hero Section** — Nome do projeto + tagline "Transformando dados em oportunidades educacionais" + gradiente PM + logo
2. **Impact Cards** (4) — animação counter-up:
   - Total de Alunos Avaliados (ícone Users)
   - Taxa de Risco Alto (ícone AlertTriangle)
   - Score Médio (ícone Target)
   - Acurácia do Modelo (ícone Brain)
3. **ODS Alignment** — badges das 5 ODS da ONU (1, 4, 5, 8, 10) com tooltip explicativo
4. **Charts Row** (3 colunas):
   - **Nivo Pie** — distribuição de risco (substituir Recharts PieChart)
   - **Nivo Waffle** — proporção risco alto vs baixo (visual impactante para apresentação)
   - **Nivo Bar** — score por faixa de indicadores
5. **System Status** — health card com uptime, latência, drift status
6. **Recent Activity** — últimas 5 predições com mini-timeline

**Técnicas acadêmicas a explicitar:**
- Tooltip em cada KPI explicando o que a métrica significa
- Info icon com popover explicando a fórmula de cálculo
- Link para glossário de cada termo técnico

#### 🔬 Análise Exploratória (`/analysis`) — NOVA
**Objetivo**: Página de EDA (Exploratory Data Analysis) rica em visualizações.

**Seções:**
1. **Overview dos Dados** — Nivo funnel mostrando pipeline de dados (raw → processed → features → prediction)
2. **Distribuição de Features** — Nivo Box Plot / Violin para cada feature principal
3. **Correlação** — Nivo Heatmap de correlação entre indicadores (IAA, IAN, IDA, IEG, IPP, IPS, IPV)
4. **Radar de Indicadores** — Nivo Radar comparando perfil médio de alunos alto-risco vs baixo-risco
5. **Timeline Temporal** — Nivo Line com evolução dos indicadores ao longo dos anos (2020-2023)
6. **Feature Importance** — Nivo Bar horizontal com SHAP importance ranking
7. **Scatter Matrix** — Nivo Scatter com correlações 2D entre features top-3

**Dados necessários**: Novo endpoint `/api/analysis/eda` ou computar client-side a partir dos artifacts.

**Valor acadêmico**: Esta página demonstra todo o pipeline de Data Science — exploração, hipóteses, padrões, e fundamenta as decisões de feature engineering.

#### 🧠 Predição (`/predict`) — APRIMORAR
**Melhorias:**
1. **Formulário redesenhado** — grouped by FEATURE_GROUPS com visual de stepper/wizard
2. **Preview em tempo real** — gauge de risco atualiza conforme preenche campos
3. **Resultado expandido**:
   - Nivo Radar com perfil do aluno vs média
   - SHAP waterfall (já existe) + business rules (já existe)
   - **Recomendações automáticas** — baseado no perfil, sugerir intervenções
4. **Batch melhorado**:
   - Nivo Swarm Plot mostrando dispersão de scores do batch
   - Exportar PDF com relatório completo
5. **Histórico** — mini-timeline das últimas predições da sessão

#### 👥 Alunos (`/students`) — APRIMORAR
**Melhorias:**
1. **Tabela com filtros avançados** — por faixa de risco, fase, indicadores
2. **Perfil individual** — ao clicar, abre drawer/modal com:
   - Nivo Radar com indicadores do aluno
   - Timeline de evolução
   - Comparação com média da turma
3. **Nivo Stream** — visualização agregada de evolução por cohort
4. **Exportar lista** — CSV/PDF dos alunos filtrados

#### 📡 Monitoramento (`/monitoring`) — MANTER + ENRIQUECER
**Melhorias:**
1. **Nivo Heatmap** — mapa de calor de erros por hora/dia (substituir tabela)
2. **SLO Dashboard** — Nivo Bullet chart para cada SLO target
3. **Drift por feature** — Nivo Bar agrupado mostrando drift de cada feature
4. **Alertas visuais** — toast notifications quando SLO degrada

#### 📋 Modelo (`/model`) — MANTER + ENRIQUECER
**Melhorias:**
1. **Nivo Bump** — evolução de ranking dos modelos comparados (HistGB vs RF vs LogReg vs Dummy)
2. **Confusion Matrix** — Nivo Heatmap 2x2 com TP/FP/TN/FN
3. **ROC Curve** — Nivo Line com curva ROC + AUC destacado
4. **Learning Curves** — Nivo Line multi-série com train vs validation
5. **Model Card expandido** — seção de limitações, riscos, recomendações de uso
6. **Tab de Reprodutibilidade** — hash do modelo, seed, hiperparâmetros, requirements

#### 📖 Sobre o Projeto (`/about`) — NOVA
**Objetivo**: Contexto completo para avaliação acadêmica.

**Seções:**
1. **A Associação Passos Mágicos** — história desde 1992, missão, visão, valores
2. **Linha do Tempo** — timeline animada: 1992 → 2016 → crescimento → datathon
3. **O Datathon** — objetivo, escopo, dados disponíveis
4. **Arquitetura Técnica** — diagrama mermaid do sistema (FastAPI → Model → Frontend)
5. **Stack Tecnológica** — cards com logo de cada tecnologia e versão
6. **ODS da ONU** — cards detalhados dos 5 ODS alinhados
7. **Equipe** — cards com membros do time do datathon
8. **Parceiros** — logo FIAP + outros parceiros do projeto
9. **Referências** — links para papers, documentação, repositório

---

## 6. Novos Componentes Reutilizáveis

### 6.1 Componentes de UI
```
src/components/
├── shared/
│   ├── CounterUp.tsx          # Animação de número subindo (NOVO)
│   ├── ImpactCard.tsx         # Card de impacto com ícone + counter (NOVO)
│   ├── ODSBadge.tsx           # Badge ODS da ONU (NOVO)
│   ├── TimelineSection.tsx    # Linha do tempo vertical (NOVO)
│   ├── HeroSection.tsx        # Hero com gradiente PM (NOVO)
│   ├── InfoTooltip.tsx        # Tooltip educativo com (i) (NOVO)
│   ├── ExportButton.tsx       # Botão exportar PDF/PNG/CSV (NOVO)
│   ├── PageHeader.tsx         # Header padronizado por página (NOVO)
│   ├── EmptyState.tsx         # Estado vazio com ilustração (NOVO)
│   ├── Explainability.tsx     # (existente)
│   ├── Glossary.tsx           # (existente)
│   ├── StatCard.tsx           # (existente — aprimorar com counter)
│   └── StatusBadge.tsx        # (existente)
├── charts/
│   ├── NivoTheme.ts           # Tema unificado Nivo (NOVO)
│   ├── CorrelationHeatmap.tsx # Heatmap de correlação (NOVO)
│   ├── RadarProfile.tsx       # Radar de perfil do aluno (NOVO)
│   ├── FeatureImportance.tsx  # Bar horizontal SHAP (NOVO)
│   ├── WaffleRisk.tsx         # Waffle chart risco (NOVO)
│   ├── BumpRanking.tsx        # Bump chart modelo (NOVO)
│   ├── ConfusionMatrix.tsx    # Heatmap 2x2 (NOVO)
│   ├── ROCCurve.tsx           # ROC com AUC (NOVO)
│   ├── StreamEvolution.tsx    # Stream chart evolução (NOVO)
│   ├── ScoreDistribution.tsx  # (existente — migrar para Nivo)
│   ├── RiskPieChart.tsx       # (existente — migrar para Nivo)
│   ├── RiskGauge.tsx          # (existente — manter SVG custom)
│   └── MetricsCharts.tsx      # (existente — manter Recharts)
└── layout/
    ├── Layout.tsx             # (existente — atualizar sidebar)
    └── Footer.tsx             # Footer com créditos PM (NOVO)
```

### 6.2 Novos Endpoints Backend Necessários
```python
# app/main.py — novos endpoints

@app.get("/api/analysis/eda")
# Retorna: estatísticas descritivas, correlações, distribuições por feature

@app.get("/api/analysis/correlation")
# Retorna: matriz de correlação entre indicadores

@app.get("/api/analysis/profiles")
# Retorna: perfil médio alto-risco vs baixo-risco (para radar)

@app.get("/api/analysis/feature-importance")
# Retorna: SHAP values agregados para feature importance global

@app.get("/api/analysis/confusion-matrix")
# Retorna: TP, FP, TN, FN do modelo em produção

@app.get("/api/analysis/roc-data")
# Retorna: pontos da curva ROC + AUC

@app.get("/api/students/{student_id}/profile")
# Retorna: indicadores individuais + histórico temporal

@app.get("/api/about/stats")
# Retorna: estatísticas gerais para página Sobre
```

---

## 7. Plano de Execução por Fases

### Fase 1: Foundation (Prioridade MÁXIMA) ⭐
**Escopo**: Base visual + bibliotecas + tema
**Estimativa**: 2-3 horas

**Tarefas:**
1. Instalar dependências Nivo: `@nivo/core @nivo/bar @nivo/pie @nivo/heatmap @nivo/radar @nivo/waffle @nivo/line @nivo/stream @nivo/bump @nivo/funnel`
2. Atualizar `tailwind.config.js` com nova paleta PM (azul, roxo, laranja)
3. Atualizar `index.css` com novas variáveis CSS e gradientes PM
4. Criar `src/components/charts/NivoTheme.ts` com `passosNivoTheme` + `passosPalette`
5. Criar `CounterUp.tsx` (componente de animação numérica)
6. Criar `ImpactCard.tsx` (card de impacto com counter + ícone + descrição)
7. Criar `HeroSection.tsx` (hero responsivo com gradiente PM)
8. Criar `InfoTooltip.tsx` (wrapper para Radix Tooltip com estilo educativo)
9. Criar `PageHeader.tsx` (header padronizado com título + descrição)

### Fase 2: Dashboard Renovation (Prioridade ALTA) ⭐
**Escopo**: Redesign completo da página principal
**Estimativa**: 3-4 horas

**Tarefas:**
1. Hero section com gradiente PM + tagline + logo
2. Impact cards (4) com counter-up animado
3. ODS badges section
4. Migrar PieChart de Recharts → Nivo ResponsivePie
5. Adicionar WaffleRisk chart
6. Adicionar Nivo Bar para distribuição de scores
7. System status card redesenhado
8. Recent activity timeline

### Fase 3: Analysis Page (Prioridade ALTA) ⭐
**Escopo**: Nova página de Análise Exploratória
**Estimativa**: 4-5 horas

**Tarefas:**
1. Backend: endpoints `/analysis/eda`, `/analysis/correlation`, `/analysis/profiles`, `/analysis/feature-importance`
2. Criar `CorrelationHeatmap.tsx` com Nivo Heatmap
3. Criar `RadarProfile.tsx` com Nivo Radar (alto-risco vs baixo-risco)
4. Criar `FeatureImportance.tsx` com Nivo Bar horizontal
5. Criar `StreamEvolution.tsx` com Nivo Stream para evolução temporal
6. Criar `AnalysisPage.tsx` montando as seções com explicações acadêmicas
7. Adicionar rota `/analysis` no `App.tsx` e navegação

### Fase 4: Model Page Enhancement (Prioridade ALTA)
**Escopo**: Gráficos avançados de ML
**Estimativa**: 3-4 horas

**Tarefas:**
1. Backend: endpoints `/analysis/confusion-matrix`, `/analysis/roc-data`
2. Criar `ConfusionMatrix.tsx` com Nivo Heatmap 2x2
3. Criar `ROCCurve.tsx` com Nivo Line
4. Criar `BumpRanking.tsx` com Nivo Bump (ranking de modelos)
5. Adicionar tab "Reprodutibilidade" com hash, seed, hyperparams
6. Expandir ModelCard com limitações e recomendações

### Fase 5: Predict Page Enhancement (Prioridade MÉDIA)
**Escopo**: UX de predição aprimorada
**Estimativa**: 2-3 horas

**Tarefas:**
1. Redesign do formulário com visual de wizard/stepper
2. Radar de perfil do aluno no resultado
3. Recomendações automáticas baseadas no perfil de risco
4. Swarm plot para batch predictions
5. Botão de exportar resultado como PDF

### Fase 6: About Page (Prioridade MÉDIA)
**Escopo**: Nova página institucional/acadêmica
**Estimativa**: 2-3 horas

**Tarefas:**
1. Criar `AboutPage.tsx` com seções: PM história, Datathon, Arquitetura, Stack, ODS, Equipe
2. TimelineSection.tsx com linha do tempo 1992→2025
3. Diagrama de arquitetura (Mermaid ou SVG estático)
4. Cards de tecnologia com logos
5. ODSBadge.tsx com os 5 ODS relevantes
6. Footer.tsx com créditos e links

### Fase 7: Students & Monitoring Polish (Prioridade MÉDIA)
**Escopo**: Melhorias incrementais
**Estimativa**: 2-3 horas

**Tarefas:**
1. Students: drawer de perfil individual com Radar
2. Students: comparação com média da turma
3. Monitoring: Heatmap de erros por hora/dia
4. Monitoring: Bullet chart para SLAs
5. Empty states customizados para cada página

### Fase 8: Polish & Export (Prioridade BAIXA)
**Escopo**: Toques finais
**Estimativa**: 1-2 horas

**Tarefas:**
1. Sidebar redesign com logo PM e cores da marca
2. Footer em todas as páginas
3. Loading states com skeleton shimmer temático
4. Micro-animações de transição entre páginas
5. Exportar gráficos como PNG (Nivo nativo)
6. Meta tags e SEO básico para apresentação

---

## 8. Dependências a Instalar

```bash
# Nivo chart ecosystem (tree-shakeable — só usar o que importar)
npm install @nivo/core @nivo/bar @nivo/pie @nivo/heatmap @nivo/radar @nivo/waffle @nivo/line @nivo/stream @nivo/bump @nivo/funnel @nivo/tooltip

# Animação de números
npm install react-countup

# Exportação PDF (para relatórios)
npm install html2canvas jspdf

# Ícones extras (complemento ao Lucide)
# Lucide já cobre — não precisa adicionar
```

**Remoções**: Nenhuma. Manter `recharts` para os gráficos de monitoring que já funcionam.

---

## 9. Estrutura Final de Arquivos

```
frontend/src/
├── App.tsx                          # +2 rotas: /analysis, /about
├── index.css                        # Atualizar paleta PM + gradientes
├── main.tsx                         # Sem mudanças
├── vite-env.d.ts                    # Sem mudanças
│
├── components/
│   ├── charts/
│   │   ├── NivoTheme.ts            # NOVO — tema + paleta unificada
│   │   ├── CorrelationHeatmap.tsx   # NOVO — heatmap de correlação
│   │   ├── RadarProfile.tsx         # NOVO — radar de perfil
│   │   ├── FeatureImportance.tsx    # NOVO — bar horizontal SHAP
│   │   ├── WaffleRisk.tsx           # NOVO — waffle risco
│   │   ├── BumpRanking.tsx          # NOVO — bump chart modelos
│   │   ├── ConfusionMatrix.tsx      # NOVO — heatmap 2x2
│   │   ├── ROCCurve.tsx             # NOVO — curva ROC
│   │   ├── StreamEvolution.tsx      # NOVO — stream chart
│   │   ├── MetricsCharts.tsx        # EXISTENTE (Recharts — manter)
│   │   ├── RiskGauge.tsx            # EXISTENTE (SVG — manter)
│   │   ├── RiskPieChart.tsx         # EXISTENTE → MIGRAR para Nivo
│   │   └── ScoreDistribution.tsx    # EXISTENTE → MIGRAR para Nivo
│   │
│   ├── shared/
│   │   ├── CounterUp.tsx            # NOVO
│   │   ├── ImpactCard.tsx           # NOVO
│   │   ├── HeroSection.tsx          # NOVO
│   │   ├── ODSBadge.tsx             # NOVO
│   │   ├── TimelineSection.tsx      # NOVO
│   │   ├── InfoTooltip.tsx          # NOVO
│   │   ├── ExportButton.tsx         # NOVO
│   │   ├── PageHeader.tsx           # NOVO
│   │   ├── EmptyState.tsx           # NOVO
│   │   ├── Explainability.tsx       # EXISTENTE
│   │   ├── Glossary.tsx             # EXISTENTE
│   │   ├── StatCard.tsx             # EXISTENTE → APRIMORAR
│   │   └── StatusBadge.tsx          # EXISTENTE
│   │
│   ├── layout/
│   │   ├── Layout.tsx               # EXISTENTE → ATUALIZAR
│   │   └── Footer.tsx               # NOVO
│   │
│   ├── ui/                          # EXISTENTE — sem mudanças
│   └── ErrorBoundary.tsx            # EXISTENTE
│
├── pages/
│   ├── DashboardPage.tsx            # REESTRUTURAR
│   ├── AnalysisPage.tsx             # NOVO
│   ├── PredictPage.tsx              # APRIMORAR
│   ├── StudentsPage.tsx             # APRIMORAR
│   ├── MonitoringPage.tsx           # ENRIQUECER
│   ├── ModelPage.tsx                # ENRIQUECER
│   └── AboutPage.tsx                # NOVO
│
├── services/
│   └── api.ts                       # EXPANDIR (+8 endpoints)
│
├── hooks/                           # EXISTENTE — sem mudanças
├── lib/                             # EXISTENTE — sem mudanças
├── stores/                          # EXISTENTE — sem mudanças
└── types/                           # EXPANDIR com novos tipos
```

---

## 10. Métricas de Sucesso

| Métrica | Atual | Meta |
|---|---|---|
| Páginas | 5 | 7 (+Analysis, +About) |
| Componentes de gráfico | 4 | 13 (+9 Nivo) |
| Tipos de visualização | 4 (line, pie, bar, gauge) | 13+ (+ heatmap, radar, waffle, bump, stream, funnel, scatter, confusion matrix, ROC) |
| Cores da marca | Azul genérico | Paleta PM com azul/roxo/laranja |
| Storytelling | Nenhum | Hero + ODS + Timeline + About |
| Explicações técnicas | Glossário | Glossário + InfoTooltips + EDA page |
| Exportação | Nenhuma | PDF/PNG/CSV |
| Counter-up animations | 0 | 8+ impact cards |
| Mobile responsiveness | Parcial | Completa |

---

## 11. Considerações para Avaliação Acadêmica

### O que esta reestruturação demonstra:

1. **Data Science Pipeline Completo** — da exploração (EDA page) à predição (Predict) ao monitoramento (Monitoring)
2. **ML Engineering** — versionamento de modelo, confusion matrix, ROC, drift detection, SLO
3. **Data Visualization Excellence** — 13+ tipos de gráficos com justificativa de uso para cada um
4. **Software Engineering** — TypeScript strict, componentização, lazy loading, error boundaries, state management
5. **UI/UX** — design system customizado, dark mode, responsive, acessibilidade (Radix), animações
6. **DevOps** — Docker multi-stage, nginx, health checks, CI/CD ready
7. **Responsible AI** — ética, SHAP explicabilidade, business rules, model card, ODS alignment
8. **Product Thinking** — storytelling com dados, impacto social quantificado, stakeholder-oriented

### Técnicas acadêmicas explicitadas:
- SHAP (SHapley Additive exPlanations) para interpretabilidade
- Confusion Matrix com métricas derivadas (Precision, Recall, F1, Specificity)
- ROC-AUC para avaliação de classificador binário
- Heatmap de correlação de Pearson entre features
- Radar chart para comparação multidimensional de perfis
- Feature importance por permutation importance + SHAP
- Data drift detection por PSI/KS test
- SLO/SLI framework para observabilidade de ML

---

> **Próximo passo**: Iniciar Fase 1 (Foundation) — instalar Nivo, atualizar paleta, criar componentes base.
