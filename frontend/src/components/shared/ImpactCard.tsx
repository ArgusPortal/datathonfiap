/**
 * ImpactCard.tsx — Card de impacto com número animado e ícone
 *
 * Design inspirado na seção "Impacto 2025" do passosmagicos.org.br
 * que exibe métricas-chave em cards visuais com números grandes.
 *
 * Cada card possui:
 *  - Ícone temático (Lucide)
 *  - Número com animação counter-up
 *  - Label descritivo
 *  - Tooltip educativo opcional
 *  - Variante de cor (blue, purple, orange, green, red)
 */
import { type LucideIcon, Info } from 'lucide-react'
import { CounterUpNumber } from './CounterUp'
import { cn } from '@/lib/utils'

type CardVariant = 'blue' | 'purple' | 'orange' | 'green' | 'red'

interface ImpactCardProps {
  icon: LucideIcon
  value: number
  label: string
  suffix?: string
  prefix?: string
  decimals?: number
  variant?: CardVariant
  tooltip?: string
  className?: string
}

const variantStyles: Record<CardVariant, { bg: string; iconBg: string; iconColor: string; border: string }> = {
  blue: {
    bg: 'bg-passos-50 dark:bg-passos-900/20',
    iconBg: 'bg-passos-100 dark:bg-passos-800/40',
    iconColor: 'text-passos-600 dark:text-passos-300',
    border: 'border-passos-200/50 dark:border-passos-700/30',
  },
  purple: {
    bg: 'bg-magic-50 dark:bg-magic-900/20',
    iconBg: 'bg-magic-100 dark:bg-magic-800/40',
    iconColor: 'text-magic-600 dark:text-magic-300',
    border: 'border-magic-200/50 dark:border-magic-700/30',
  },
  orange: {
    bg: 'bg-impact-50 dark:bg-orange-900/20',
    iconBg: 'bg-impact-100 dark:bg-orange-800/40',
    iconColor: 'text-impact-600 dark:text-orange-300',
    border: 'border-impact-200/50 dark:border-orange-700/30',
  },
  green: {
    bg: 'bg-green-50 dark:bg-green-900/20',
    iconBg: 'bg-green-100 dark:bg-green-800/40',
    iconColor: 'text-green-600 dark:text-green-300',
    border: 'border-green-200/50 dark:border-green-700/30',
  },
  red: {
    bg: 'bg-red-50 dark:bg-red-900/20',
    iconBg: 'bg-red-100 dark:bg-red-800/40',
    iconColor: 'text-red-600 dark:text-red-300',
    border: 'border-red-200/50 dark:border-red-700/30',
  },
}

export function ImpactCard({
  icon: Icon,
  value,
  label,
  suffix = '',
  prefix = '',
  decimals = 0,
  variant = 'blue',
  tooltip,
  className,
}: ImpactCardProps) {
  const styles = variantStyles[variant]

  return (
    <div
      className={cn(
        'relative rounded-xl border p-5 transition-all duration-300 hover:shadow-lg hover:-translate-y-1',
        styles.bg,
        styles.border,
        className,
      )}
    >
      {/* Ícone */}
      <div className={cn('flex h-10 w-10 items-center justify-center rounded-lg mb-3', styles.iconBg)}>
        <Icon className={cn('h-5 w-5', styles.iconColor)} />
      </div>

      {/* Número animado */}
      <div className="flex items-baseline gap-1">
        <CounterUpNumber
          end={value}
          prefix={prefix}
          suffix={suffix}
          decimals={decimals}
          className="text-2xl font-bold text-foreground"
        />
      </div>

      {/* Label */}
      <p className="mt-1 text-sm text-muted-foreground leading-tight">{label}</p>

      {/* Tooltip educativo */}
      {tooltip && (
        <div className="absolute top-3 right-3 group">
          <Info className="h-3.5 w-3.5 text-muted-foreground/50 cursor-help" />
          <div className="invisible group-hover:visible absolute right-0 top-5 z-10 w-52 rounded-lg bg-card border p-3 text-xs text-muted-foreground shadow-lg">
            {tooltip}
          </div>
        </div>
      )}
    </div>
  )
}
