/**
 * NivoTheme.ts — Tema unificado para todos os gráficos Nivo
 *
 * Alinhado com a identidade visual da Associação Passos Mágicos:
 *  - Azul institucional (#3366ff) como cor primária
 *  - Roxo (#8b3dff) como cor de transformação/magia
 *  - Laranja (#f97316) como cor de impacto/destaque
 *
 * Uso: importe `passosNivoTheme` e `passosPalette` em qualquer componente Nivo.
 */
/** Tipo parcial do tema Nivo */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
type NivoTheme = Record<string, any>

/** Tema Nivo customizado — cores, fontes, tooltips */
export const passosNivoTheme: NivoTheme = {
  background: 'transparent',
  text: {
    fontSize: 12,
    fill: '#374151',
    fontFamily: 'Inter, system-ui, -apple-system, sans-serif',
  },
  axis: {
    domain: { line: { stroke: '#d1d5db', strokeWidth: 1 } },
    ticks: {
      line: { stroke: '#e5e7eb', strokeWidth: 1 },
      text: { fontSize: 11, fill: '#6b7280' },
    },
    legend: { text: { fontSize: 13, fill: '#374151', fontWeight: 600 } },
  },
  grid: { line: { stroke: '#f3f4f6', strokeWidth: 1 } },
  crosshair: { line: { stroke: '#3b82f6', strokeWidth: 1, strokeOpacity: 0.5 } },
  tooltip: {
    container: {
      background: '#ffffff',
      borderRadius: '8px',
      boxShadow: '0 4px 16px rgba(0,0,0,0.12)',
      padding: '10px 14px',
      fontSize: '13px',
      fontFamily: 'Inter, system-ui, sans-serif',
      border: '1px solid #e5e7eb',
    },
  },
  labels: { text: { fontSize: 12, fontWeight: 600, fill: '#374151' } },
  legends: { text: { fontSize: 12, fill: '#6b7280' } },
  annotations: {
    text: { fontSize: 13, fill: '#374151', fontWeight: 600 },
    link: { stroke: '#3b82f6', strokeWidth: 1.5 },
    outline: { stroke: '#3b82f6', strokeWidth: 2 },
    symbol: { fill: '#3b82f6' },
  },
}

/** Tema dark mode */
export const passosNivoThemeDark: NivoTheme = {
  ...passosNivoTheme,
  text: {
    ...passosNivoTheme.text,
    fill: '#d1d5db',
  },
  axis: {
    domain: { line: { stroke: '#374151', strokeWidth: 1 } },
    ticks: {
      line: { stroke: '#374151', strokeWidth: 1 },
      text: { fontSize: 11, fill: '#9ca3af' },
    },
    legend: { text: { fontSize: 13, fill: '#d1d5db', fontWeight: 600 } },
  },
  grid: { line: { stroke: '#1f2937', strokeWidth: 1 } },
  tooltip: {
    container: {
      background: '#1e293b',
      borderRadius: '8px',
      boxShadow: '0 4px 16px rgba(0,0,0,0.4)',
      padding: '10px 14px',
      fontSize: '13px',
      fontFamily: 'Inter, system-ui, sans-serif',
      border: '1px solid #334155',
      color: '#e2e8f0',
    },
  },
  labels: { text: { fontSize: 12, fontWeight: 600, fill: '#e2e8f0' } },
  legends: { text: { fontSize: 12, fill: '#9ca3af' } },
}

/**
 * Paleta de cores sequencial — 10 cores para séries de dados.
 * Ordenadas por prioridade visual: azul → roxo → laranja → verde → etc.
 */
export const passosPalette = [
  '#3b82f6', // blue-500
  '#6366f1', // indigo-500
  '#f59e0b', // amber-500
  '#22c55e', // green-500
  '#ef4444', // red-500
  '#06b6d4', // cyan-500
  '#8b5cf6', // violet-500
  '#ec4899', // pink-500
  '#14b8a6', // teal-500
  '#f97316', // orange-500
]

/** Paleta para gráficos de risco (3 faixas) */
export const riskPalette = {
  low: '#22c55e',
  medium: '#f59e0b',
  high: '#ef4444',
}

/** Paleta divergente para heatmaps (vermelho → branco → azul) */
export const divergentPalette = ['#ef4444', '#fca5a5', '#fef2f2', '#dbeafe', '#60a5fa', '#3366ff']

/** Paleta sequencial para heatmaps de intensidade */
export const sequentialPalette = ['#eff6ff', '#bfdbfe', '#60a5fa', '#3b82f6', '#1d4ed8', '#1e3a8a']

/** Hook helper para selecionar tema baseado no modo atual */
export function useNivoTheme(isDark?: boolean): NivoTheme {
  if (isDark === undefined) {
    // Detect from document class (Tailwind dark mode)
    const dark = typeof document !== 'undefined' && document.documentElement.classList.contains('dark')
    return dark ? passosNivoThemeDark : passosNivoTheme
  }
  return isDark ? passosNivoThemeDark : passosNivoTheme
}
