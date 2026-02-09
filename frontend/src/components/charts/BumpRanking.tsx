/**
 * BumpRanking.tsx — Nivo Bump Chart
 *
 * Mostra a evolução do ranking dos modelos por diferentes métricas.
 * Usa @nivo/bump para visualizar como a posição relativa dos modelos
 * muda conforme a métrica de avaliação (Recall, Precision, F1, F2, PR-AUC).
 */
import { ResponsiveBump } from '@nivo/bump'
import { useNivoTheme, passosPalette } from './NivoTheme'

export interface BumpSerie {
  id: string
  data: { x: string; y: number }[]
  [key: string]: unknown
}

interface BumpRankingProps {
  data: BumpSerie[]
  height?: number
}

export function BumpRanking({ data, height = 300 }: BumpRankingProps) {
  const theme = useNivoTheme()

  if (data.length === 0) return null

  return (
    <div style={{ height }}>
      <ResponsiveBump
        data={data}
        theme={theme}
        colors={passosPalette}
        lineWidth={3}
        activeLineWidth={5}
        inactiveLineWidth={2}
        inactiveOpacity={0.2}
        pointSize={8}
        activePointSize={14}
        inactivePointSize={0}
        pointBorderWidth={2}
        pointBorderColor={{ from: 'serie.color' }}
        pointColor={{ theme: 'background' }}
        axisTop={{
          tickSize: 5,
          tickPadding: 5,
          legend: '',
        }}
        axisBottom={{
          tickSize: 5,
          tickPadding: 5,
          legend: 'Métrica',
          legendPosition: 'middle',
          legendOffset: 36,
        }}
        axisLeft={{
          tickSize: 5,
          tickPadding: 5,
          legend: 'Ranking',
          legendPosition: 'middle',
          legendOffset: -40,
        }}
        margin={{ top: 30, right: 120, bottom: 50, left: 50 }}
      />
    </div>
  )
}
