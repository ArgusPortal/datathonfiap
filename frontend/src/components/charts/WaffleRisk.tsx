/**
 * WaffleRisk.tsx — Nivo Waffle Chart
 *
 * Visualização de proporção de risco alto vs baixo/moderado.
 * Cada célula representa ~1% do total. Formato visual impactante
 * para apresentações e relatórios de impacto social.
 */
import { ResponsiveWaffle } from '@nivo/waffle'
import { useNivoTheme, riskPalette } from './NivoTheme'

interface WaffleRiskProps {
  low: number
  medium: number
  high: number
  total: number
  height?: number
}

export function WaffleRisk({ low, medium, high, total, height = 260 }: WaffleRiskProps) {
  const theme = useNivoTheme()

  const data = [
    { id: 'Baixo Risco', label: 'Baixo Risco (<30%)', value: low },
    { id: 'Risco Moderado', label: 'Risco Moderado (30-70%)', value: medium },
    { id: 'Alto Risco', label: 'Alto Risco (>70%)', value: high },
  ]

  return (
    <div style={{ height }}>
      <ResponsiveWaffle
        data={data}
        theme={theme}
        total={total}
        rows={10}
        columns={10}
        padding={2}
        colors={[riskPalette.low, riskPalette.medium, riskPalette.high]}
        borderRadius={3}
        margin={{ top: 10, right: 10, bottom: 10, left: 10 }}
        legends={[
          {
            anchor: 'bottom',
            direction: 'row',
            justify: false,
            translateX: 0,
            translateY: 0,
            itemsSpacing: 4,
            itemWidth: 120,
            itemHeight: 20,
            itemDirection: 'left-to-right',
            symbolSize: 14,
          },
        ]}
        motionStagger={2}
      />
    </div>
  )
}
