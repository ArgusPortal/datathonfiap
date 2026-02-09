import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts'
import type { PredictionResult } from '@/types'
import { getRiskLevel, getRiskColor } from '@/lib/utils'

interface ScoreDistributionProps {
  predictions: PredictionResult[]
  height?: number
}

export function ScoreDistribution({ predictions, height = 250 }: ScoreDistributionProps) {
  // Create histogram bins
  const bins = [
    { range: '0-10', min: 0, max: 0.1, count: 0 },
    { range: '10-20', min: 0.1, max: 0.2, count: 0 },
    { range: '20-30', min: 0.2, max: 0.3, count: 0 },
    { range: '30-40', min: 0.3, max: 0.4, count: 0 },
    { range: '40-50', min: 0.4, max: 0.5, count: 0 },
    { range: '50-60', min: 0.5, max: 0.6, count: 0 },
    { range: '60-70', min: 0.6, max: 0.7, count: 0 },
    { range: '70-80', min: 0.7, max: 0.8, count: 0 },
    { range: '80-90', min: 0.8, max: 0.9, count: 0 },
    { range: '90-100', min: 0.9, max: 1.01, count: 0 },
  ]

  predictions.forEach((p) => {
    const bin = bins.find((b) => p.risk_score >= b.min && p.risk_score < b.max)
    if (bin) bin.count++
  })

  const getBarColor = (range: string) => {
    const midpoint = (bins.find(b => b.range === range)!.min + bins.find(b => b.range === range)!.max) / 2
    return getRiskColor(getRiskLevel(midpoint))
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={bins} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
        <XAxis
          dataKey="range"
          tick={{ fontSize: 11 }}
          className="text-muted-foreground"
        />
        <YAxis
          tick={{ fontSize: 11 }}
          className="text-muted-foreground"
          allowDecimals={false}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: 'hsl(var(--card))',
            border: '1px solid hsl(var(--border))',
            borderRadius: '8px',
            fontSize: '13px',
          }}
          formatter={(value: number) => [`${value} alunos`, 'Quantidade']}
          labelFormatter={(label) => `Score: ${label}%`}
        />
        <Bar dataKey="count" radius={[4, 4, 0, 0]}>
          {bins.map((entry) => (
            <Cell key={entry.range} fill={getBarColor(entry.range)} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
