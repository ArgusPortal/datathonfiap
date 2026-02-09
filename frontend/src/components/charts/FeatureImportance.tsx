/**
 * FeatureImportance.tsx — Nivo Horizontal Bar Chart
 *
 * Mostra a importância relativa de cada feature no modelo.
 * Bar chart horizontal, ordenado por importância.
 * Substitui a versão anterior baseada em Progress bars.
 */
import { ResponsiveBar } from '@nivo/bar'
import { useNivoTheme, passosPalette } from './NivoTheme'

export interface FeatureImportanceDatum {
  feature: string
  importance: number
  [key: string]: string | number
}

interface FeatureImportanceProps {
  data: FeatureImportanceDatum[]
  height?: number
}

export function FeatureImportance({ data, height = 350 }: FeatureImportanceProps) {
  const theme = useNivoTheme()

  const sorted = [...data].sort((a, b) => a.importance - b.importance)

  return (
    <div style={{ height }}>
      <ResponsiveBar
        data={sorted}
        theme={theme}
        keys={['importance']}
        indexBy="feature"
        layout="horizontal"
        colors={[passosPalette[0]]}
        margin={{ top: 10, right: 40, bottom: 50, left: 110 }}
        padding={0.3}
        borderRadius={4}
        valueScale={{ type: 'linear' }}
        indexScale={{ type: 'band', round: true }}
        axisBottom={{
          legend: 'Importância Relativa',
          legendOffset: 40,
          legendPosition: 'middle',
          format: (v: number) => `${(v * 100).toFixed(0)}%`,
        }}
        axisLeft={{
          tickSize: 0,
          tickPadding: 8,
        }}
        enableLabel={true}
        label={(d) => `${((d.value ?? 0) * 100).toFixed(0)}%`}
        labelSkipWidth={30}
        labelTextColor="#ffffff"
        enableGridY={false}
        tooltip={({ value, indexValue }) => (
          <div className="bg-card border rounded-lg shadow-md px-3 py-2 text-xs">
            <p className="font-semibold">{indexValue}</p>
            <p>Importância: {((value ?? 0) * 100).toFixed(1)}%</p>
          </div>
        )}
      />
    </div>
  )
}
