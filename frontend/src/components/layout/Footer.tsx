/**
 * Footer.tsx — Rodapé institucional
 *
 * Exibido em todas as páginas. Contém créditos do projeto,
 * link para a ONG, badge LGPD, ODS e versão.
 */
import { Heart, Shield, ExternalLink, GraduationCap } from 'lucide-react'

export function Footer() {
  const year = new Date().getFullYear()

  return (
    <footer className="border-t mt-8 py-5 px-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 text-[11px] text-muted-foreground">
        {/* Left — branding */}
        <div className="flex flex-col gap-1.5">
          <div className="flex items-center gap-1.5">
            <Heart className="h-3 w-3 text-red-400" />
            <span>
              Datathon FIAP {year} ·{' '}
              <a
                href="https://passosmagicos.org.br"
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary hover:underline inline-flex items-center gap-0.5"
              >
                Associação Passos Mágicos <ExternalLink className="h-2.5 w-2.5" />
              </a>
            </span>
          </div>
          <span className="text-[10px] opacity-70">
            <GraduationCap className="h-2.5 w-2.5 inline mr-0.5" />
            Desenvolvido por: Argus Portal · Pós-Graduação em Machine Learning Engineering (MLET5) — FIAP
          </span>
        </div>

        {/* Right — compliance & version */}
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1 px-2 py-0.5 rounded-full border border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-950/20 text-green-700 dark:text-green-400 text-[10px]">
            <Shield className="h-2.5 w-2.5" />
            LGPD Compliant
          </span>
          <span className="font-mono text-[10px] opacity-60">v2.0.0</span>
        </div>
      </div>
    </footer>
  )
}
