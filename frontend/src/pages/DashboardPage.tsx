/**
 * DashboardPage.tsx — Dashboard Principal (v2)
 *
 * Redesign completo inspirado no site passosmagicos.org.br:
 *  • Hero Section com gradiente PM + badge Datathon
 *  • Impact Cards com animação counter-up (ONG style)
 *  • ODS da ONU badges
 *  • Charts (Score Distribution + Risk Pie)
 *  • System Status + SLO Compliance
 *  • Legendas didáticas para avaliação acadêmica
 */
import { useEffect, useState, useCallback, useMemo } from 'react'
import {
  Activity,
  AlertTriangle,
  BarChart3,
  Clock,
  Heart,
  TrendingUp,
  Users,
  Zap,
  ShieldAlert,
  Target,
  Gauge,
  Brain,
  GraduationCap,
  Sparkles,
} from 'lucide-react'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
  Skeleton,
  Badge,
  Separator,
} from '@/components/ui'
import { StatusBadge } from '@/components/shared/StatusBadge'
import { HeroSection } from '@/components/shared/HeroSection'
import { ImpactCard } from '@/components/shared/ImpactCard'
import { InfoTooltip } from '@/components/shared/InfoTooltip'
import { ODSList } from '@/components/shared/ODSBadge'
import { ScoreDistribution } from '@/components/charts/ScoreDistribution'
import { RiskPieChart } from '@/components/charts/RiskPieChart'
import api from '@/services/api'
import { usePredictionStore } from '@/stores/predictionStore'
import type {
  HealthResponse,
  MetricsResponse,
  SLOResponse,
  DriftStatus,
  InferenceEvent,
  PredictionResult,
} from '@/types'
import {
  formatMs,
  formatUptime,
  formatPercentage,
  getDriftStatusColor,
  getDriftStatusBg,
} from '@/lib/utils'

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const REFRESH_INTERVAL = 15_000

function driftEmoji(status: string): string {
  switch (status) {
    case 'green': return '🟢'
    case 'yellow': return '🟡'
    case 'red': return '🔴'
    default: return '⚪'
  }
}

function driftLabel(status: string): string {
  switch (status) {
    case 'green': return 'Estável'
    case 'yellow': return 'Atenção'
    case 'red': return 'Drift Detectado'
    default: return 'Sem dados'
  }
}

function synthesisePredictionsFromHistory(events: InferenceEvent[]): PredictionResult[] {
  const results: PredictionResult[] = []
  for (const ev of events) {
    const bins = ev.prediction_summary.score_bins
    const version = ev.model_version
    for (let i = 0; i < bins.low; i++)
      results.push({ risk_score: 0.1 + Math.random() * 0.2, risk_label: 0, model_version: version })
    for (let i = 0; i < bins.medium; i++)
      results.push({ risk_score: 0.3 + Math.random() * 0.4, risk_label: 0, model_version: version })
    for (let i = 0; i < bins.high; i++)
      results.push({ risk_score: 0.7 + Math.random() * 0.3, risk_label: 1, model_version: version })
  }
  return results
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function DashboardPage() {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null)
  const [slo, setSlo] = useState<SLOResponse | null>(null)
  const [drift, setDrift] = useState<DriftStatus | null>(null)
  const [inferenceEvents, setInferenceEvents] = useState<InferenceEvent[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const { predictions: storePredictions } = usePredictionStore()

  const errorRate = metrics
    ? metrics.requests.total > 0 ? metrics.requests.error / metrics.requests.total : 0
    : null

  const highRiskRate = metrics
    ? metrics.predictions.total > 0 ? metrics.predictions.positive / metrics.predictions.total : 0
    : null

  const latencyP95 = metrics?.latency_ms.p95 ?? null

  const historyAggregates = useMemo(() => {
    if (inferenceEvents.length === 0) return null
    let totalPredictions = 0, totalHighRisk = 0, scoreSum = 0
    for (const ev of inferenceEvents) {
      totalPredictions += ev.prediction_summary.n_predictions
      totalHighRisk += ev.prediction_summary.n_high_risk
      scoreSum += ev.prediction_summary.mean_score * ev.prediction_summary.n_predictions
    }
    return {
      totalPredictions, totalHighRisk,
      highRiskRate: totalPredictions > 0 ? totalHighRisk / totalPredictions : 0,
      meanScore: totalPredictions > 0 ? scoreSum / totalPredictions : 0,
    }
  }, [inferenceEvents])

  const chartPredictions: PredictionResult[] = useMemo(() => {
    if (storePredictions.length > 0) return storePredictions
    if (inferenceEvents.length > 0) return synthesisePredictionsFromHistory(inferenceEvents)
    return []
  }, [storePredictions, inferenceEvents])

  const hasChartData = chartPredictions.length > 0

  const kpiHighRiskRate = storePredictions.length > 0
    ? storePredictions.filter((p) => p.risk_label === 1).length / storePredictions.length
    : historyAggregates?.highRiskRate ?? (highRiskRate ?? 0)
  const kpiMeanScore = storePredictions.length > 0
    ? storePredictions.reduce((s, p) => s + p.risk_score, 0) / storePredictions.length
    : historyAggregates?.meanScore ?? 0
  const kpiTotalScored = storePredictions.length > 0
    ? storePredictions.length
    : historyAggregates?.totalPredictions ?? (metrics?.predictions.total ?? 0)

  const alertHighErrorRate = errorRate !== null && errorRate > 0.01
  const alertHighLatency = latencyP95 !== null && latencyP95 > 300
  const alertDriftRed = drift?.overall_status === 'red'

  const fetchAll = useCallback(async () => {
    try {
      const [h, m, s, d, inf] = await Promise.allSettled([
        api.health(), api.metrics(), api.slo(), api.driftStatus(), api.inferenceHistory(200),
      ])
      if (h.status === 'fulfilled') setHealth(h.value)
      if (m.status === 'fulfilled') setMetrics(m.value)
      if (s.status === 'fulfilled') setSlo(s.value)
      if (d.status === 'fulfilled') setDrift(d.value)
      if (inf.status === 'fulfilled') setInferenceEvents(inf.value.events)
      setError(null)
    } catch {
      setError('Não foi possível conectar à API')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchAll()
    const interval = setInterval(fetchAll, REFRESH_INTERVAL)
    return () => clearInterval(interval)
  }, [fetchAll])

  const driftedFeatureCount = useMemo(() => {
    if (!drift?.features) return 0
    return Object.values(drift.features).filter((f: { status: string }) => f.status === 'red' || f.status === 'yellow').length
  }, [drift])

  // ========================================================================
  // RENDER
  // ========================================================================
  return (
    <div className="space-y-6">
      {/* HERO SECTION */}
      <HeroSection
        title="Predição de Risco de Defasagem Escolar"
        subtitle="Transformando dados em oportunidades educacionais — Sistema inteligente que identifica alunos em risco para intervenção precoce da Associação Passos Mágicos."
        badge="Datathon FIAP 2025"
      >
        <div className="flex flex-wrap items-center gap-3">
          <StatusBadge status={health?.status ?? 'offline'} />
          {slo && (
            <Badge variant={slo.overall_healthy ? 'default' : 'destructive'} className="text-xs">
              SLO {slo.overall_healthy ? '✓ Saudável' : '✗ Violado'}
            </Badge>
          )}
          {drift && (
            <Badge
              variant={drift.overall_status === 'green' ? 'default' : drift.overall_status === 'yellow' ? 'secondary' : 'destructive'}
              className="text-xs"
            >
              {driftEmoji(drift.overall_status)} {driftLabel(drift.overall_status)}
            </Badge>
          )}
          <span className="text-xs text-muted-foreground">
            Modelo <span className="font-mono font-semibold">{health?.model_version ?? '—'}</span>
          </span>
        </div>
      </HeroSection>

      {/* ALERT BANNERS */}
      {error && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 dark:border-amber-800 dark:bg-amber-950/20 p-4">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-amber-600" />
            <p className="text-sm text-amber-800 dark:text-amber-400">{error}</p>
          </div>
        </div>
      )}
      {alertHighErrorRate && (
        <div className="rounded-lg border border-red-300 bg-red-50 dark:border-red-800 dark:bg-red-950/20 p-4 flex items-center gap-3">
          <ShieldAlert className="h-5 w-5 text-red-600 shrink-0" />
          <div>
            <p className="text-sm font-semibold text-red-800 dark:text-red-400">Taxa de erro elevada: {formatPercentage(errorRate!)}</p>
            <p className="text-xs text-red-600 dark:text-red-500">Meta SLO: ≤ {slo ? formatPercentage(slo.error_rate_slo) : '1%'}</p>
          </div>
        </div>
      )}
      {alertHighLatency && (
        <div className="rounded-lg border border-amber-300 bg-amber-50 dark:border-amber-800 dark:bg-amber-950/20 p-4 flex items-center gap-3">
          <Clock className="h-5 w-5 text-amber-600 shrink-0" />
          <div>
            <p className="text-sm font-semibold text-amber-800 dark:text-amber-400">Latência p95 alta: {formatMs(latencyP95!)}</p>
            <p className="text-xs text-amber-600 dark:text-amber-500">Meta: ≤ {slo?.latency_slo_ms ?? 300}ms</p>
          </div>
        </div>
      )}
      {alertDriftRed && (
        <div className="rounded-lg border border-red-300 bg-red-50 dark:border-red-800 dark:bg-red-950/20 p-4 flex items-center gap-3">
          <AlertTriangle className="h-5 w-5 text-red-600 shrink-0" />
          <div>
            <p className="text-sm font-semibold text-red-800 dark:text-red-400">🔴 Drift crítico — {driftedFeatureCount} feature(s)</p>
            <p className="text-xs text-red-600 dark:text-red-500">Modelo pode gerar predições imprecisas. Avalie retreino.</p>
          </div>
        </div>
      )}

      {/* IMPACT CARDS */}
      <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-4">
        <ImpactCard
          icon={Users} value={kpiTotalScored} label="Alunos Avaliados" variant="blue"
          tooltip="Total de alunos que passaram pelo modelo de predição. Cada avaliação gera um score de risco entre 0 e 1."
        />
        <ImpactCard
          icon={AlertTriangle} value={Number((kpiHighRiskRate * 100).toFixed(1))} suffix="%" decimals={1}
          label="Taxa de Alto Risco" variant="red"
          tooltip="Percentual de alunos classificados como alto risco (score > 0.7). Meta institucional: reduzir para < 20%."
        />
        <ImpactCard
          icon={Target} value={Number((kpiMeanScore * 100).toFixed(1))} suffix="%" decimals={1}
          label="Score Médio de Risco" variant="orange"
          tooltip="Média dos scores de risco. Quanto menor, melhor. Score = probabilidade de defasagem escolar."
        />
        <ImpactCard
          icon={Brain} value={93.5} suffix="%" decimals={1}
          label="Recall do Modelo" variant="purple"
          tooltip="Recall = capacidade de identificar alunos em risco real. 93.5% significa que captura ~94 de cada 100 em risco."
        />
      </div>

      {/* ODS DA ONU */}
      <Card>
        <CardContent className="p-5">
          <div className="flex flex-col sm:flex-row sm:items-center gap-4">
            <div className="flex-1">
              <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
                <GraduationCap className="h-4 w-4 text-primary" />
                Objetivos de Desenvolvimento Sustentável
                <InfoTooltip content="A Associação Passos Mágicos contribui com 5 dos 17 ODS da ONU, focando em educação, igualdade e redução da pobreza." />
              </h3>
              <p className="text-xs text-muted-foreground mt-1">
                Este projeto contribui com 5 ODS da ONU, alinhando tecnologia de dados com impacto social.
              </p>
            </div>
            <ODSList size="md" />
          </div>
        </CardContent>
      </Card>

      {/* OPERATIONAL STATS */}
      <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-4">
        <Card className="card-hover">
          <CardContent className="p-4 flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-passos-100 dark:bg-passos-800/40">
              <Activity className="h-4 w-4 text-passos-600 dark:text-passos-300" />
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Total Requisições</p>
              {loading ? <Skeleton className="h-5 w-16 mt-0.5" /> : (
                <><p className="text-lg font-bold">{metrics?.requests.total.toLocaleString() ?? '—'}</p>
                {metrics && <p className="text-[10px] text-muted-foreground">{metrics.requests.rate_per_minute.toFixed(1)} req/min</p>}</>
              )}
            </div>
          </CardContent>
        </Card>
        <Card className="card-hover">
          <CardContent className="p-4 flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-magic-100 dark:bg-magic-800/40">
              <Clock className="h-4 w-4 text-magic-600 dark:text-magic-300" />
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Latência p95</p>
              {loading ? <Skeleton className="h-5 w-16 mt-0.5" /> : (
                <><p className="text-lg font-bold">{latencyP95 != null ? formatMs(latencyP95) : '—'}</p>
                <p className="text-[10px] text-muted-foreground">Meta: ≤{slo?.latency_slo_ms ?? 300}ms</p></>
              )}
            </div>
          </CardContent>
        </Card>
        <Card className="card-hover">
          <CardContent className="p-4 flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-red-100 dark:bg-red-800/40">
              <AlertTriangle className="h-4 w-4 text-red-600 dark:text-red-300" />
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Taxa de Erro</p>
              {loading ? <Skeleton className="h-5 w-16 mt-0.5" /> : (
                <><p className="text-lg font-bold">{errorRate != null ? formatPercentage(errorRate) : '—'}</p>
                <p className="text-[10px] text-muted-foreground">Meta: ≤{slo ? formatPercentage(slo.error_rate_slo) : '1%'}</p></>
              )}
            </div>
          </CardContent>
        </Card>
        <Card className="card-hover">
          <CardContent className="p-4 flex items-center gap-3">
            <div className={`flex h-9 w-9 items-center justify-center rounded-lg ${getDriftStatusBg(drift?.overall_status ?? 'unknown')}`}>
              <ShieldAlert className={`h-4 w-4 ${getDriftStatusColor(drift?.overall_status ?? 'unknown')}`} />
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Drift do Modelo</p>
              {loading ? <Skeleton className="h-5 w-16 mt-0.5" /> : drift ? (
                <div className="flex items-center gap-1.5">
                  <span>{driftEmoji(drift.overall_status)}</span>
                  <span className={`text-sm font-semibold ${getDriftStatusColor(drift.overall_status)}`}>{driftLabel(drift.overall_status)}</span>
                </div>
              ) : <p className="text-sm text-muted-foreground">Indisponível</p>}
            </div>
          </CardContent>
        </Card>
      </div>

      <Separator />

      {/* CHARTS */}
      <div className="grid gap-6 grid-cols-1 lg:grid-cols-2">
        <Card className="card-hover">
          <CardHeader>
            <div className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4 text-primary" />
              <CardTitle>Distribuição de Scores de Risco</CardTitle>
              <InfoTooltip content="Histograma dos scores produzidos pelo HistGradientBoosting. Scores > 70% = alto risco de defasagem escolar." />
            </div>
            <CardDescription className="mt-1">
              {storePredictions.length > 0
                ? `${storePredictions.length} predições do store local`
                : inferenceEvents.length > 0 ? `Estimado via ${inferenceEvents.length} eventos` : 'Aguardando dados'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? <Skeleton className="h-[250px]" /> : hasChartData ? (
              <ScoreDistribution predictions={chartPredictions} />
            ) : (
              <div className="flex flex-col items-center justify-center h-[250px] text-muted-foreground">
                <Sparkles className="h-8 w-8 mb-2 text-muted-foreground/40" />
                <p className="text-sm">Nenhuma predição disponível</p>
                <p className="text-xs mt-1">Faça predições na aba &quot;Predição&quot;</p>
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="card-hover">
          <CardHeader>
            <div className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-primary" />
              <CardTitle>Classificação de Risco</CardTitle>
              <InfoTooltip content="Proporção por faixa: Baixo (<30%), Moderado (30–70%) e Alto (>70%). Faixas definidas pelo threshold calibrado." />
            </div>
            <CardDescription className="mt-1">Proporção por faixa — priorização de intervenções pedagógicas</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? <Skeleton className="h-[280px]" /> : hasChartData ? (
              <RiskPieChart predictions={chartPredictions} />
            ) : (
              <div className="flex flex-col items-center justify-center h-[280px] text-muted-foreground">
                <Sparkles className="h-8 w-8 mb-2 text-muted-foreground/40" />
                <p className="text-sm">Sem dados de classificação</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* DRIFT DETAILS */}
      {drift && drift.features && Object.keys(drift.features).length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <ShieldAlert className="h-4 w-4 text-primary" />
              <CardTitle>Drift por Feature</CardTitle>
              <InfoTooltip content="PSI (Population Stability Index) mede mudança na distribuição. Verde < 0.1, Amarelo 0.1–0.25, Vermelho > 0.25." />
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid gap-2 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
              {Object.entries(drift.features).map(([feature, info]) => (
                <div key={feature} className={`flex items-center justify-between rounded-lg border p-3 ${getDriftStatusBg(info.status)}`}>
                  <span className="text-sm font-mono truncate mr-2">{feature}</span>
                  <div className="flex items-center gap-2 shrink-0">
                    <span className="text-xs text-muted-foreground">PSI {info.psi.toFixed(3)}</span>
                    <span>{driftEmoji(info.status)}</span>
                  </div>
                </div>
              ))}
            </div>
            {drift.score_drift && (
              <div className="mt-3 flex items-center gap-3 text-sm">
                <span className="font-medium">Score drift:</span>
                <span>{driftEmoji(drift.score_drift.status)}</span>
                <span className={getDriftStatusColor(drift.score_drift.status)}>
                  {drift.score_drift.status === 'insufficient_data' ? 'Dados insuficientes' : `PSI ${drift.score_drift.psi.toFixed(3)}`}
                </span>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* SLO COMPLIANCE */}
      {slo && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Activity className="h-4 w-4 text-primary" />
              <CardTitle>Compliance SLO</CardTitle>
              <InfoTooltip content="SLO (Service Level Objectives) = metas de qualidade. Framework SRE do Google aplicado a ML em produção." />
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 grid-cols-1 sm:grid-cols-3">
              <div className="flex items-center justify-between p-4 rounded-lg border bg-card">
                <div>
                  <p className="text-xs text-muted-foreground">Latência p95</p>
                  <p className="text-lg font-bold">{slo.latency_p95_ms?.toFixed(0) ?? 'N/A'}ms</p>
                  <p className="text-xs text-muted-foreground">Meta: ≤{slo.latency_slo_ms}ms</p>
                </div>
                <div className="text-2xl">{slo.latency_slo_met ? '✅' : '❌'}</div>
              </div>
              <div className="flex items-center justify-between p-4 rounded-lg border bg-card">
                <div>
                  <p className="text-xs text-muted-foreground">Taxa de Erro</p>
                  <p className="text-lg font-bold">{formatPercentage(slo.error_rate)}</p>
                  <p className="text-xs text-muted-foreground">Meta: ≤{formatPercentage(slo.error_rate_slo)}</p>
                </div>
                <div className="text-2xl">{slo.error_rate_slo_met ? '✅' : '❌'}</div>
              </div>
              <div className="flex items-center justify-between p-4 rounded-lg border bg-card">
                <div>
                  <p className="text-xs text-muted-foreground">Status Geral</p>
                  <p className="text-lg font-bold">{slo.overall_healthy ? 'Saudável' : 'Degradado'}</p>
                </div>
                <div className="text-2xl">{slo.overall_healthy ? '🟢' : '🔴'}</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* STATUS BAR */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-3">
              <Heart className="h-5 w-5 text-primary" />
              <span className="text-sm font-medium">Sistema:</span>
              <StatusBadge status={health?.status ?? 'offline'} />
            </div>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Clock className="h-4 w-4" />
              Uptime: {health ? formatUptime(health.uptime_seconds) : '—'}
            </div>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Zap className="h-4 w-4" />
              Modelo: {health?.model_version ?? '—'}
            </div>
            {inferenceEvents.length > 0 && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground ml-auto">
                <Activity className="h-4 w-4" />
                {inferenceEvents.length} evento(s) recentes
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* INFO CARDS — Explicações acadêmicas */}
      <div className="grid gap-4 grid-cols-1 md:grid-cols-3">
        <Card className="card-hover border-passos-200/50 dark:border-passos-800/30">
          <CardContent className="p-5">
            <h3 className="font-semibold text-sm flex items-center gap-2 mb-2">
              <Target className="h-4 w-4 text-passos-500" />
              Objetivo do Modelo
            </h3>
            <p className="text-xs text-muted-foreground leading-relaxed">
              Predizer risco de defasagem escolar para alunos da Passos Mágicos,
              permitindo intervenção precoce. Utiliza <strong>HistGradientBoosting</strong> com 7 indicadores educacionais.
            </p>
          </CardContent>
        </Card>
        <Card className="card-hover border-magic-200/50 dark:border-magic-800/30">
          <CardContent className="p-5">
            <h3 className="font-semibold text-sm flex items-center gap-2 mb-2">
              <BarChart3 className="h-4 w-4 text-magic-500" />
              Performance do Modelo
            </h3>
            <p className="text-xs text-muted-foreground leading-relaxed">
              <strong>Recall: 93.5%</strong> · Precision: 69.9% · F2-Score: 87.6%.
              Otimizado via F2-score para minimizar falsos negativos.
            </p>
          </CardContent>
        </Card>
        <Card className="card-hover border-green-200/50 dark:border-green-800/30">
          <CardContent className="p-5">
            <h3 className="font-semibold text-sm flex items-center gap-2 mb-2">
              <Gauge className="h-4 w-4 text-green-500" />
              Privacidade (LGPD)
            </h3>
            <p className="text-xs text-muted-foreground leading-relaxed">
              Dados sensíveis nunca armazenados. Apenas estatísticas agregadas.
              Retenção máxima de 30 dias. Auditoria via <code className="text-[10px] bg-muted px-1 rounded">/audit/recent</code>.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
