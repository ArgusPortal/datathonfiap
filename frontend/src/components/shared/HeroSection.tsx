/**
 * HeroSection.tsx — Seção hero com gradiente Passos Mágicos
 *
 * Inspirado no hero do site passosmagicos.org.br:
 *  "Acreditamos em transformar vidas através da educação!"
 *
 * Para o projeto acadêmico, o hero contextualiza a ferramenta
 * como parte do ecossistema de transformação educacional da ONG.
 *
 * Props:
 *  - title: título principal (pode conter JSX para gradient-text)
 *  - subtitle: texto descritivo abaixo do título
 *  - badge: texto de badge opcional (ex: "Datathon FIAP 2025")
 *  - children: conteúdo extra (botões, stats inline, etc.)
 */
import { Sparkles } from 'lucide-react'
import { cn } from '@/lib/utils'

interface HeroSectionProps {
  title: string
  subtitle?: string
  badge?: string
  children?: React.ReactNode
  className?: string
  compact?: boolean
}

export function HeroSection({
  title,
  subtitle,
  badge,
  children,
  className,
  compact = false,
}: HeroSectionProps) {
  return (
    <div
      className={cn(
        'relative overflow-hidden rounded-2xl border bg-muted/30',
        compact ? 'p-6' : 'p-8 lg:p-10',
        className,
      )}
    >
      {/* Content */}
      <div className="relative z-10">
        {badge && (
          <div className="inline-flex items-center gap-1.5 rounded-full bg-primary/10 px-3 py-1 mb-4">
            <Sparkles className="h-3.5 w-3.5 text-primary" />
            <span className="text-xs font-semibold text-primary">
              {badge}
            </span>
          </div>
        )}

        <h1
          className={cn(
            'font-bold tracking-tight text-foreground',
            compact ? 'text-xl lg:text-2xl' : 'text-2xl lg:text-3xl',
          )}
        >
          {title}
        </h1>

        {subtitle && (
          <p
            className={cn(
              'mt-2 text-muted-foreground max-w-2xl',
              compact ? 'text-sm' : 'text-base',
            )}
          >
            {subtitle}
          </p>
        )}

        {children && <div className="mt-4">{children}</div>}
      </div>
    </div>
  )
}
