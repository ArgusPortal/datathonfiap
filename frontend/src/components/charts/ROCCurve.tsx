/**
 * ROCCurve.tsx — Curva ROC com Nivo Line
 *
 * Visualiza a curva ROC (Receiver Operating Characteristic) do modelo.
 * Mostra a relação entre TPR (Recall) e FPR para diferentes thresholds.
 * A diagonal cinza representa um classificador aleatório (AUC=0.5).
 */
import { ResponsiveLine } from '@nivo/line'
import { useNivoTheme, passosPalette } from './NivoTheme'

export interface ROCPoint {
  fpr: number
  tpr: number
}

interface ROCCurveProps {
  points: ROCPoint[]
  auc?: number
  height?: number
}

export function ROCCurve({ points, auc, height = 320 }: ROCCurveProps) {
  const theme = useNivoTheme()

  const lineData = [
    {
      id: `ROC Curve${auc != null ? ` (AUC=${auc.toFixed(3)})` : ''}`,
      data: points.map((p) => ({ x: p.fpr, y: p.tpr })),
    },
    {
      id: 'Random (AUC=0.500)',
      data: [
        { x: 0, y: 0 },
        { x: 1, y: 1 },
      ],
    },
  ]

  return (
    <div style={{ height }}>
      <ResponsiveLine
        data={lineData}
        theme={theme}
        colors={[passosPalette[0], '#d1d5db']}
        margin={{ top: 20, right: 20, bottom: 60, left: 60 }}
        xScale={{ type: 'linear', min: 0, max: 1 }}
        yScale={{ type: 'linear', min: 0, max: 1 }}
        axisBottom={{
          legend: 'Taxa de Falso Positivo (FPR)',
          legendOffset: 46,
          legendPosition: 'middle',
          format: (v: number) => `${(v * 100).toFixed(0)}%`,
        }}
        axisLeft={{
          legend: 'Taxa de Verdadeiro Positivo (TPR)',
          legendOffset: -48,
          legendPosition: 'middle',
          format: (v: number) => `${(v * 100).toFixed(0)}%`,
        }}
        lineWidth={3}
        pointSize={0}
        enableArea={true}
        areaOpacity={0.08}
        useMesh={true}
        enableCrosshair={true}
        legends={[
          {
            anchor: 'bottom-right',
            direction: 'column',
            translateX: 0,
            translateY: -10,
            itemWidth: 160,
            itemHeight: 20,
            symbolSize: 10,
            symbolShape: 'circle',
          },
        ]}
        tooltip={({ point }) => (
          <div className="bg-card border rounded-lg shadow-md px-3 py-2 text-xs">
            <p className="font-semibold">{point.seriesId}</p>
            <p>FPR: {((point.data.x as number) * 100).toFixed(1)}%</p>
            <p>TPR: {((point.data.y as number) * 100).toFixed(1)}%</p>
          </div>
        )}
      />
    </div>
  )
}
