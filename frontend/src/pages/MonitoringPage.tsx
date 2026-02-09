import { useEffect, useState, useCallback, useRef, useMemo } from 'react'
import {
  Activity,
  Clock,
  AlertTriangle,
  RefreshCw,
  Server,
  BarChart3,
  Shield,
  Gauge,
  TrendingUp,
  FileText,
  Info,
  Filter,
  Database,
  Hash,
} from 'lucide-react'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
  Button,
  Badge,
  Skeleton,
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
  Separator,
  Select,
} from '@/components/ui'
import { StatCard } from '@/components/shared/StatCard'
import { StatusBadge, SLOIndicator } from '@/components/shared/StatusBadge'
import { InfoTooltip } from '@/components/shared/InfoTooltip'
import { LatencyChart, MetricsTimeline } from '@/components/charts/MetricsCharts'
import { ResponsiveBar } from '@nivo/bar'
import { useNivoTheme } from '@/components/charts/NivoTheme'
import api from '@/services/api'
import type {
  MetricsResponse,
  SLOResponse,
  HealthResponse,
  DriftStatus,
  AuditRecord,
} from '@/types'
import {
  formatMs,
  formatUptime,
  formatPercentage,
  getDriftStatusColor,
  getDriftStatusBg,
} from '@/lib/utils'

// ──────────────────────────────────────────────
// Types
// ──────────────────────────────────────────────

interface MetricsSnapshot {
  time: string
  latency: number
  requests: number
  errors: number
}

const MAX_BUFFER = 30

// ──────────────────────────────────────────────
// Helpers
// ──────────────────────────────────────────────

function driftEmoji(status: string) {
  switch (status) {
    case 'green':
      return '🟢'
    case 'yellow':
      return '🟡'
    case 'red':
      return '🔴'
    default:
      return '⚪'
  }
}

function driftLabel(status: string) {
  switch (status) {
    case 'green':
      return 'Sem drift'
    case 'yellow':
      return 'Drift moderado'
    case 'red':
      return 'Drift significativo'
    default:
      return 'Desconhecido'
  }
}

function driftBannerClass(status: string) {
  switch (status) {
    case 'green':
      return 'border-green-300 bg-green-50 text-green-800 dark:border-green-700 dark:bg-green-950/30 dark:text-green-300'
    case 'yellow':
      return 'border-amber-300 bg-amber-50 text-amber-800 dark:border-amber-700 dark:bg-amber-950/30 dark:text-amber-300'
    case 'red':
      return 'border-red-300 bg-red-50 text-red-800 dark:border-red-700 dark:bg-red-950/30 dark:text-red-300'
    default:
      return 'border-gray-300 bg-gray-50 text-gray-800 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-300'
  }
}

// ──────────────────────────────
// PSI Drift Bar (Nivo)
// ──────────────────────────────

function PSIDriftBar({ features }: { features: Record<string, { psi: number; status: string }> }) {
  const nivoTheme = useNivoTheme()
  const data = useMemo(() =>
    Object.entries(features)
      .sort(([, a], [, b]) => b.psi - a.psi)
      .map(([name, info]) => ({
        feature: name.replace(/_2023$/, '').toUpperCase(),
        PSI: Number(info.psi.toFixed(4)),
        color: info.status === 'red' ? '#ef4444' : info.status === 'yellow' ? '#f59e0b' : '#22c55e',
      })),
    [features],
  )

  if (data.length === 0) return null

  return (
    <div style={{ height: Math.max(180, data.length * 36) }}>
      <ResponsiveBar
        data={data}
        keys={['PSI']}
        indexBy="feature"
        layout="horizontal"
        theme={nivoTheme}
        margin={{ top: 4, right: 50, bottom: 30, left: 60 }}
        padding={0.35}
        colors={({ data: d }) => (d as Record<string, unknown>).color as string}
        borderRadius={3}
        axisBottom={{ tickSize: 0, tickPadding: 6, legend: 'PSI', legendPosition: 'middle', legendOffset: 24 }}
        axisLeft={{ tickSize: 0, tickPadding: 8 }}
        labelSkipWidth={40}
        labelTextColor="#fff"
        enableGridY={false}
        markers={[
          { axis: 'x', value: 0.1, lineStyle: { stroke: '#f59e0b', strokeDasharray: '4 4' }, legend: '0.1', legendPosition: 'top-right' },
          { axis: 'x', value: 0.25, lineStyle: { stroke: '#ef4444', strokeDasharray: '4 4' }, legend: '0.25', legendPosition: 'top-right' },
        ]}
        tooltip={({ id, value, indexValue }) => (
          <div className="bg-popover text-popover-foreground shadow-lg rounded px-3 py-2 text-xs border">
            <strong>{indexValue}</strong>: {id} = {value}
          </div>
        )}
      />
    </div>
  )
}

// ──────────────────────────────────────────────
// Component
// ──────────────────────────────────────────────

export function MonitoringPage() {
  // Core state
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null)
  const [slo, setSlo] = useState<SLOResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date())

  // Drift state
  const [drift, setDrift] = useState<DriftStatus | null>(null)
  const [driftLoading, setDriftLoading] = useState(false)
  const [driftError, setDriftError] = useState<string | null>(null)

  // Audit state
  const [auditRecords, setAuditRecords] = useState<AuditRecord[]>([])
  const [auditSummary, setAuditSummary] = useState<Record<string, unknown>>({})
  const [auditLoading, setAuditLoading] = useState(false)
  const [auditError, setAuditError] = useState<string | null>(null)
  const [auditFilter, setAuditFilter] = useState<string>('all')

  // Tab state
  const [activeTab, setActiveTab] = useState('overview')

  // Metrics circular buffer (useRef to avoid re-renders on push)
  const bufferRef = useRef<MetricsSnapshot[]>([])
  const [bufferVersion, setBufferVersion] = useState(0)

  // Previous totals for delta calculation
  const prevTotalsRef = useRef<{ requests: number; errors: number } | null>(null)

  // ──────────────────────────────
  // Fetch core metrics (overview)
  // ──────────────────────────────
  const fetchCore = useCallback(async () => {
    try {
      const [h, m, s] = await Promise.allSettled([
        api.health(),
        api.metrics(),
        api.slo(),
      ])
      if (h.status === 'fulfilled') setHealth(h.value)
      if (m.status === 'fulfilled') {
        const metricsData = m.value
        setMetrics(metricsData)

        // Build snapshot and push to circular buffer
        const now = new Date()
        const time = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`

        const prev = prevTotalsRef.current
        const reqDelta = prev ? Math.max(0, metricsData.requests.total - prev.requests) : 0
        const errDelta = prev ? Math.max(0, metricsData.requests.error - prev.errors) : 0

        prevTotalsRef.current = {
          requests: metricsData.requests.total,
          errors: metricsData.requests.error,
        }

        // Only push after we have a baseline (skip first tick for delta)
        if (prev) {
          const snapshot: MetricsSnapshot = {
            time,
            latency: metricsData.latency_ms.p95 ?? metricsData.latency_ms.p50 ?? 0,
            requests: reqDelta,
            errors: errDelta,
          }
          const buf = bufferRef.current
          if (buf.length >= MAX_BUFFER) buf.shift()
          buf.push(snapshot)
          setBufferVersion((v) => v + 1)
        }
      }
      if (s.status === 'fulfilled') setSlo(s.value)
    } catch {
      // silently handle
    } finally {
      setLoading(false)
      setLastRefresh(new Date())
    }
  }, [])

  // ──────────────────────────────
  // Fetch drift
  // ──────────────────────────────
  const fetchDrift = useCallback(async () => {
    setDriftLoading(true)
    setDriftError(null)
    try {
      const d = await api.driftStatus()
      setDrift(d)
    } catch (err) {
      setDriftError(err instanceof Error ? err.message : 'Erro ao buscar dados de drift')
    } finally {
      setDriftLoading(false)
    }
  }, [])

  // ──────────────────────────────
  // Fetch audit
  // ──────────────────────────────
  const fetchAudit = useCallback(async () => {
    setAuditLoading(true)
    setAuditError(null)
    try {
      const res = await api.auditRecent(100)
      setAuditRecords(res.records)
      setAuditSummary(res.summary)
    } catch (err) {
      setAuditError(err instanceof Error ? err.message : 'Erro ao buscar auditoria')
    } finally {
      setAuditLoading(false)
    }
  }, [])

  // Auto-refresh core metrics every 10s
  useEffect(() => {
    fetchCore()
    const interval = setInterval(fetchCore, 10000)
    return () => clearInterval(interval)
  }, [fetchCore])

  // Fetch drift/audit on tab switch
  useEffect(() => {
    if (activeTab === 'drift' && !drift && !driftLoading) fetchDrift()
    if (activeTab === 'audit' && auditRecords.length === 0 && !auditLoading) fetchAudit()
  }, [activeTab, drift, driftLoading, auditRecords.length, auditLoading, fetchDrift, fetchAudit])

  // ──────────────────────────────
  // Derived data
  // ──────────────────────────────

  // eslint-disable-next-line react-hooks/exhaustive-deps
  const chartData = useMemo(() => [...bufferRef.current], [bufferVersion])

  const auditActions = useMemo(() => {
    const s = new Set(auditRecords.map((r) => r.action))
    return ['all', ...Array.from(s).sort()]
  }, [auditRecords])

  const filteredAudit = useMemo(
    () =>
      auditFilter === 'all'
        ? auditRecords
        : auditRecords.filter((r) => r.action === auditFilter),
    [auditRecords, auditFilter],
  )

  // ──────────────────────────────
  // Manual refresh
  // ──────────────────────────────
  const handleRefresh = useCallback(() => {
    fetchCore()
    if (activeTab === 'drift') fetchDrift()
    if (activeTab === 'audit') fetchAudit()
  }, [fetchCore, fetchDrift, fetchAudit, activeTab])

  // ──────────────────────────────
  // Render
  // ──────────────────────────────
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Monitoramento</h1>
          <p className="text-muted-foreground text-sm">
            Métricas de operação, SLOs, drift e auditoria em tempo real
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-muted-foreground">
            Atualizado: {lastRefresh.toLocaleTimeString('pt-BR')}
          </span>
          <Button variant="outline" size="sm" onClick={handleRefresh}>
            <RefreshCw className="h-3.5 w-3.5 mr-1.5" />
            Atualizar
          </Button>
        </div>
      </div>

      <Tabs defaultValue="overview" value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview">
            <Activity className="h-4 w-4 mr-1.5" /> Visão Geral
          </TabsTrigger>
          <TabsTrigger value="slo">
            <Gauge className="h-4 w-4 mr-1.5" /> SLOs
          </TabsTrigger>
          <TabsTrigger value="drift">
            <TrendingUp className="h-4 w-4 mr-1.5" /> Drift
          </TabsTrigger>
          <TabsTrigger value="audit">
            <FileText className="h-4 w-4 mr-1.5" /> Auditoria
          </TabsTrigger>
          <TabsTrigger value="system">
            <Server className="h-4 w-4 mr-1.5" /> Sistema
          </TabsTrigger>
        </TabsList>

        {/* ════════════════════════════════════════
            TAB: Visão Geral
        ════════════════════════════════════════ */}
        <TabsContent value="overview">
          <div className="space-y-6">
            {/* Health banner */}
            <Card>
              <CardContent className="p-4 flex flex-wrap items-center gap-4">
                <StatusBadge status={health?.status ?? 'offline'} />
                <Badge variant="outline" className="gap-1.5">
                  <Server className="h-3 w-3" />
                  {health?.model_version ?? 'N/A'}
                </Badge>
                <Badge variant="outline" className="gap-1.5">
                  <Clock className="h-3 w-3" />
                  Uptime: {health ? formatUptime(health.uptime_seconds) : '—'}
                </Badge>
                {slo && (
                  <Badge
                    variant="outline"
                    className={`gap-1.5 ml-auto ${
                      slo.overall_healthy
                        ? 'border-green-300 text-green-700 dark:border-green-700 dark:text-green-400'
                        : 'border-red-300 text-red-700 dark:border-red-700 dark:text-red-400'
                    }`}
                  >
                    <Shield className="h-3 w-3" />
                    SLO: {slo.overall_healthy ? 'Compliant' : 'Violado'}
                  </Badge>
                )}
              </CardContent>
            </Card>

            {/* Metrics cards */}
            <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-4">
              <StatCard
                title="Requests/min"
                value={metrics?.requests.rate_per_minute.toFixed(1) ?? '—'}
                icon={<Activity className="h-4 w-4" />}
                loading={loading}
              />
              <StatCard
                title="Latência p50"
                value={metrics?.latency_ms.p50 != null ? formatMs(metrics.latency_ms.p50) : '—'}
                subtitle={`p95: ${metrics?.latency_ms.p95 != null ? formatMs(metrics.latency_ms.p95) : '—'} | p99: ${metrics?.latency_ms.p99 != null ? formatMs(metrics.latency_ms.p99) : '—'}`}
                icon={<Clock className="h-4 w-4" />}
                loading={loading}
              />
              <StatCard
                title="Taxa de Erro"
                value={
                  metrics
                    ? formatPercentage(
                        metrics.requests.total > 0
                          ? metrics.requests.error / metrics.requests.total
                          : 0,
                      )
                    : '—'
                }
                subtitle={`${metrics?.requests.error ?? 0} erros de ${metrics?.requests.total ?? 0} reqs`}
                icon={<AlertTriangle className="h-4 w-4" />}
                loading={loading}
              />
              <StatCard
                title="Predições"
                value={metrics?.predictions.total.toLocaleString() ?? '—'}
                subtitle={
                  metrics && metrics.predictions.total > 0
                    ? `${formatPercentage(metrics.predictions.positive / metrics.predictions.total)} alto risco`
                    : undefined
                }
                icon={<BarChart3 className="h-4 w-4" />}
                loading={loading}
              />
            </div>

            {/* Charts — real-time buffer */}
            <div className="grid gap-6 grid-cols-1 lg:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base flex items-center gap-2">
                    <Clock className="h-4 w-4 text-primary" />
                    Latência p95 (tempo real)
                  </CardTitle>
                  <CardDescription>
                    {chartData.length === 0
                      ? 'Aguardando coleta de dados...'
                      : `${chartData.length} amostras coletadas (máx. ${MAX_BUFFER})`}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {loading && chartData.length === 0 ? (
                    <Skeleton className="h-[250px]" />
                  ) : chartData.length === 0 ? (
                    <div className="flex items-center justify-center h-[250px] text-muted-foreground text-sm">
                      <div className="text-center space-y-2">
                        <Activity className="h-8 w-8 mx-auto opacity-40" />
                        <p>O gráfico será preenchido conforme dados chegam a cada 10s</p>
                      </div>
                    </div>
                  ) : (
                    <LatencyChart
                      data={chartData}
                      sloTarget={slo?.latency_slo_ms ?? 300}
                    />
                  )}
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle className="text-base flex items-center gap-2">
                    <Activity className="h-4 w-4 text-primary" />
                    Tráfego & Erros (tempo real)
                  </CardTitle>
                  <CardDescription>
                    {chartData.length === 0
                      ? 'Aguardando coleta de dados...'
                      : `Δ requests e erros por intervalo de 10s`}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {loading && chartData.length === 0 ? (
                    <Skeleton className="h-[250px]" />
                  ) : chartData.length === 0 ? (
                    <div className="flex items-center justify-center h-[250px] text-muted-foreground text-sm">
                      <div className="text-center space-y-2">
                        <BarChart3 className="h-8 w-8 mx-auto opacity-40" />
                        <p>O gráfico será preenchido conforme dados chegam a cada 10s</p>
                      </div>
                    </div>
                  ) : (
                    <MetricsTimeline data={chartData} />
                  )}
                </CardContent>
              </Card>
            </div>
          </div>
        </TabsContent>

        {/* ════════════════════════════════════════
            TAB: SLOs
        ════════════════════════════════════════ */}
        <TabsContent value="slo">
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  Service Level Objectives
                  <InfoTooltip content="SLOs definem metas de qualidade: latência p95 < 300ms e taxa de erro < 1%. Violações indicam degradação do serviço." />
                </CardTitle>
                <CardDescription>
                  Metas de qualidade do serviço definidas para a API de predição
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4 grid-cols-1 sm:grid-cols-2">
                  <SLOIndicator
                    label="Latência p95"
                    value={slo?.latency_p95_ms ?? null}
                    target={slo?.latency_slo_ms ?? 300}
                    unit="ms"
                    inverted
                  />
                  <SLOIndicator
                    label="Taxa de Erro"
                    value={slo ? slo.error_rate * 100 : null}
                    target={slo ? slo.error_rate_slo * 100 : 1}
                    unit="%"
                    inverted
                  />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Detalhes SLO</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 text-sm">
                  <div className="grid grid-cols-2 gap-2">
                    <span className="text-muted-foreground">Total de requests</span>
                    <span>{metrics?.requests.total ?? 0}</span>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <span className="text-muted-foreground">Status latência</span>
                    <span>{slo?.latency_slo_met ? '✅ Dentro da meta' : '❌ Fora da meta'}</span>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <span className="text-muted-foreground">Status erro</span>
                    <span>{slo?.error_rate_slo_met ? '✅ Dentro da meta' : '❌ Fora da meta'}</span>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <span className="text-muted-foreground">Saúde geral</span>
                    <span className="font-medium">
                      {slo?.overall_healthy ? '🟢 Saudável' : '🔴 Degradado'}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* ════════════════════════════════════════
            TAB: Drift
        ════════════════════════════════════════ */}
        <TabsContent value="drift">
          <div className="space-y-6">
            {driftLoading && !drift && (
              <div className="space-y-4">
                <Skeleton className="h-24" />
                <Skeleton className="h-64" />
              </div>
            )}

            {driftError && (
              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center gap-3 text-red-600 dark:text-red-400">
                    <AlertTriangle className="h-5 w-5" />
                    <div>
                      <p className="font-medium">Erro ao carregar drift</p>
                      <p className="text-sm text-muted-foreground">{driftError}</p>
                    </div>
                  </div>
                  <Button variant="outline" size="sm" className="mt-3" onClick={fetchDrift}>
                    <RefreshCw className="h-3.5 w-3.5 mr-1.5" />
                    Tentar novamente
                  </Button>
                </CardContent>
              </Card>
            )}

            {drift && (
              <>
                {/* Overall status banner */}
                <Card className={`border ${driftBannerClass(drift.overall_status)}`}>
                  <CardContent className="p-5">
                    <div className="flex items-start gap-4">
                      <span className="text-3xl">{driftEmoji(drift.overall_status)}</span>
                      <div className="flex-1">
                        <h3 className="text-lg font-semibold">
                          {driftLabel(drift.overall_status)}
                        </h3>
                        <p className="text-sm mt-1 opacity-90">
                          {drift.message || `Status geral: ${drift.status}`}
                        </p>
                        <div className="flex flex-wrap gap-4 mt-3 text-xs">
                          {drift.n_baseline_events != null && (
                            <span className="flex items-center gap-1">
                              <Database className="h-3 w-3" />
                              Baseline: {drift.n_baseline_events.toLocaleString()} eventos
                            </span>
                          )}
                          {drift.n_current_events != null && (
                            <span className="flex items-center gap-1">
                              <Database className="h-3 w-3" />
                              Atual: {drift.n_current_events.toLocaleString()} eventos
                            </span>
                          )}
                        </div>
                      </div>
                      <Button variant="outline" size="sm" onClick={fetchDrift} disabled={driftLoading}>
                        <RefreshCw className={`h-3.5 w-3.5 mr-1.5 ${driftLoading ? 'animate-spin' : ''}`} />
                        Atualizar
                      </Button>
                    </div>
                  </CardContent>
                </Card>

                {/* Per-feature PSI grid */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base flex items-center gap-2">
                      <BarChart3 className="h-4 w-4 text-primary" />
                      PSI por Feature
                      <InfoTooltip content="Population Stability Index — mede a mudança na distribuição de cada feature entre baseline (treino) e produção. PSI > 0.25 = drift significativo." />
                    </CardTitle>
                    <CardDescription>
                      Population Stability Index — mede a mudança na distribuição de cada feature
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {Object.keys(drift.features).length === 0 ? (
                      <p className="text-sm text-muted-foreground">Nenhuma feature monitorada</p>
                    ) : (
                      <>
                        {/* Nivo Bar Chart for PSI */}
                        <PSIDriftBar features={drift.features} />

                        <Separator className="my-4" />

                        {/* Card grid */}
                        <div className="grid gap-3 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
                        {Object.entries(drift.features)
                          .sort(([, a], [, b]) => b.psi - a.psi)
                          .map(([name, info]) => (
                            <div
                              key={name}
                              className={`rounded-lg border p-3 ${getDriftStatusBg(info.status)}`}
                            >
                              <div className="flex items-center justify-between">
                                <span className="text-sm font-medium truncate mr-2">{name}</span>
                                <span className="text-lg">{driftEmoji(info.status)}</span>
                              </div>
                              <div className="mt-1 flex items-baseline gap-2">
                                <span className={`text-xl font-bold ${getDriftStatusColor(info.status)}`}>
                                  {info.psi.toFixed(4)}
                                </span>
                                <span className="text-xs text-muted-foreground">PSI</span>
                              </div>
                            </div>
                          ))}
                      </div>
                      </>
                    )}
                  </CardContent>
                </Card>

                {/* Score drift */}
                {drift.score_drift && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base flex items-center gap-2">
                        <TrendingUp className="h-4 w-4 text-primary" />
                        Drift do Score de Predição
                        <InfoTooltip content="Mede se a distribuição das probabilidades preditas mudou em relação ao baseline de treino. PSI alto indica que o modelo produz scores diferentes do esperado." />
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className={`rounded-lg border p-4 ${getDriftStatusBg(drift.score_drift.status)}`}>
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-sm text-muted-foreground">Score PSI</p>
                            <p className={`text-2xl font-bold ${getDriftStatusColor(drift.score_drift.status)}`}>
                              {drift.score_drift.status === 'insufficient_data'
                                ? 'Dados insuficientes'
                                : drift.score_drift.psi.toFixed(4)}
                            </p>
                          </div>
                          <span className="text-3xl">{driftEmoji(drift.score_drift.status)}</span>
                        </div>
                        {drift.score_drift.status !== 'insufficient_data' && (
                          <p className="text-xs text-muted-foreground mt-2">
                            {driftLabel(drift.score_drift.status)}
                          </p>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Missing rates comparison */}
                {drift.missing_rates && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base flex items-center gap-2">
                        <AlertTriangle className="h-4 w-4 text-primary" />
                        Taxa de Valores Ausentes
                      </CardTitle>
                      <CardDescription>
                        Comparação baseline vs. atual — percentual de valores nulos por feature
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="border-b">
                              <th className="text-left py-2 pr-4 font-medium text-muted-foreground">Feature</th>
                              <th className="text-right py-2 px-4 font-medium text-muted-foreground">Baseline</th>
                              <th className="text-right py-2 px-4 font-medium text-muted-foreground">Atual</th>
                              <th className="text-right py-2 pl-4 font-medium text-muted-foreground">Δ</th>
                            </tr>
                          </thead>
                          <tbody>
                            {Object.keys({
                              ...drift.missing_rates.baseline,
                              ...drift.missing_rates.current,
                            })
                              .sort()
                              .map((feat) => {
                                const bVal = drift.missing_rates!.baseline[feat] ?? 0
                                const cVal = drift.missing_rates!.current[feat] ?? 0
                                const delta = cVal - bVal
                                return (
                                  <tr key={feat} className="border-b last:border-0 hover:bg-muted/30">
                                    <td className="py-2 pr-4 font-mono text-xs">{feat}</td>
                                    <td className="py-2 px-4 text-right">{(bVal * 100).toFixed(1)}%</td>
                                    <td className="py-2 px-4 text-right">{(cVal * 100).toFixed(1)}%</td>
                                    <td
                                      className={`py-2 pl-4 text-right font-medium ${
                                        delta > 0.05
                                          ? 'text-red-600 dark:text-red-400'
                                          : delta > 0
                                          ? 'text-amber-600 dark:text-amber-400'
                                          : 'text-green-600 dark:text-green-400'
                                      }`}
                                    >
                                      {delta > 0 ? '+' : ''}
                                      {(delta * 100).toFixed(1)}%
                                    </td>
                                  </tr>
                                )
                              })}
                          </tbody>
                        </table>
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* PSI explanation */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base flex items-center gap-2">
                      <Info className="h-4 w-4 text-primary" />
                      O que é PSI?
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground mb-4">
                      O <strong>Population Stability Index (PSI)</strong> mede a mudança entre a
                      distribuição do baseline (treino) e a distribuição atual dos dados em produção.
                      Valores altos indicam que os dados mudaram significativamente, o que pode
                      degradar a performance do modelo.
                    </p>
                    <div className="grid gap-3 grid-cols-1 sm:grid-cols-3">
                      <div className="rounded-lg border border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-950/20 p-3 text-center">
                        <span className="text-2xl">🟢</span>
                        <p className="font-semibold text-sm mt-1">PSI &lt; 0.1</p>
                        <p className="text-xs text-muted-foreground">Sem drift significativo</p>
                      </div>
                      <div className="rounded-lg border border-amber-200 bg-amber-50 dark:border-amber-800 dark:bg-amber-950/20 p-3 text-center">
                        <span className="text-2xl">🟡</span>
                        <p className="font-semibold text-sm mt-1">0.1 ≤ PSI ≤ 0.25</p>
                        <p className="text-xs text-muted-foreground">Drift moderado — investigar</p>
                      </div>
                      <div className="rounded-lg border border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-950/20 p-3 text-center">
                        <span className="text-2xl">🔴</span>
                        <p className="font-semibold text-sm mt-1">PSI &gt; 0.25</p>
                        <p className="text-xs text-muted-foreground">Drift significativo — retreinar</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </>
            )}
          </div>
        </TabsContent>

        {/* ════════════════════════════════════════
            TAB: Auditoria
        ════════════════════════════════════════ */}
        <TabsContent value="audit">
          <div className="space-y-6">
            {auditLoading && auditRecords.length === 0 && (
              <div className="space-y-4">
                <Skeleton className="h-20" />
                <Skeleton className="h-64" />
              </div>
            )}

            {auditError && (
              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center gap-3 text-red-600 dark:text-red-400">
                    <AlertTriangle className="h-5 w-5" />
                    <div>
                      <p className="font-medium">Erro ao carregar auditoria</p>
                      <p className="text-sm text-muted-foreground">{auditError}</p>
                    </div>
                  </div>
                  <Button variant="outline" size="sm" className="mt-3" onClick={fetchAudit}>
                    <RefreshCw className="h-3.5 w-3.5 mr-1.5" />
                    Tentar novamente
                  </Button>
                </CardContent>
              </Card>
            )}

            {auditRecords.length > 0 && (
              <>
                {/* Summary stats */}
                <div className="grid gap-4 grid-cols-2 sm:grid-cols-4">
                  <StatCard
                    title="Total de Registros"
                    value={auditRecords.length}
                    icon={<FileText className="h-4 w-4" />}
                  />
                  <StatCard
                    title="Ações Distintas"
                    value={auditActions.length - 1}
                    icon={<Hash className="h-4 w-4" />}
                  />
                  {Object.entries(auditSummary)
                    .slice(0, 2)
                    .map(([key, val]) => (
                      <StatCard
                        key={key}
                        title={key}
                        value={String(val)}
                        icon={<Activity className="h-4 w-4" />}
                      />
                    ))}
                </div>

                {/* Filter + table */}
                <Card>
                  <CardHeader className="pb-3">
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                      <CardTitle className="text-base flex items-center gap-2">
                        <FileText className="h-4 w-4 text-primary" />
                        Registros de Auditoria
                      </CardTitle>
                      <div className="flex items-center gap-2">
                        <Filter className="h-4 w-4 text-muted-foreground" />
                        <Select
                          value={auditFilter}
                          onChange={(e) => setAuditFilter(e.target.value)}
                          className="w-48 h-8 text-xs"
                        >
                          {auditActions.map((a) => (
                            <option key={a} value={a}>
                              {a === 'all' ? 'Todas as ações' : a}
                            </option>
                          ))}
                        </Select>
                        <Button variant="outline" size="sm" onClick={fetchAudit} disabled={auditLoading}>
                          <RefreshCw className={`h-3.5 w-3.5 ${auditLoading ? 'animate-spin' : ''}`} />
                        </Button>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="border-b">
                            <th className="text-left py-2 pr-4 font-medium text-muted-foreground">Timestamp</th>
                            <th className="text-left py-2 px-4 font-medium text-muted-foreground">Ação</th>
                            <th className="text-left py-2 px-4 font-medium text-muted-foreground">Request ID</th>
                            <th className="text-left py-2 pl-4 font-medium text-muted-foreground">Git SHA</th>
                          </tr>
                        </thead>
                        <tbody>
                          {filteredAudit.map((record, i) => (
                            <tr key={`${record.timestamp}-${i}`} className="border-b last:border-0 hover:bg-muted/30">
                              <td className="py-2 pr-4 font-mono text-xs whitespace-nowrap">
                                {new Date(record.timestamp).toLocaleString('pt-BR')}
                              </td>
                              <td className="py-2 px-4">
                                <Badge variant="secondary" className="text-[10px]">
                                  {record.action}
                                </Badge>
                              </td>
                              <td className="py-2 px-4 font-mono text-xs text-muted-foreground">
                                {record.request_id
                                  ? record.request_id.slice(0, 12) + '…'
                                  : '—'}
                              </td>
                              <td className="py-2 pl-4 font-mono text-xs text-muted-foreground">
                                {record.git_sha ? record.git_sha.slice(0, 8) : '—'}
                              </td>
                            </tr>
                          ))}
                          {filteredAudit.length === 0 && (
                            <tr>
                              <td colSpan={4} className="py-8 text-center text-muted-foreground">
                                Nenhum registro encontrado para o filtro selecionado
                              </td>
                            </tr>
                          )}
                        </tbody>
                      </table>
                    </div>
                    <Separator className="my-3" />
                    <p className="text-xs text-muted-foreground">
                      Exibindo {filteredAudit.length} de {auditRecords.length} registros
                    </p>
                  </CardContent>
                </Card>
              </>
            )}

            {!auditLoading && !auditError && auditRecords.length === 0 && (
              <Card>
                <CardContent className="p-12 text-center">
                  <FileText className="h-10 w-10 mx-auto text-muted-foreground opacity-40" />
                  <p className="mt-3 text-sm text-muted-foreground">
                    Nenhum registro de auditoria encontrado
                  </p>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>

        {/* ════════════════════════════════════════
            TAB: Sistema
        ════════════════════════════════════════ */}
        <TabsContent value="system">
          <div className="space-y-6">
            <div className="grid gap-4 grid-cols-1 sm:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Saúde do Serviço</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Status</span>
                    <StatusBadge status={health?.status ?? 'offline'} />
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Modelo carregado</span>
                    <span>{health?.model_loaded ? '✅ Sim' : '❌ Não'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Versão do modelo</span>
                    <span className="font-mono text-xs">{health?.model_version ?? '—'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Uptime</span>
                    <span>{health ? formatUptime(health.uptime_seconds) : '—'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Total requests</span>
                    <span>{metrics?.requests.total ?? '—'}</span>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Configuração</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">API Port</span>
                    <span className="font-mono text-xs">8000</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Rate Limit</span>
                    <span className="font-mono text-xs">60 req/min</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Max Body</span>
                    <span className="font-mono text-xs">256KB</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Privacy Mode</span>
                    <span className="font-mono text-xs">aggregate_only</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Retenção Dados</span>
                    <span className="font-mono text-xs">30 dias</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Feature Policy</span>
                    <span className="font-mono text-xs">reject</span>
                  </div>
                </CardContent>
              </Card>
            </div>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Endpoints da API</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {[
                    { method: 'GET', path: '/health', desc: 'Health check do serviço' },
                    { method: 'GET', path: '/ready', desc: 'Readiness probe' },
                    { method: 'GET', path: '/metadata', desc: 'Metadata do modelo' },
                    { method: 'POST', path: '/predict', desc: 'Predição de risco (single/batch)' },
                    { method: 'GET', path: '/metrics', desc: 'Métricas da API' },
                    { method: 'GET', path: '/slo', desc: 'Status de compliance SLO' },
                    { method: 'GET', path: '/artifacts/metrics', desc: 'Métricas dos artefatos do modelo' },
                    { method: 'GET', path: '/artifacts/metadata', desc: 'Metadata dos artefatos' },
                    { method: 'GET', path: '/artifacts/report', desc: 'Relatório do modelo (markdown)' },
                    { method: 'GET', path: '/drift/status', desc: 'Status de drift das features' },
                    { method: 'GET', path: '/inference/history', desc: 'Histórico de inferências' },
                    { method: 'GET', path: '/audit/recent', desc: 'Registros de auditoria recentes' },
                  ].map((ep) => (
                    <div
                      key={ep.path}
                      className="flex items-center gap-3 p-2 rounded hover:bg-muted/50"
                    >
                      <Badge
                        variant={ep.method === 'POST' ? 'default' : 'secondary'}
                        className="w-14 justify-center text-[10px]"
                      >
                        {ep.method}
                      </Badge>
                      <span className="font-mono text-sm">{ep.path}</span>
                      <span className="text-xs text-muted-foreground ml-auto hidden sm:inline">
                        {ep.desc}
                      </span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}
