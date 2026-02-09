import { cn } from '@/lib/utils'

interface StatusBadgeProps {
  status: 'healthy' | 'degraded' | 'offline' | boolean
  label?: string
  className?: string
}

export function StatusBadge({ status, label, className }: StatusBadgeProps) {
  const isOk = status === 'healthy' || status === true
  const isDegraded = status === 'degraded'

  const colorClass = isOk
    ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
    : isDegraded
    ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'
    : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'

  const dotClass = isOk
    ? 'bg-green-500'
    : isDegraded
    ? 'bg-amber-500'
    : 'bg-red-500'

  const defaultLabel = isOk ? 'Saudável' : isDegraded ? 'Degradado' : 'Offline'

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium',
        colorClass,
        className,
      )}
    >
      <span className={cn('h-1.5 w-1.5 rounded-full', dotClass, isOk && 'animate-pulse')} />
      {label ?? defaultLabel}
    </span>
  )
}

interface SLOIndicatorProps {
  label: string
  value: number | null
  target: number
  unit?: string
  inverted?: boolean // true = lower is better (latency)
}

export function SLOIndicator({ label, value, target, unit = '', inverted = false }: SLOIndicatorProps) {
  const ok = value != null && (inverted ? value <= target : value >= target)
  const displayValue = value != null ? `${value.toFixed(1)}${unit}` : 'N/A'

  return (
    <div
      className={cn(
        'flex items-center justify-between p-3 rounded-lg border',
        ok
          ? 'border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-950/20'
          : 'border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-950/20',
      )}
    >
      <div>
        <p className="text-xs text-muted-foreground">{label}</p>
        <p className="text-lg font-bold">{displayValue}</p>
      </div>
      <div className="text-right">
        <p className="text-[10px] text-muted-foreground">Meta</p>
        <p className={cn('text-sm font-medium', ok ? 'text-green-600' : 'text-red-600')}>
          {inverted ? '≤' : '≥'} {target}{unit}
        </p>
        <span className="text-lg">{ok ? '✅' : '❌'}</span>
      </div>
    </div>
  )
}
