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
        'relative overflow-hidden rounded-2xl border',
        compact ? 'p-6' : 'p-8 lg:p-10',
        className,
      )}
    >
      {/* Background gradient */}
      <div className="absolute inset-0 pm-hero-gradient opacity-90 dark:opacity-70" />

      {/* Decorative elements */}
      <div className="absolute -top-12 -right-12 h-40 w-40 rounded-full bg-magic-500/10 blur-3xl" />
      <div className="absolute -bottom-8 -left-8 h-32 w-32 rounded-full bg-passos-500/10 blur-3xl" />

      {/* Content */}
      <div className="relative z-10">
        {badge && (
          <div className="inline-flex items-center gap-1.5 rounded-full bg-passos-500/10 dark:bg-passos-500/20 px-3 py-1 mb-4">
            <Sparkles className="h-3.5 w-3.5 text-passos-500" />
            <span className="text-xs font-semibold text-passos-600 dark:text-passos-300">
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
          <span className="gradient-text">{title}</span>
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
