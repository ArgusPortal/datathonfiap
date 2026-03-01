---
applyTo: "frontend/**/*.{ts,tsx}"
---

# TypeScript/React — Convenções Passos Mágicos

- **React 18** + TypeScript strict, build com Vite
- Componentes: functional com props tipadas, sem `any`
- Design system: shadcn/ui (Card, Button, Tabs, Badge, Dialog)
- Estilo: Tailwind CSS utility-first, sem CSS custom
- Ícones: Lucide React (`import { IconName } from "lucide-react"`)
- Gráficos: Nivo (bar, pie, line, heatmap, radar), Recharts (timelines)
- Estado: React hooks (local), Zustand (global em `stores/`)
- API: cliente centralizado em `services/api.ts` com tipos genéricos
- Tipos: interfaces em `types/index.ts`, matching schemas Pydantic
- Empty states: sempre tratar com ícone + mensagem descritiva
- Cores de status: emerald (ok), amber (warning), red (critical)
- Responsive: mobile-first com `grid-cols-1 md:grid-cols-2 lg:grid-cols-3`
