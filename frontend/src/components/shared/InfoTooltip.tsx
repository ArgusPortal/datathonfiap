/**
 * InfoTooltip.tsx — Tooltip educativo com ícone (i)
 *
 * Componente essencial para o contexto acadêmico: cada métrica,
 * gráfico ou conceito técnico pode ter um InfoTooltip que explica
 * ao avaliador o que está sendo mostrado.
 *
 * Usa Radix UI Tooltip para acessibilidade (WCAG 2.1 AA).
 */
import { Info } from 'lucide-react'
import * as Tooltip from '@radix-ui/react-tooltip'
import { cn } from '@/lib/utils'

interface InfoTooltipProps {
  content: string
  side?: 'top' | 'right' | 'bottom' | 'left'
  className?: string
  iconClassName?: string
}

export function InfoTooltip({
  content,
  side = 'top',
  className,
  iconClassName,
}: InfoTooltipProps) {
  return (
    <Tooltip.Provider delayDuration={200}>
      <Tooltip.Root>
        <Tooltip.Trigger asChild>
          <button
            type="button"
            className={cn(
              'inline-flex items-center justify-center rounded-full p-0.5 text-muted-foreground/60 hover:text-muted-foreground transition-colors',
              className,
            )}
            aria-label="Informação"
          >
            <Info className={cn('h-3.5 w-3.5', iconClassName)} />
          </button>
        </Tooltip.Trigger>
        <Tooltip.Portal>
          <Tooltip.Content
            side={side}
            sideOffset={6}
            className="z-50 max-w-xs rounded-lg border bg-card px-3 py-2 text-xs text-muted-foreground shadow-lg animate-fade-in-up"
          >
            {content}
            <Tooltip.Arrow className="fill-card" />
          </Tooltip.Content>
        </Tooltip.Portal>
      </Tooltip.Root>
    </Tooltip.Provider>
  )
}
