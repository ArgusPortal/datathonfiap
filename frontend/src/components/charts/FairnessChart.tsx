import { useMemo } from 'react'
import type { FairnessGroup, FairnessSubgroupMetrics } from '@/types'
import { formatPercentage } from '@/lib/utils'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
interface SubgroupRow {
  name: string
  n: number
  prevalence: number
  recall: number | null
  precision: number | null
  f1: number | null
  f2: number | null
}

interface FairnessTableProps {
  title: string
  description: string
  group: FairnessGroup
  icon: string
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function extractRows(group: FairnessGroup): { rows: SubgroupRow[]; disparity: number | null } {
  const rows: SubgroupRow[] = []
  let disparity: number | null = null

  for (const [key, value] of Object.entries(group)) {
    if (key === '_disparity') {
      disparity = (value as { recall_disparity: number }).recall_disparity
    } else {
      const m = value as FairnessSubgroupMetrics
      rows.push({
        name: key,
        n: m.n,
        prevalence: m.prevalence,
        recall: m.recall,
        precision: m.precision,
        f1: m.f1,
        f2: m.f2,
      })
    }
  }

  // Sort by name
  rows.sort((a, b) => a.name.localeCompare(b.name, 'pt-BR'))
  return { rows, disparity }
}

function fmt(v: number | null): string {
  if (v === null || v === undefined) return '—'
  return formatPercentage(v)
}

function disparityBadge(disparity: number | null) {
  if (disparity === null) return null
  const pct = (disparity * 100).toFixed(1)
  if (disparity <= 0.05) {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300">
        ✓ Excelente ({pct}%)
      </span>
    )
  }
  if (disparity <= 0.10) {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300">
        ✓ Aceitável ({pct}%)
      </span>
    )
  }
  if (disparity <= 0.15) {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300">
        ⚠ Atenção ({pct}%)
      </span>
    )
  }
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300">
      ✗ Alto ({pct}%)
    </span>
  )
}

function recallBar(recall: number | null) {
  if (recall === null) return <div className="h-2 w-full rounded bg-muted" />
  const pct = Math.round(recall * 100)
  const color =
    recall >= 0.95
      ? 'bg-green-500'
      : recall >= 0.85
        ? 'bg-blue-500'
        : recall >= 0.75
          ? 'bg-amber-500'
          : 'bg-red-500'
  return (
    <div className="flex items-center gap-2 w-full">
      <div className="flex-1 h-2 rounded bg-muted overflow-hidden">
        <div className={`h-full rounded ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-[11px] font-mono w-12 text-right">{fmt(recall)}</span>
    </div>
  )
}

// ---------------------------------------------------------------------------
// FairnessTable
// ---------------------------------------------------------------------------
export function FairnessTable({ title, description, group, icon }: FairnessTableProps) {
  const { rows, disparity } = useMemo(() => extractRows(group), [group])

  return (
    <div className="rounded-lg border">
      <div className="px-4 py-3 border-b bg-muted/30">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center gap-2">
            <span className="text-lg">{icon}</span>
            <div>
              <h4 className="font-semibold text-sm">{title}</h4>
              <p className="text-xs text-muted-foreground">{description}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">Disparidade Recall:</span>
            {disparityBadge(disparity)}
          </div>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b text-xs text-muted-foreground">
              <th className="text-left p-3 font-medium">Subgrupo</th>
              <th className="text-right p-3 font-medium">N</th>
              <th className="text-right p-3 font-medium">Prevalência</th>
              <th className="p-3 font-medium w-40">Recall</th>
              <th className="text-right p-3 font-medium">Precision</th>
              <th className="text-right p-3 font-medium">F1</th>
              <th className="text-right p-3 font-medium">F2</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.name} className="border-b last:border-0 hover:bg-muted/30">
                <td className="p-3 font-medium">{row.name}</td>
                <td className="p-3 text-right text-muted-foreground">{row.n}</td>
                <td className="p-3 text-right text-muted-foreground">{fmt(row.prevalence)}</td>
                <td className="p-3">{recallBar(row.recall)}</td>
                <td className="p-3 text-right font-mono text-xs">{fmt(row.precision)}</td>
                <td className="p-3 text-right font-mono text-xs">{fmt(row.f1)}</td>
                <td className="p-3 text-right font-mono text-xs">{fmt(row.f2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Disparity Summary Cards
// ---------------------------------------------------------------------------
interface DisparitySummaryProps {
  generoDisparity: number | null
  faseDisparity: number | null
  instituicaoDisparity: number | null
}

export function DisparitySummary({ generoDisparity, faseDisparity, instituicaoDisparity }: DisparitySummaryProps) {
  const items = [
    { label: 'Gênero', value: generoDisparity, icon: '👥' },
    { label: 'Fase', value: faseDisparity, icon: '📚' },
    { label: 'Instituição', value: instituicaoDisparity, icon: '🏫' },
  ]

  return (
    <div className="grid gap-4 grid-cols-1 sm:grid-cols-3">
      {items.map((item) => (
        <div key={item.label} className="rounded-lg border p-4 text-center">
          <span className="text-2xl">{item.icon}</span>
          <p className="text-sm font-medium mt-2">{item.label}</p>
          <p className="text-2xl font-bold mt-1">
            {item.value !== null ? `${(item.value * 100).toFixed(1)}%` : '—'}
          </p>
          <div className="mt-2">{disparityBadge(item.value)}</div>
        </div>
      ))}
    </div>
  )
}
