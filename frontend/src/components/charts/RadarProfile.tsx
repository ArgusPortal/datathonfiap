/**
 * RadarProfile.tsx — Nivo Radar Chart
 *
 * Compara perfis multidimensionais de alunos ou modelos.
 * Usado para visualizar indicadores (INDE, IAA, IEG, etc.)
 * de alunos alto-risco vs baixo-risco, ou comparar métricas de modelos.
 */
import { ResponsiveRadar } from '@nivo/radar'
import { useNivoTheme, passosPalette } from './NivoTheme'

export interface RadarDatum {
  indicator: string
  [key: string]: string | number
}

interface RadarProfileProps {
  data: RadarDatum[]
  keys: string[]
  indexBy?: string
  height?: number
  maxValue?: number | 'auto'
}

export function RadarProfile({
  data,
  keys,
  indexBy = 'indicator',
  height = 320,
  maxValue = 'auto',
}: RadarProfileProps) {
  const theme = useNivoTheme()

  return (
    <div style={{ height }}>
      <ResponsiveRadar
        data={data}
        keys={keys}
        indexBy={indexBy}
        theme={theme}
        colors={passosPalette}
        maxValue={maxValue}
        margin={{ top: 40, right: 80, bottom: 40, left: 80 }}
        borderColor={{ from: 'color' }}
        borderWidth={2}
        gridLevels={5}
        gridShape="circular"
        gridLabelOffset={16}
        dotSize={8}
        dotColor={{ theme: 'background' }}
        dotBorderWidth={2}
        dotBorderColor={{ from: 'color' }}
        fillOpacity={0.15}
        blendMode="multiply"
        animate={true}
        legends={[
          {
            anchor: 'top-left',
            direction: 'column',
            translateX: -50,
            translateY: -30,
            itemWidth: 100,
            itemHeight: 18,
            symbolSize: 10,
            symbolShape: 'circle',
          },
        ]}
        sliceTooltip={({ index, data: sliceData }) => (
          <div className="bg-card border rounded-lg shadow-md px-3 py-2 text-xs">
            <p className="font-semibold mb-1">{index}</p>
            {sliceData.map((d) => (
              <p key={d.id} className="flex items-center gap-2">
                <span
                  className="inline-block w-2 h-2 rounded-full"
                  style={{ backgroundColor: d.color }}
                />
                {d.id}: {typeof d.value === 'number' ? d.value.toFixed(2) : d.value}
              </p>
            ))}
          </div>
        )}
      />
    </div>
  )
}
