/**
 * ODSBadge.tsx — Badge dos Objetivos de Desenvolvimento Sustentável da ONU
 *
 * A Associação Passos Mágicos alinha-se com 5 ODS:
 *  - ODS 1: Erradicação da Pobreza
 *  - ODS 4: Educação de Qualidade
 *  - ODS 5: Igualdade de Gênero
 *  - ODS 8: Trabalho Decente e Crescimento Econômico
 *  - ODS 10: Redução das Desigualdades
 *
 * Este componente renderiza badges individuais ou a lista completa.
 * Referência: https://brasil.un.org/pt-br/sdgs
 */
import { cn } from '@/lib/utils'

interface ODSInfo {
  number: number
  title: string
  color: string
  description: string
}

export const ODS_PASSOS_MAGICOS: ODSInfo[] = [
  {
    number: 1,
    title: 'Erradicação da Pobreza',
    color: '#e5243b',
    description: 'Acabar com a pobreza em todas as suas formas, em todos os lugares.',
  },
  {
    number: 4,
    title: 'Educação de Qualidade',
    color: '#c5192d',
    description: 'Assegurar a educação inclusiva e equitativa de qualidade.',
  },
  {
    number: 5,
    title: 'Igualdade de Gênero',
    color: '#ff3a21',
    description: 'Alcançar a igualdade de gênero e empoderar todas as mulheres e meninas.',
  },
  {
    number: 8,
    title: 'Trabalho Decente',
    color: '#a21942',
    description: 'Promover o crescimento econômico sustentado, inclusivo e sustentável.',
  },
  {
    number: 10,
    title: 'Redução das Desigualdades',
    color: '#dd1367',
    description: 'Reduzir a desigualdade dentro dos países e entre eles.',
  },
]

interface ODSBadgeProps {
  ods: ODSInfo
  size?: 'sm' | 'md' | 'lg'
  showTooltip?: boolean
  className?: string
}

export function ODSBadge({ ods, size = 'md', showTooltip = true, className }: ODSBadgeProps) {
  const sizeClasses = {
    sm: 'h-8 w-8 text-xs',
    md: 'h-10 w-10 text-sm',
    lg: 'h-14 w-14 text-base',
  }

  return (
    <div className={cn('group relative', className)}>
      <div
        className={cn(
          'flex items-center justify-center rounded-lg font-bold text-white shadow-sm transition-transform hover:scale-110',
          sizeClasses[size],
        )}
        style={{ backgroundColor: ods.color }}
        title={`ODS ${ods.number}: ${ods.title}`}
      >
        {ods.number}
      </div>
      {showTooltip && (
        <div className="invisible group-hover:visible absolute bottom-full left-1/2 -translate-x-1/2 mb-2 z-20 w-48 rounded-lg bg-card border p-2 text-xs shadow-lg">
          <p className="font-semibold text-foreground">ODS {ods.number}</p>
          <p className="text-muted-foreground mt-0.5">{ods.title}</p>
          <p className="text-muted-foreground/70 mt-1 text-[10px]">{ods.description}</p>
        </div>
      )}
    </div>
  )
}

interface ODSListProps {
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

export function ODSList({ size = 'md', className }: ODSListProps) {
  return (
    <div className={cn('flex items-center gap-2 flex-wrap', className)}>
      {ODS_PASSOS_MAGICOS.map((ods) => (
        <ODSBadge key={ods.number} ods={ods} size={size} />
      ))}
    </div>
  )
}
