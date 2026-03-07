/**
 * AnalysisPage.tsx — Análise Exploratória de Dados (EDA)
 *
 * Página dedicada à exploração real do dataset de alunos da
 * Associação Passos Mágicos. Carrega dados via /analysis/eda
 * e exibe: visão geral, distribuições, dados faltantes,
 * correlações e análise do target.
 */
import { useEffect, useState, useMemo, useRef } from 'react'
import {
  FlaskConical,
  BarChart3,
  Database,
  PieChart,
  AlertTriangle,
  TrendingUp,
  GraduationCap,
  Users,
  Calendar,
  Layers,
} from 'lucide-react'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
  Badge,
  Skeleton,
} from '@/components/ui'
import { PageHeader } from '@/components/shared/PageHeader'
import { InfoTooltip } from '@/components/shared/InfoTooltip'
import { ExportChartButton } from '@/components/shared/ExportChartButton'
import { ResponsiveBar } from '@nivo/bar'
import { ResponsivePie } from '@nivo/pie'
import { ResponsiveHeatMap } from '@nivo/heatmap'
import { useNivoTheme, passosPalette, riskPalette } from '@/components/charts/NivoTheme'
import api from '@/services/api'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface FeatureStat {
  name: string
  mean: number
  std: number
  min: number
  max: number
  q25: number
  q50: number
  q75: number
  missing: number
  histogram: { bin: string; count: number }[]
}

interface MissingItem {
  feature: string
  count: number
  percentage: number
}

interface EdaData {
  overview: {
    total_samples: number
    n_features: number
    target: string
    target_distribution: Record<string, number>
    years: string[]
    year_counts: Record<string, number>
    features: string[]
  }
  missing_data: MissingItem[]
  feature_stats: FeatureStat[]
  correlations: { x: string; y: string; value: number }[]
  year_missing: Record<string, {
    n_rows: number
    n_columns: number
    total_missing_cells: number
    missing_percentage: number
  }>
}

/** Friendly labels for features */
const FEATURE_LABELS: Record<string, string> = {
  instituicao_2023: 'Instituição',
  idade_2023: 'Idade',
  genero_2023: 'Gênero',
  fase_2023: 'Fase',
  ano_ingresso_2023: 'Ano Ingresso',
  ian_2023: 'IAN',
  ida_2023: 'IDA',
  ieg_2023: 'IEG',
  iaa_2023: 'IAA',
  ips_2023: 'IPS',
  ipp_2023: 'IPP',
  ipv_2023: 'IPV',
  delta_ian_2022_2023: 'Δ IAN',
  delta_ida_2022_2023: 'Δ IDA',
  delta_ieg_2022_2023: 'Δ IEG',
  delta_iaa_2022_2023: 'Δ IAA',
  delta_ips_2022_2023: 'Δ IPS',
  delta_ipv_2022_2023: 'Δ IPV',
  has_prev_year_data: 'Prev Year',
  em_risco_2024: 'Em Risco',
}

function shortLabel(name: string): string {
  return FEATURE_LABELS[name] ?? name.replace(/_2023$/, '').replace(/^delta_/, 'Δ ').replace(/_2022_2023$/, '')
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function AnalysisPage() {
  const nivoTheme = useNivoTheme()
  const [data, setData] = useState<EdaData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const yearChartRef = useRef<HTMLDivElement>(null)
  const targetChartRef = useRef<HTMLDivElement>(null)
  const missingChartRef = useRef<HTMLDivElement>(null)
  const heatmapRef = useRef<HTMLDivElement>(null)
  const distributionRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    api.eda()
      .then((d: EdaData) => setData(d))
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  // --- Derived data ---
  const targetPie = useMemo(() => {
    if (!data) return []
    const dist = data.overview.target_distribution
    return [
      { id: 'Sem Risco', value: dist.em_risco_0 ?? 0, color: riskPalette.low },
      { id: 'Em Risco', value: dist.em_risco_1 ?? 0, color: riskPalette.high },
    ]
  }, [data])

  const yearBars = useMemo(() => {
    if (!data) return []
    return data.overview.years.map((yr) => ({
      year: yr,
      alunos: data.overview.year_counts[yr] ?? 0,
    }))
  }, [data])

  const missingBars = useMemo(() => {
    if (!data) return []
    return data.missing_data
      .filter((m) => m.count > 0)
      .slice(0, 15)
      .map((m) => ({
        feature: shortLabel(m.feature),
        percentage: m.percentage,
        count: m.count,
      }))
  }, [data])

  // Correlation heatmap — key features only
  const heatmapData = useMemo(() => {
    if (!data || data.correlations.length === 0) return []
    const keyFeats = data.overview.features.filter(
      (f) => !f.startsWith('delta_') && f !== 'has_prev_year_data',
    )
    if (data.correlations.some((c) => c.x === 'em_risco_2024')) {
      keyFeats.push('em_risco_2024')
    }
    const featSet = new Set(keyFeats)
    const byRow: Record<string, Record<string, number>> = {}
    for (const c of data.correlations) {
      if (!featSet.has(c.x) || !featSet.has(c.y)) continue
      if (!byRow[c.y]) byRow[c.y] = {}
      byRow[c.y][c.x] = c.value
    }
    return Object.entries(byRow).map(([rowId, cols]) => ({
      id: shortLabel(rowId),
      data: keyFeats.map((col) => ({
        x: shortLabel(col),
        y: cols[col] ?? 0,
      })),
    }))
  }, [data])

  // Distribution histograms for key indicators
  const distributionFeats = useMemo(() => {
    if (!data) return []
    const indicators = ['ian_2023', 'ida_2023', 'ieg_2023', 'iaa_2023', 'ips_2023', 'ipv_2023', 'ipp_2023']
    return data.feature_stats.filter((f) => indicators.includes(f.name))
  }, [data])

  if (error) {
    return (
      <div className="space-y-6">
        <PageHeader icon={FlaskConical} title="Análise Exploratória" description="Exploração do dataset de alunos da Associação Passos Mágicos." />
        <Card>
          <CardContent className="p-8 text-center">
            <AlertTriangle className="h-8 w-8 text-destructive mx-auto mb-3" />
            <p className="text-sm text-muted-foreground">Não foi possível carregar a análise: {error}</p>
            <p className="text-xs text-muted-foreground mt-1">Verifique se a API está rodando e se o dataset existe em data/processed/</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <PageHeader
        icon={FlaskConical}
        title="Análise Exploratória de Dados"
        description="Exploração do dataset de alunos da Associação Passos Mágicos — distribuições, dados faltantes, correlações e perfil do target."
      />

      {/* OVERVIEW CARDS */}
      <div className="grid gap-4 grid-cols-2 sm:grid-cols-4">
        {[
          { label: 'Amostras', value: data?.overview.total_samples, icon: Users, fmt: (v: number) => v.toLocaleString() },
          { label: 'Features', value: data?.overview.n_features, icon: Layers, fmt: (v: number) => String(v) },
          { label: 'Anos', value: data?.overview.years.length, icon: Calendar, fmt: (v: number) => `${v} (${data?.overview.years[0]}–${data?.overview.years[data!.overview.years.length - 1]})` },
          { label: 'Taxa de Risco', value: data?.overview.target_distribution.ratio_em_risco, icon: AlertTriangle, fmt: (v: number) => `${(v * 100).toFixed(1)}%` },
        ].map(({ label, value, icon: Icon, fmt }, idx) => (
          <Card key={label} className={`card-hover card-shine animate-fade-in-up stagger-${idx + 1}`}>
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-1">
                <Icon className="h-4 w-4 text-muted-foreground" />
                <span className="text-xs text-muted-foreground">{label}</span>
              </div>
              {loading ? (
                <Skeleton className="h-7 w-20 mt-1" />
              ) : (
                <p className="text-xl font-bold">{value != null ? fmt(value) : '—'}</p>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {/* ROW 1: Year evolution + Target distribution */}
      <div className="grid gap-6 grid-cols-1 lg:grid-cols-2">
        {/* Alunos per year */}
        <Card className="card-hover card-shine">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Calendar className="h-4 w-4 text-primary" />
              <CardTitle>Evolução por Ano</CardTitle>
              <InfoTooltip content="Número de alunos presentes nos dados brutos de cada ano letivo. O dataset de modelagem usa 2022→2023 como features e 2024 como target." />
              <span className="ml-auto"><ExportChartButton chartRef={yearChartRef} filename="evolucao-ano" /></span>
            </div>
            <CardDescription>Total de registros por ano letivo</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? <Skeleton className="h-[240px] w-full" /> : (
              <div className="h-[240px]" ref={yearChartRef}>
                <ResponsiveBar
                  data={yearBars}
                  keys={['alunos']}
                  indexBy="year"
                  margin={{ top: 10, right: 20, bottom: 40, left: 60 }}
                  padding={0.4}
                  colors={[passosPalette[0]]}
                  theme={nivoTheme}
                  borderRadius={4}
                  axisBottom={{ legend: 'Ano', legendPosition: 'middle', legendOffset: 32 }}
                  axisLeft={{ legend: 'Alunos', legendPosition: 'middle', legendOffset: -48 }}
                  enableGridY
                  animate
                  motionConfig="gentle"
                  label={(d) => String(d.value)}
                  labelSkipWidth={16}
                  labelTextColor="#fff"
                />
              </div>
            )}
          </CardContent>
        </Card>

        {/* Target distribution */}
        <Card className="card-hover card-shine">
          <CardHeader>
            <div className="flex items-center gap-2">
              <PieChart className="h-4 w-4 text-primary" />
              <CardTitle>Distribuição do Target</CardTitle>
              <InfoTooltip content="Proporção de alunos classificados como 'em risco' de defasagem vs. 'sem risco'. Target desbalanceado: ~40% em risco." />
              <span className="ml-auto"><ExportChartButton chartRef={targetChartRef} filename="target-distribuicao" /></span>
            </div>
            <CardDescription>em_risco_2024 — variável a ser predita</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? <Skeleton className="h-[240px] w-full" /> : (
              <div className="h-[240px]" ref={targetChartRef}>
                <ResponsivePie
                  data={targetPie}
                  margin={{ top: 20, right: 80, bottom: 20, left: 80 }}
                  innerRadius={0.55}
                  padAngle={2}
                  cornerRadius={4}
                  activeOuterRadiusOffset={6}
                  colors={{ datum: 'data.color' }}
                  borderWidth={1}
                  borderColor={{ from: 'color', modifiers: [['darker', 0.2]] }}
                  arcLinkLabelsTextColor="inherit"
                  arcLinkLabelsThickness={2}
                  arcLinkLabelsColor={{ from: 'color' }}
                  arcLabelsSkipAngle={12}
                  theme={nivoTheme}
                  animate
                  motionConfig="gentle"
                  tooltip={({ datum }) => (
                    <div className="bg-popover text-popover-foreground border rounded-lg shadow-lg p-2 text-xs">
                      <p className="font-semibold">{datum.id}</p>
                      <p className="text-muted-foreground">{datum.value} alunos ({((datum.value / (data?.overview.total_samples ?? 1)) * 100).toFixed(1)}%)</p>
                    </div>
                  )}
                />
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* ROW 2: Missing data analysis */}
      <Card className="card-hover card-shine">
        <CardHeader>
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-primary" />
            <CardTitle>Dados Faltantes</CardTitle>
            <InfoTooltip content="Percentual de valores ausentes por feature no dataset de modelagem (765 amostras). Deltas têm mais missings porque dependem de dados do ano anterior." />
            <span className="ml-auto"><ExportChartButton chartRef={missingChartRef} filename="dados-faltantes" /></span>
          </div>
          <CardDescription>Features com maior proporção de missing values</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? <Skeleton className="h-[340px] w-full" /> : missingBars.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-8">Nenhum dado faltante detectado.</p>
          ) : (
            <div className="h-[340px]" ref={missingChartRef}>
              <ResponsiveBar
                data={missingBars}
                keys={['percentage']}
                indexBy="feature"
                layout="horizontal"
                margin={{ top: 10, right: 40, bottom: 40, left: 130 }}
                padding={0.3}
                colors={['#f59e0b']}
                theme={nivoTheme}
                borderRadius={3}
                axisBottom={{ legend: 'Missing (%)', legendPosition: 'middle', legendOffset: 32 }}
                axisLeft={{ tickSize: 0, tickPadding: 8 }}
                enableGridY={false}
                animate
                motionConfig="gentle"
                labelFormat={(v) => `${v}%`}
                tooltip={({ indexValue, data: d }) => (
                  <div className="bg-popover text-popover-foreground border rounded-lg shadow-lg p-2 text-xs">
                    <p className="font-semibold">{indexValue}</p>
                    <p className="text-muted-foreground">{(d as Record<string, unknown>).count as number} valores faltantes ({(d as Record<string, unknown>).percentage as number}%)</p>
                  </div>
                )}
              />
            </div>
          )}
        </CardContent>
      </Card>

      {/* ROW 3: Feature distributions */}
      {distributionFeats.length > 0 && (
        <Card className="card-hover card-shine">
          <CardHeader>
            <div className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4 text-primary" />
              <CardTitle>Distribuição dos Indicadores</CardTitle>
              <InfoTooltip content="Histogramas dos 7 indicadores educacionais do Passos Mágicos. Cada indicador mede uma dimensão do desenvolvimento do aluno." />
              <span className="ml-auto"><ExportChartButton chartRef={distributionRef} filename="indicadores-distribuicao" /></span>
            </div>
            <CardDescription>Histogramas dos principais indicadores educacionais (2023)</CardDescription>
          </CardHeader>
          <CardContent>
            <div ref={distributionRef} className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {distributionFeats.map((feat, idx) => (
                <div key={feat.name} className="space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold">{shortLabel(feat.name)}</span>
                    <Badge variant="secondary" className="text-[10px]">
                      μ={feat.mean.toFixed(1)} σ={feat.std.toFixed(1)}
                    </Badge>
                  </div>
                  <div className="h-[120px]">
                    <ResponsiveBar
                      data={feat.histogram}
                      keys={['count']}
                      indexBy="bin"
                      margin={{ top: 4, right: 4, bottom: 24, left: 30 }}
                      padding={0.15}
                      colors={[passosPalette[idx % passosPalette.length]]}
                      theme={nivoTheme}
                      borderRadius={2}
                      axisBottom={{ tickRotation: -45, tickSize: 0, tickPadding: 4 }}
                      axisLeft={{ tickSize: 0, tickPadding: 4 }}
                      enableGridY={false}
                      enableLabel={false}
                      animate
                      motionConfig="gentle"
                    />
                  </div>
                  <div className="flex justify-between text-[10px] text-muted-foreground px-1">
                    <span>min: {feat.min.toFixed(1)}</span>
                    <span>med: {feat.q50.toFixed(1)}</span>
                    <span>max: {feat.max.toFixed(1)}</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* ROW 4: Correlation heatmap */}
      {heatmapData.length > 0 && (
        <Card className="card-hover card-shine">
          <CardHeader>
            <div className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-primary" />
              <CardTitle>Matriz de Correlação</CardTitle>
              <InfoTooltip content="Correlação de Pearson entre features base e o target. Valores próximos de -1 ou +1 indicam forte relação linear." />
              <span className="ml-auto"><ExportChartButton chartRef={heatmapRef} filename="correlacao-heatmap" /></span>
            </div>
            <CardDescription>Correlação de Pearson entre indicadores e target</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[420px]" ref={heatmapRef}>
              <ResponsiveHeatMap
                data={heatmapData}
                margin={{ top: 80, right: 30, bottom: 30, left: 100 }}
                axisTop={{
                  tickRotation: -45,
                  tickSize: 0,
                  tickPadding: 5,
                }}
                axisLeft={{
                  tickSize: 0,
                  tickPadding: 8,
                }}
                colors={{
                  type: 'diverging',
                  scheme: 'red_yellow_blue',
                  minValue: -1,
                  maxValue: 1,
                }}
                emptyColor="#f3f4f6"
                borderWidth={1}
                borderColor="#ffffff"
                labelTextColor={{ from: 'color', modifiers: [['darker', 3]] }}
                theme={nivoTheme}
                animate
                motionConfig="gentle"
                tooltip={({ cell }) => (
                  <div className="bg-popover text-popover-foreground border rounded-lg shadow-lg p-2 text-xs">
                    <p className="font-semibold">{cell.serieId} × {cell.data.x}</p>
                    <p className="text-muted-foreground">r = {typeof cell.data.y === 'number' ? cell.data.y.toFixed(3) : cell.data.y}</p>
                  </div>
                )}
              />
            </div>
          </CardContent>
        </Card>
      )}

      {/* ROW 5: Feature stats table */}
      {data && data.feature_stats.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Database className="h-4 w-4 text-primary" />
              <CardTitle>Estatísticas Descritivas</CardTitle>
              <InfoTooltip content="Estatísticas resumidas de todas as features numéricas usadas no modelo de predição." />
            </div>
            <CardDescription>Resumo estatístico das features (n={data.overview.total_samples})</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b text-left text-muted-foreground">
                    <th className="py-2 pr-4 font-medium">Feature</th>
                    <th className="py-2 px-2 font-medium text-right">Média</th>
                    <th className="py-2 px-2 font-medium text-right">Desvio</th>
                    <th className="py-2 px-2 font-medium text-right">Mín</th>
                    <th className="py-2 px-2 font-medium text-right">Q25</th>
                    <th className="py-2 px-2 font-medium text-right">Mediana</th>
                    <th className="py-2 px-2 font-medium text-right">Q75</th>
                    <th className="py-2 px-2 font-medium text-right">Máx</th>
                    <th className="py-2 px-2 font-medium text-right">Missing</th>
                  </tr>
                </thead>
                <tbody>
                  {data.feature_stats.map((f) => (
                    <tr key={f.name} className="border-b border-border/50 hover:bg-muted/50 transition-colors">
                      <td className="py-2 pr-4 font-mono font-medium">{shortLabel(f.name)}</td>
                      <td className="py-2 px-2 text-right font-mono">{f.mean.toFixed(2)}</td>
                      <td className="py-2 px-2 text-right font-mono">{f.std.toFixed(2)}</td>
                      <td className="py-2 px-2 text-right font-mono">{f.min.toFixed(2)}</td>
                      <td className="py-2 px-2 text-right font-mono">{f.q25.toFixed(2)}</td>
                      <td className="py-2 px-2 text-right font-mono">{f.q50.toFixed(2)}</td>
                      <td className="py-2 px-2 text-right font-mono">{f.q75.toFixed(2)}</td>
                      <td className="py-2 px-2 text-right font-mono">{f.max.toFixed(2)}</td>
                      <td className="py-2 px-2 text-right">
                        {f.missing > 0 ? (
                          <span className="text-amber-600 dark:text-amber-400 font-semibold">{f.missing}</span>
                        ) : (
                          <span className="text-muted-foreground">0</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Feature legend */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <GraduationCap className="h-4 w-4 text-primary" />
            <CardTitle>Indicadores Educacionais</CardTitle>
            <InfoTooltip content="Os indicadores foram desenvolvidos pela Associação Passos Mágicos para acompanhar o desenvolvimento integral dos alunos ao longo dos anos." />
          </div>
          <CardDescription>Descrição das features utilizadas no pipeline de predição</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {[
              { key: 'IAN', desc: 'Indicador de Adequação de Nível — avalia se o aluno está na série ideal para sua idade.' },
              { key: 'IDA', desc: 'Indicador de Adequação Acadêmica — desempenho nas disciplinas em relação ao esperado.' },
              { key: 'IEG', desc: 'Indicador de Engajamento — participação em atividades extracurriculares e presença.' },
              { key: 'IAA', desc: 'Indicador de Auto-Avaliação — percepção do próprio aluno sobre seu desempenho.' },
              { key: 'IPS', desc: 'Indicador Psicossocial — aspectos emocionais, motivação e integração social.' },
              { key: 'IPP', desc: 'Indicador de Provas Padronizadas — desempenho em avaliações externas.' },
              { key: 'IPV', desc: 'Indicador de Ponto de Virada — sinais de evolução ou regressão recente.' },
              { key: 'Delta (Δ)', desc: 'Variação do indicador entre 2022 e 2023. Captura tendência de melhora ou piora.' },
            ].map(({ key, desc }) => (
              <div key={key} className="p-3 rounded-lg border hover:border-primary/30 transition-colors">
                <span className="text-sm font-bold text-primary">{key}</span>
                <p className="text-[11px] text-muted-foreground leading-relaxed mt-1">{desc}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
