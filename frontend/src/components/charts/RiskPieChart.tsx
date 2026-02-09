import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  Legend,
} from 'recharts'
import type { PredictionResult } from '@/types'
import { getRiskLevel, getRiskColor, getRiskLabel } from '@/lib/utils'

interface RiskPieChartProps {
  predictions: PredictionResult[]
  height?: number
}

export function RiskPieChart({ predictions, height = 280 }: RiskPieChartProps) {
  const counts = { low: 0, medium: 0, high: 0 }
  predictions.forEach((p) => {
    counts[getRiskLevel(p.risk_score)]++
  })

  const data = [
    { name: getRiskLabel('low'), value: counts.low, level: 'low' as const },
    { name: getRiskLabel('medium'), value: counts.medium, level: 'medium' as const },
    { name: getRiskLabel('high'), value: counts.high, level: 'high' as const },
  ].filter((d) => d.value > 0)

  return (
    <ResponsiveContainer width="100%" height={height}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={60}
          outerRadius={90}
          paddingAngle={4}
          dataKey="value"
          label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
          labelLine={false}
        >
          {data.map((entry) => (
            <Cell key={entry.name} fill={getRiskColor(entry.level)} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{
            backgroundColor: 'hsl(var(--card))',
            border: '1px solid hsl(var(--border))',
            borderRadius: '8px',
            fontSize: '13px',
          }}
          formatter={(value: number) => [`${value} alunos`, 'Total']}
        />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  )
}
