import { cn } from '@/lib/utils'
import type { RiskLevel } from '@/types'
import { getRiskColor } from '@/lib/utils'

interface RiskGaugeProps {
  score: number
  size?: 'sm' | 'md' | 'lg'
  showLabel?: boolean
  className?: string
}

export function RiskGauge({ score, size = 'md', showLabel = true, className }: RiskGaugeProps) {
  const level: RiskLevel = score >= 0.7 ? 'high' : score >= 0.3 ? 'medium' : 'low'
  const color = getRiskColor(level)
  const pct = Math.min(100, Math.max(0, score * 100))

  const sizes = {
    sm: { container: 'w-20 h-20', text: 'text-lg', label: 'text-[10px]' },
    md: { container: 'w-32 h-32', text: 'text-2xl', label: 'text-xs' },
    lg: { container: 'w-44 h-44', text: 'text-4xl', label: 'text-sm' },
  }

  const radius = size === 'sm' ? 32 : size === 'md' ? 52 : 72
  const strokeWidth = size === 'sm' ? 4 : 6
  const circumference = 2 * Math.PI * radius
  const strokeDashoffset = circumference - (pct / 100) * circumference * 0.75
  const viewSize = (radius + strokeWidth) * 2

  return (
    <div className={cn('flex flex-col items-center', className)}>
      <div className={cn('relative', sizes[size].container)}>
        <svg
          className="transform -rotate-135"
          viewBox={`0 0 ${viewSize} ${viewSize}`}
          fill="none"
        >
          {/* Background arc */}
          <circle
            cx={viewSize / 2}
            cy={viewSize / 2}
            r={radius}
            stroke="currentColor"
            strokeWidth={strokeWidth}
            strokeDasharray={`${circumference * 0.75} ${circumference * 0.25}`}
            className="text-muted"
            strokeLinecap="round"
            fill="none"
          />
          {/* Value arc */}
          <circle
            cx={viewSize / 2}
            cy={viewSize / 2}
            r={radius}
            stroke={color}
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            fill="none"
            className="transition-all duration-700 ease-out"
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={cn('font-bold', sizes[size].text)} style={{ color }}>
            {(score * 100).toFixed(0)}
          </span>
          {showLabel && (
            <span className={cn('text-muted-foreground', sizes[size].label)}>
              de 100
            </span>
          )}
        </div>
      </div>
    </div>
  )
}
