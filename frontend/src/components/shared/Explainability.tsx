import { useMemo } from 'react'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
  Badge,
  Progress,
} from '@/components/ui'
import { Info, ArrowRight, TrendingDown, TrendingUp } from 'lucide-react'
import type { StudentFeatures } from '@/types'
import { formatPercentage } from '@/lib/utils'

// ---------------------------------------------------------------------------
// Business-rules constants matching src/business_rules.py
// ---------------------------------------------------------------------------
const INDE_WEIGHTS: Record<string, { weight: number; label: string; fullName: string }> = {
  ian_2023: { weight: 0.1, label: 'IAN', fullName: 'Adequação de Nível' },
  ida_2023: { weight: 0.2, label: 'IDA', fullName: 'Desempenho Acadêmico' },
  ieg_2023: { weight: 0.2, label: 'IEG', fullName: 'Engajamento' },
  iaa_2023: { weight: 0.1, label: 'IAA', fullName: 'Autoavaliação' },
  ips_2023: { weight: 0.1, label: 'IPS', fullName: 'Psicossocial' },
  ipp_2023: { weight: 0.1, label: 'IPP', fullName: 'Psicopedagógico' },
  ipv_2023: { weight: 0.2, label: 'IPV', fullName: 'Ponto de Virada' },
}

const PEDRA_RANGES = [
  { name: 'Quartzo', min: 0, max: 6.1, color: 'bg-gray-200 dark:bg-gray-700', textColor: 'text-gray-700 dark:text-gray-300', emoji: '🪨' },
  { name: 'Ágata', min: 6.1, max: 7.2, color: 'bg-blue-200 dark:bg-blue-800', textColor: 'text-blue-700 dark:text-blue-300', emoji: '💎' },
  { name: 'Ametista', min: 7.2, max: 8.2, color: 'bg-purple-200 dark:bg-purple-800', textColor: 'text-purple-700 dark:text-purple-300', emoji: '🔮' },
  { name: 'Topázio', min: 8.2, max: 10, color: 'bg-yellow-200 dark:bg-yellow-800', textColor: 'text-yellow-700 dark:text-yellow-300', emoji: '🏆' },
]

const IAN_SCALE = [
  { level: 'Abaixo', range: '< 5.5', desc: 'Abaixo do nível esperado' },
  { level: 'Na média', range: '5.5 – 7.5', desc: 'Dentro do esperado' },
  { level: 'Acima', range: '> 7.5', desc: 'Acima do esperado' },
]

// ---------------------------------------------------------------------------
// SHAP-like waterfall chart (simplified, rule-based attribution)
// ---------------------------------------------------------------------------

interface WaterfallBar {
  feature: string
  label: string
  value: number
  contribution: number // positive = pushes toward risk, negative = reduces risk
  direction: 'risk' | 'protect'
}

function computeContributions(features: StudentFeatures, _riskScore?: number): WaterfallBar[] {
  const bars: WaterfallBar[] = []
  const threshold = 5.0 // below this → risk contributor

  const featureKeys = [
    { key: 'ian_2023', label: 'IAN', weight: 3 },
    { key: 'ida_2023', label: 'IDA', weight: 2.5 },
    { key: 'ieg_2023', label: 'IEG', weight: 2.5 },
    { key: 'ipv_2023', label: 'IPV', weight: 2 },
    { key: 'iaa_2023', label: 'IAA', weight: 1.5 },
    { key: 'ips_2023', label: 'IPS', weight: 1 },
    { key: 'ipp_2023', label: 'IPP', weight: 1 },
  ]

  for (const { key, label, weight } of featureKeys) {
    const val = features[key]
    if (typeof val !== 'number' || val == null) continue

    const deviation = val - threshold
    const contribution = deviation * weight * -0.02 // negative val → positive contribution to risk
    bars.push({
      feature: key,
      label,
      value: val,
      contribution: Math.max(-0.3, Math.min(0.3, contribution)),
      direction: contribution > 0 ? 'risk' : 'protect',
    })
  }

  // Add derived features
  const media = features.media_indicadores
  if (typeof media === 'number') {
    const deviation = media - threshold
    bars.push({
      feature: 'media_indicadores',
      label: 'Média Ind.',
      value: media,
      contribution: Math.max(-0.3, Math.min(0.3, deviation * -0.03)),
      direction: deviation < 0 ? 'risk' : 'protect',
    })
  }

  // Sort by absolute contribution
  bars.sort((a, b) => Math.abs(b.contribution) - Math.abs(a.contribution))

  return bars
}

export function ShapWaterfall({
  features,
  riskScore,
}: {
  features: StudentFeatures
  riskScore: number
}) {
  const bars = useMemo(() => computeContributions(features, riskScore), [features, riskScore])

  if (bars.length === 0) {
    return (
      <p className="text-xs text-muted-foreground text-center py-4">
        Dados insuficientes para análise de contribuição.
      </p>
    )
  }

  const maxAbs = Math.max(...bars.map((b) => Math.abs(b.contribution)), 0.01)

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between text-[10px] text-muted-foreground mb-2">
        <span className="flex items-center gap-1">
          <TrendingDown className="h-3 w-3 text-green-500" /> Reduz risco
        </span>
        <span className="flex items-center gap-1">
          Aumenta risco <TrendingUp className="h-3 w-3 text-red-500" />
        </span>
      </div>
      {bars.slice(0, 8).map((bar) => {
        const pct = (Math.abs(bar.contribution) / maxAbs) * 100
        const isRisk = bar.direction === 'risk'
        return (
          <div key={bar.feature} className="flex items-center gap-2">
            <span className="text-xs font-mono w-20 truncate text-right">{bar.label}</span>
            <span className="text-[10px] text-muted-foreground w-10 text-right">{bar.value.toFixed(1)}</span>
            <div className="flex-1 h-5 relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full h-[1px] bg-border" />
              </div>
              <div className="absolute inset-y-0 left-1/2 w-[1px] bg-border" />
              {isRisk ? (
                <div
                  className="absolute top-0.5 bottom-0.5 left-1/2 bg-red-400/80 dark:bg-red-500/60 rounded-r"
                  style={{ width: `${pct / 2}%` }}
                />
              ) : (
                <div
                  className="absolute top-0.5 bottom-0.5 bg-green-400/80 dark:bg-green-500/60 rounded-l"
                  style={{
                    right: '50%',
                    width: `${pct / 2}%`,
                  }}
                />
              )}
            </div>
            <span className={`text-[10px] font-mono w-12 ${isRisk ? 'text-red-600' : 'text-green-600'}`}>
              {isRisk ? '+' : ''}{(bar.contribution * 100).toFixed(1)}%
            </span>
          </div>
        )
      })}
      <div className="flex items-center justify-between text-xs mt-3 px-1">
        <span className="text-muted-foreground">Score final:</span>
        <span className="font-bold">{formatPercentage(riskScore)}</span>
      </div>
      <p className="text-[10px] text-muted-foreground italic mt-1 flex items-center gap-1">
        <Info className="h-3 w-3 shrink-0" />
        Contribuições aproximadas baseadas em regras de negócio. Não substituem análise SHAP real.
      </p>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Business Rules Visual
// ---------------------------------------------------------------------------

export function BusinessRulesCard() {
  return (
    <div className="space-y-6">
      {/* INDE Composition */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            📊 Composição do INDE
          </CardTitle>
          <CardDescription>
            Fórmula: INDE = IAN×0.1 + IDA×0.2 + IEG×0.2 + IAA×0.1 + IPS×0.1 + IPP×0.1 + IPV×0.2
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {Object.entries(INDE_WEIGHTS).map(([, info]) => (
              <div key={info.label} className="flex items-center gap-3">
                <span className="text-xs font-mono w-8 font-semibold">{info.label}</span>
                <span className="text-xs text-muted-foreground w-36 truncate">{info.fullName}</span>
                <Progress
                  value={info.weight}
                  max={0.2}
                  className="flex-1 h-4"
                  indicatorClassName={
                    info.weight >= 0.2
                      ? 'bg-primary'
                      : info.weight >= 0.15
                        ? 'bg-blue-500'
                        : 'bg-blue-300 dark:bg-blue-700'
                  }
                />
                <span className="text-xs font-mono w-10 text-right">
                  {(info.weight * 100).toFixed(0)}%
                </span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Pedra Classification */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            💎 Classificação Pedra
          </CardTitle>
          <CardDescription>
            Baseada no valor do INDE (0 a 10)
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex w-full h-12 rounded-lg overflow-hidden border">
            {PEDRA_RANGES.map((pedra) => {
              const widthPct = ((pedra.max - pedra.min) / 10) * 100
              return (
                <div
                  key={pedra.name}
                  className={`${pedra.color} flex items-center justify-center relative group`}
                  style={{ width: `${widthPct}%` }}
                >
                  <span className={`text-xs font-semibold ${pedra.textColor}`}>
                    {pedra.emoji} {pedra.name}
                  </span>
                  <span className="absolute -bottom-5 text-[9px] text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity">
                    {pedra.min}–{pedra.max}
                  </span>
                </div>
              )
            })}
          </div>
          <div className="flex justify-between mt-6 text-[10px] text-muted-foreground px-1">
            <span>0</span>
            <span>6.1</span>
            <span>7.2</span>
            <span>8.2</span>
            <span>10</span>
          </div>

          {/* Legend */}
          <div className="grid grid-cols-2 gap-2 mt-4">
            {PEDRA_RANGES.map((pedra) => (
              <div key={pedra.name} className="flex items-center gap-2 text-xs">
                <span>{pedra.emoji}</span>
                <span className="font-medium">{pedra.name}</span>
                <span className="text-muted-foreground">
                  ({pedra.min.toFixed(1)} – {pedra.max.toFixed(1)})
                </span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* IAN Scale */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            📏 Escala IAN
          </CardTitle>
          <CardDescription>
            Indicador de Adequação de Nível — referência de interpretação
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {IAN_SCALE.map((level) => (
              <div
                key={level.level}
                className="flex items-center gap-3 p-2 rounded-lg hover:bg-muted/50"
              >
                <Badge
                  variant={
                    level.level === 'Abaixo' ? 'destructive' :
                    level.level === 'Na média' ? 'secondary' :
                    'default'
                  }
                  className="w-20 justify-center"
                >
                  {level.level}
                </Badge>
                <span className="text-xs font-mono text-muted-foreground w-16">{level.range}</span>
                <span className="text-xs">{level.desc}</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Risk pipeline */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            🔄 Pipeline de Decisão
          </CardTitle>
          <CardDescription>
            Fluxo simplificado desde os dados até a recomendação
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center flex-wrap gap-2">
            {[
              { label: 'Indicadores\n(IAN, IEG, etc.)', emoji: '📋' },
              { label: 'Modelo ML\n(RandomForest + Calibração)', emoji: '🧠' },
              { label: 'Score\nde Risco', emoji: '📊' },
              { label: 'Threshold\n(0.2814)', emoji: '🎚️' },
              { label: 'Classificação\n(Risco/Seguro)', emoji: '🏷️' },
              { label: 'Ação\nPedagógica', emoji: '🎯' },
            ].map((step, i, arr) => (
              <div key={step.label} className="flex items-center gap-2">
                <div className="flex flex-col items-center text-center p-3 rounded-lg border bg-muted/30 min-w-[90px]">
                  <span className="text-lg mb-1">{step.emoji}</span>
                  <span className="text-[10px] leading-tight whitespace-pre-line">{step.label}</span>
                </div>
                {i < arr.length - 1 && (
                  <ArrowRight className="h-4 w-4 text-muted-foreground shrink-0" />
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
