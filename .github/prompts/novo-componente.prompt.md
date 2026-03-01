---
description: "Criar novo componente React com shadcn/ui, Tailwind e tipagem completa"
mode: "agent"
tools:
  - search
  - codebase
  - editFiles
---

Crie um novo componente React seguindo o padrão do projeto Passos Mágicos:

1. **Componente** em `frontend/src/components/` (pasta adequada: charts/, shared/, layout/)
2. Usar **functional component** com props tipadas (interface explícita)
3. Usar **shadcn/ui** (Card, Button, Tabs, etc.) + **Tailwind CSS** utility-first
4. Ícones via **Lucide React**
5. Gráficos com **Nivo** (bar, pie, line, heatmap) ou **Recharts** (timelines)
6. Tratar **empty state** com ícone + mensagem descritiva
7. Ser **responsive**: `grid-cols-1 md:grid-cols-2 lg:grid-cols-3`
8. Cores de status: emerald (ok), amber (warning), red (critical)

Padrão de componente:
```tsx
interface Props { /* tipagem completa */ }
export function NomeComponente({ prop1, prop2 }: Props) {
  return <Card>...</Card>;
}
```
