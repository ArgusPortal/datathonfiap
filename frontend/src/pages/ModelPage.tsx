import { useEffect, useState, useCallback } from 'react'
import {
  FileText,
  Brain,
  Target,
  BarChart3,
  Shield,
  AlertTriangle,
  Users,
  Clock,
  CheckCircle2,
  BookOpen,
  Settings2,
  GitCompare,
  Info,
  Layers,
  Hash,
  FlaskConical,
  ListChecks,
  ChevronRight,
  Fingerprint,
  TrendingUp,
  Scale,
} from 'lucide-react'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
  Badge,
  Separator,
  Skeleton,
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
} from '@/components/ui'
import api from '@/services/api'
import type { ModelComparisonData, ArtifactMetadata, MetadataResponse, FairnessAnalysis } from '@/types'
import { formatPercentage } from '@/lib/utils'
import { InfoTooltip } from '@/components/shared/InfoTooltip'
import { GlossaryTip } from '@/components/shared/Glossary'
import { BumpRanking, type BumpSerie } from '@/components/charts/BumpRanking'
import { ROCCurve, type ROCPoint } from '@/components/charts/ROCCurve'
import { FeatureImportance } from '@/components/charts/FeatureImportance'
import { FairnessTable, DisparitySummary } from '@/components/charts/FairnessChart'

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
const MODEL_NAME_MAP: Record<string, string> = {
  hist_gb: 'HistGradientBoosting',
  rf: 'Random Forest',
  logreg: 'Logistic Regression',
  dummy_baseline: 'Dummy Baseline',
}

function displayModelName(key: string): string {
  return MODEL_NAME_MAP[key] ?? key
}

function fmtDate(raw: string | null | undefined): string {
  if (!raw) return '—'
  try {
    return new Date(raw).toLocaleDateString('pt-BR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return raw
  }
}

// Simple markdown → HTML converter (handles headers, bold, lists, code)
function renderMarkdown(md: string): string {
  // Process code blocks first (preserve content inside)
  let result = md.replace(
    /```[\s\S]*?```/g,
    (block) => {
      const content = block.replace(/^```\w*\n?/, '').replace(/\n?```$/, '')
      return `<pre class="bg-muted/60 rounded-lg p-4 text-xs font-mono overflow-x-auto my-3 border">${content.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</pre>`
    },
  )

  // Tables: detect markdown table blocks and convert them
  result = result.replace(
    /(?:^|\n)((?:\|.+\|(?:\n|$))+)/g,
    (_match, tableBlock: string) => {
      const rows = tableBlock.trim().split('\n').filter(Boolean)
      if (rows.length < 2) return tableBlock

      // Check if second row is separator (|---|---|)
      const isSeparator = /^\|[\s:-]+\|/.test(rows[1])
      const dataRows = isSeparator ? [rows[0], ...rows.slice(2)] : rows

      let html = '<div class="overflow-x-auto my-4"><table class="w-full text-sm border-collapse">'

      dataRows.forEach((row, idx) => {
        const cells = row.split('|').slice(1, -1).map(c => c.trim())
        const isHeader = idx === 0 && isSeparator
        const tag = isHeader ? 'th' : 'td'
        const cellClass = isHeader
          ? 'px-3 py-2 text-left font-semibold bg-muted/50 border-b-2 border-border text-xs uppercase tracking-wider'
          : 'px-3 py-2 border-b border-border/50'
        html += '<tr>'
        cells.forEach(cell => {
          // Process inline markdown within cells
          const processed = cell
            .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
            .replace(/`([^`]+)`/g, '<code class="bg-muted px-1 py-0.5 rounded text-xs font-mono">$1</code>')
          html += `<${tag} class="${cellClass}">${processed}</${tag}>`
        })
        html += '</tr>'
      })

      html += '</table></div>'
      return html
    },
  )

  // Horizontal rules
  result = result.replace(/^---+$/gm, '<hr class="my-6 border-border/60" />')
  // Italic note at end
  result = result.replace(/^\*([^*]+)\*$/gm, '<p class="text-xs text-muted-foreground italic mt-4">$1</p>')

  // Headings (order matters: ### before ## before #)
  result = result.replace(/^### (.+)$/gm, '<h3 class="text-base font-semibold mt-5 mb-2 flex items-center gap-2">$1</h3>')
  result = result.replace(/^## (.+)$/gm, '<h2 class="text-lg font-bold mt-8 mb-3 pb-1 border-b border-border/40">$1</h2>')
  result = result.replace(/^# (.+)$/gm, '<h1 class="text-xl font-bold mt-4 mb-4">$1</h1>')

  // Inline formatting
  result = result.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  result = result.replace(/`([^`]+)`/g, '<code class="bg-muted px-1.5 py-0.5 rounded text-xs font-mono">$1</code>')

  // Numbered lists
  result = result.replace(/^(\d+)\. (.+)$/gm, '<li class="ml-5 list-decimal text-sm text-muted-foreground mb-1">$2</li>')
  // Bullet lists
  result = result.replace(/^- (.+)$/gm, '<li class="ml-5 list-disc text-sm text-muted-foreground mb-1">$1</li>')

  // Wrap consecutive <li> items in <ul>/<ol>
  result = result.replace(/((?:<li class="ml-5 list-disc[^>]*>.*?<\/li>\s*)+)/g, '<ul class="my-3 space-y-0.5">$1</ul>')
  result = result.replace(/((?:<li class="ml-5 list-decimal[^>]*>.*?<\/li>\s*)+)/g, '<ol class="my-3 space-y-0.5">$1</ol>')

  // Paragraphs
  result = result.replace(/\n{2,}/g, '</p><p class="text-sm text-muted-foreground mb-2">')
  result = result.replace(/\n/g, '<br/>')

  return result
}

// ---------------------------------------------------------------------------
// Skeleton helpers
// ---------------------------------------------------------------------------
function SkeletonRows({ rows = 6 }: { rows?: number }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: rows }).map((_, i) => (
        <Skeleton key={i} className="h-4 w-full" />
      ))}
    </div>
  )
}

function SkeletonCards({ count = 6 }: { count?: number }) {
  return (
    <div className="grid gap-4 grid-cols-2 sm:grid-cols-3 lg:grid-cols-6">
      {Array.from({ length: count }).map((_, i) => (
        <Card key={i}>
          <CardContent className="p-4">
            <Skeleton className="h-3 w-16 mb-2" />
            <Skeleton className="h-8 w-20 mx-auto" />
          </CardContent>
        </Card>
      ))}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Confusion Matrix component
// ---------------------------------------------------------------------------
function ConfusionMatrix({
  matrix,
  nSamples,
  nPositive,
  threshold,
  fn,
}: {
  matrix: number[][]
  nSamples?: number
  nPositive?: number
  threshold?: number
  fn?: number
}) {
  const tn = matrix[0]?.[0] ?? 0
  const fp = matrix[0]?.[1] ?? 0
  const fnVal = fn ?? matrix[1]?.[0] ?? 0
  const tp = matrix[1]?.[1] ?? 0

  return (
    <div className="max-w-md mx-auto">
      <div className="grid grid-cols-3 gap-1 text-center text-sm">
        <div />
        <div className="font-medium text-muted-foreground py-2">Pred = Ok</div>
        <div className="font-medium text-muted-foreground py-2">Pred = Risco</div>

        <div className="font-medium text-muted-foreground flex items-center justify-center">
          Real = Ok
        </div>
        <div className="bg-green-100 dark:bg-green-900/30 rounded-lg p-4">
          <p className="text-2xl font-bold text-green-700 dark:text-green-400">{tn}</p>
          <p className="text-[10px] text-green-600">TN</p>
        </div>
        <div className="bg-amber-100 dark:bg-amber-900/30 rounded-lg p-4">
          <p className="text-2xl font-bold text-amber-700 dark:text-amber-400">{fp}</p>
          <p className="text-[10px] text-amber-600">FP</p>
        </div>

        <div className="font-medium text-muted-foreground flex items-center justify-center">
          Real = Risco
        </div>
        <div className="bg-red-100 dark:bg-red-900/30 rounded-lg p-4">
          <p className="text-2xl font-bold text-red-700 dark:text-red-400">{fnVal}</p>
          <p className="text-[10px] text-red-600">FN</p>
        </div>
        <div className="bg-green-100 dark:bg-green-900/30 rounded-lg p-4">
          <p className="text-2xl font-bold text-green-700 dark:text-green-400">{tp}</p>
          <p className="text-[10px] text-green-600">TP</p>
        </div>
      </div>

      <div className="mt-4 p-3 rounded-lg bg-muted/50 text-center text-xs text-muted-foreground">
        {nSamples != null && (
          <span>
            {nSamples} amostras
            {nPositive != null &&
              ` (${nPositive} positivos = ${((nPositive / nSamples) * 100).toFixed(1)}%)`}
          </span>
        )}
        {threshold != null && <span> · Threshold: {threshold}</span>}
        {fnVal > 0 && (
          <>
            <br />
            Apenas <strong className="text-red-600">
              {fnVal} aluno{fnVal > 1 ? 's' : ''}
            </strong>{' '}
            em risco real não identificado{fnVal > 1 ? 's' : ''} (FN = {fnVal})
          </>
        )}
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------
export function ModelPage() {
  const [metadata, setMetadata] = useState<MetadataResponse | null>(null)
  const [comparison, setComparison] = useState<ModelComparisonData | null>(null)
  const [artifactMeta, setArtifactMeta] = useState<ArtifactMetadata | null>(null)
  const [report, setReport] = useState<string | null>(null)
  const [fairness, setFairness] = useState<FairnessAnalysis | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Comparação tab: selected model
  const [selectedCompModel, setSelectedCompModel] = useState<string | null>(null)

  const fetchAll = useCallback(async () => {
    setLoading(true)
    setError(null)

    const [metaRes, compRes, artifactRes, reportRes, fairnessRes] = await Promise.allSettled([
      api.metadata(),
      api.artifactMetrics(),
      api.artifactMetadata(),
      api.artifactReport(),
      api.artifactFairness(),
    ])

    if (metaRes.status === 'fulfilled') setMetadata(metaRes.value)
    if (compRes.status === 'fulfilled') {
      setComparison(compRes.value)
      setSelectedCompModel(compRes.value.best_model)
    }
    if (artifactRes.status === 'fulfilled') setArtifactMeta(artifactRes.value)
    if (reportRes.status === 'fulfilled') setReport(reportRes.value.content)
    if (fairnessRes.status === 'fulfilled') setFairness(fairnessRes.value)

    // If all failed, show error
    if (
      metaRes.status === 'rejected' &&
      compRes.status === 'rejected' &&
      artifactRes.status === 'rejected'
    ) {
      setError('Não foi possível carregar os dados do modelo. Verifique a conexão com a API.')
    }

    setLoading(false)
  }, [])

  useEffect(() => {
    fetchAll()
  }, [fetchAll])

  // Derived data
  const best = comparison?.best_metrics
  const ranking = comparison?.ranking ?? []
  const expectedFeatures = artifactMeta?.expected_features ?? metadata?.expected_features ?? []
  const blockedFeatures = artifactMeta?.blocked_features ?? []

  // Feature importance mock (illustrative — we don't have SHAP data)
  const featureImportanceMock: { name: string; importance: number }[] = expectedFeatures.map(
    (f, i) => ({
      name: f,
      importance: Math.max(0.15, 1 - i * 0.06),
    }),
  )

  // ---------------------------------------------------------------------------
  // Error fallback
  // ---------------------------------------------------------------------------
  if (error && !comparison && !artifactMeta && !metadata) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 py-20">
        <AlertTriangle className="h-12 w-12 text-amber-500" />
        <p className="text-lg font-medium">{error}</p>
        <button
          onClick={fetchAll}
          className="px-4 py-2 rounded-md bg-primary text-primary-foreground text-sm hover:bg-primary/90"
        >
          Tentar novamente
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-1">
        <h1 className="text-2xl font-bold tracking-tight">Informações do Modelo</h1>
        <p className="text-muted-foreground text-sm">
          Model Card, métricas de performance e documentação técnica
        </p>
      </div>

      <Tabs defaultValue="card">
        <TabsList className="flex-wrap">
          <TabsTrigger value="card">
            <FileText className="h-4 w-4 mr-1.5" /> Model Card
          </TabsTrigger>
          <TabsTrigger value="performance">
            <BarChart3 className="h-4 w-4 mr-1.5" /> Performance
          </TabsTrigger>
          <TabsTrigger value="features">
            <BookOpen className="h-4 w-4 mr-1.5" /> Features
          </TabsTrigger>
          <TabsTrigger value="ethics">
            <Shield className="h-4 w-4 mr-1.5" /> Ética & LGPD
          </TabsTrigger>
          <TabsTrigger value="fairness">
            <Scale className="h-4 w-4 mr-1.5" /> Fairness
          </TabsTrigger>
          <TabsTrigger value="governance">
            <Settings2 className="h-4 w-4 mr-1.5" /> Governança
          </TabsTrigger>
          <TabsTrigger value="comparison">
            <GitCompare className="h-4 w-4 mr-1.5" /> Comparação
          </TabsTrigger>
          <TabsTrigger value="reproducibility">
            <Fingerprint className="h-4 w-4 mr-1.5" /> Reprodutibilidade
          </TabsTrigger>
        </TabsList>

        {/* ================================================================
            TAB: Model Card
        ================================================================ */}
        <TabsContent value="card">
          <div className="grid gap-6 grid-cols-1 lg:grid-cols-2">
            {/* Model Details */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Brain className="h-5 w-5 text-primary" />
                  Detalhes do Modelo
                </CardTitle>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <SkeletonRows rows={10} />
                ) : (
                  <div className="space-y-3 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Nome</span>
                      <span className="font-medium">Defasagem Risk Classifier</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Versão</span>
                      <Badge variant="outline">
                        {artifactMeta?.model_version ?? metadata?.model_version ?? '—'}
                      </Badge>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Tipo</span>
                      <span>Classificação Binária</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Framework</span>
                      <span>scikit-learn {artifactMeta?.sklearn_version ?? artifactMeta?.libs_versions?.sklearn ?? ''}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Algoritmo</span>
                      <span>
                        {comparison?.best_model
                          ? displayModelName(comparison.best_model)
                          : metadata?.model_family ?? '—'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Calibração</span>
                      <span>{artifactMeta?.calibration ?? metadata?.calibration ?? '—'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Threshold</span>
                      <span className="font-mono">
                        {best?.threshold ?? metadata?.threshold ?? '—'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Seed</span>
                      <span className="font-mono">{artifactMeta?.seed ?? '—'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Criado em</span>
                      <span>{fmtDate(artifactMeta?.created_at ?? metadata?.created_at)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Target</span>
                      <span className="text-xs max-w-[260px] text-right">
                        {artifactMeta?.target_definition ?? '—'}
                      </span>
                    </div>
                    {artifactMeta?.training_periods && (
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Períodos de Treino</span>
                        <span className="font-mono">
                          {artifactMeta.training_periods.join(', ')}
                        </span>
                      </div>
                    )}
                    {artifactMeta?.population_filter && (
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Filtro de População</span>
                        <span>{artifactMeta.population_filter}</span>
                      </div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Uso Pretendido */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Target className="h-5 w-5 text-primary" />
                  Uso Pretendido
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4 text-sm">
                <div>
                  <h4 className="font-semibold mb-1">Caso de Uso Principal</h4>
                  <p className="text-muted-foreground">
                    Predição de risco de defasagem escolar para alunos do programa Passos Mágicos,
                    permitindo intervenção precoce e alocação otimizada de recursos.
                  </p>
                </div>
                <Separator />
                <div>
                  <h4 className="font-semibold mb-2">Usuários Pretendidos</h4>
                  <div className="space-y-2">
                    {[
                      { icon: Users, label: 'Coordenadores pedagógicos' },
                      { icon: Users, label: 'Assistentes sociais' },
                      { icon: Users, label: 'Equipe de gestão da ONG' },
                    ].map(({ icon: Icon, label }) => (
                      <div key={label} className="flex items-center gap-2 text-muted-foreground">
                        <Icon className="h-3.5 w-3.5" />
                        <span>{label}</span>
                      </div>
                    ))}
                  </div>
                </div>
                <Separator />
                <div>
                  <h4 className="font-semibold mb-2 flex items-center gap-1.5">
                    <AlertTriangle className="h-3.5 w-3.5 text-amber-500" />
                    Usos Fora do Escopo
                  </h4>
                  <ul className="space-y-1 text-muted-foreground text-xs">
                    <li>• Decisões automatizadas sem revisão humana</li>
                    <li>• Uso em contextos não-educacionais</li>
                    <li>• Predição para populações fora do escopo do programa</li>
                  </ul>
                </div>
              </CardContent>
            </Card>

            {/* Dados de Treino */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="h-5 w-5 text-primary" />
                  Dados de Treino
                </CardTitle>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <SkeletonRows rows={8} />
                ) : (
                  <div className="space-y-3 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Fonte</span>
                      <span>Dados históricos Passos Mágicos</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Período</span>
                      <span className="font-mono">
                        {artifactMeta?.training_periods?.join(', ') ?? '—'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Total amostras (teste)</span>
                      <span className="font-mono">{best?.n_samples ?? '—'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Positivos (teste)</span>
                      <span className="font-mono">{best?.n_positive ?? '—'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Negativos (teste)</span>
                      <span className="font-mono">{best?.n_negative ?? '—'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Taxa base positiva</span>
                      <span className="font-mono">
                        {best?.baseline_rate != null
                          ? `${(best.baseline_rate * 100).toFixed(1)}%`
                          : '—'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Features esperadas</span>
                      <span className="font-mono">{expectedFeatures.length}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Seed</span>
                      <span className="font-mono">{artifactMeta?.seed ?? '—'}</span>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Riscos e Limitações */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5 text-amber-500" />
                  Riscos e Limitações
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {[
                    {
                      title: 'Sem backtest multi-ano',
                      desc: 'Validação apenas em 2023→2024',
                      severity: 'high',
                    },
                    {
                      title: 'Split simples',
                      desc: 'Holdout 20%, sem GroupKFold por escola',
                      severity: 'medium',
                    },
                    {
                      title: 'Population drift',
                      desc: 'Performance pode variar com mudanças demográficas',
                      severity: 'high',
                    },
                    {
                      title: 'Features limitadas',
                      desc: 'Apenas indicadores 2023 disponíveis',
                      severity: 'medium',
                    },
                    {
                      title: 'Amostra pequena',
                      desc: `${best?.n_samples ?? '~153'} registros de teste — intervalos de confiança largos`,
                      severity: 'medium',
                    },
                  ].map((risk) => (
                    <div
                      key={risk.title}
                      className="flex items-start gap-3 p-2 rounded hover:bg-muted/50"
                    >
                      <span className="text-sm mt-0.5">
                        {risk.severity === 'high' ? '🔴' : '🟡'}
                      </span>
                      <div>
                        <p className="text-sm font-medium">{risk.title}</p>
                        <p className="text-xs text-muted-foreground">{risk.desc}</p>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Assumptions from metadata */}
                {artifactMeta?.assumptions && artifactMeta.assumptions.length > 0 && (
                  <>
                    <Separator className="my-4" />
                    <div>
                      <h4 className="text-sm font-semibold mb-2 flex items-center gap-1.5">
                        <Info className="h-3.5 w-3.5 text-blue-500" />
                        Premissas
                      </h4>
                      <ul className="space-y-1">
                        {artifactMeta.assumptions.map((a) => (
                          <li
                            key={a}
                            className="text-xs text-muted-foreground flex items-start gap-2"
                          >
                            <ChevronRight className="h-3 w-3 mt-0.5 shrink-0" />
                            {a}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* ================================================================
            TAB: Performance
        ================================================================ */}
        <TabsContent value="performance">
          <div className="space-y-6">
            {/* Main metrics */}
            {loading ? (
              <SkeletonCards count={6} />
            ) : best ? (
              <div className="grid gap-4 grid-cols-2 sm:grid-cols-3 lg:grid-cols-6">
                {[
                  { label: 'Recall', value: best.recall, key: true, term: 'Recall' },
                  { label: 'Precision', value: best.precision, term: 'Precision' },
                  { label: 'F1-Score', value: best.f1 },
                  { label: 'F2-Score', value: best.f2, term: 'F2-Score' },
                  { label: 'PR-AUC', value: best.pr_auc, term: 'PR-AUC' },
                  { label: 'Brier Score', value: best.brier_score, lower: true, term: 'Brier Score' },
                ].map((m) => (
                  <Card key={m.label} className="card-hover">
                    <CardContent className="p-4 text-center">
                      <p className="text-xs text-muted-foreground">{m.term ? <GlossaryTip term={m.term}>{m.label}</GlossaryTip> : m.label}</p>
                      <p className={`text-2xl font-bold mt-1 ${m.key ? 'text-primary' : ''}`}>
                        {m.lower ? m.value.toFixed(3) : formatPercentage(m.value, 1)}
                      </p>
                      {m.key && comparison?.constraints_applied?.min_recall != null && (
                        <p className="text-[10px] text-green-600 dark:text-green-400 mt-0.5">
                          {m.value >= comparison.constraints_applied.min_recall
                            ? `✓ Meta ≥ ${formatPercentage(comparison.constraints_applied.min_recall, 0)}`
                            : `✗ Abaixo da meta ${formatPercentage(comparison.constraints_applied.min_recall, 0)}`}
                        </p>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : (
              <Card>
                <CardContent className="p-6 text-center text-muted-foreground text-sm">
                  Métricas não disponíveis
                </CardContent>
              </Card>
            )}

            {/* Why recall */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">
                  Por que {comparison?.primary_metric?.toUpperCase() ?? 'Recall'} como Métrica
                  Principal?
                </CardTitle>
                {comparison?.selection_criteria && (
                  <CardDescription>
                    Critério de seleção: {comparison.selection_criteria}
                  </CardDescription>
                )}
              </CardHeader>
              <CardContent>
                <div className="grid gap-4 grid-cols-1 sm:grid-cols-3">
                  <div className="p-4 rounded-lg bg-muted/50">
                    <p className="text-sm font-medium flex items-center gap-2 mb-2">
                      <AlertTriangle className="h-4 w-4 text-amber-500" />
                      Custo Assimétrico
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Não identificar um aluno em risco (<GlossaryTip term="Falso Negativo (FN)">FN</GlossaryTip>) tem custo muito maior do que um <GlossaryTip term="Falso Positivo (FP)">falso alerta (FP)</GlossaryTip>.
                    </p>
                  </div>
                  <div className="p-4 rounded-lg bg-muted/50">
                    <p className="text-sm font-medium flex items-center gap-2 mb-2">
                      <Target className="h-4 w-4 text-primary" />
                      Objetivo Operacional
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Maximizar cobertura de alunos vulneráveis para intervenção preventiva.
                    </p>
                  </div>
                  <div className="p-4 rounded-lg bg-muted/50">
                    <p className="text-sm font-medium flex items-center gap-2 mb-2">
                      <CheckCircle2 className="h-4 w-4 text-green-500" />
                      Trade-off Aceito
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Precisão mais baixa é aceitável se recall alto — falsos alertas custam menos
                      que crianças não atendidas.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Confusion Matrix */}
            {best && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Matriz de Confusão (Teste Final)</CardTitle>
                  <CardDescription className="flex items-center gap-1">
                    {best.n_samples} amostras ({best.n_positive} positivos ={' '}
                    {((best.n_positive / best.n_samples) * 100).toFixed(1)}%) · Threshold:{' '}
                    {best.threshold}
                    <InfoTooltip content="TP = corretamente identificou risco. FN = não identificou risco real (pior caso). FP = falso alarme. TN = corretamente dispensou." />
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <ConfusionMatrix
                    matrix={best.confusion_matrix}
                    nSamples={best.n_samples}
                    nPositive={best.n_positive}
                    threshold={best.threshold}
                    fn={best.false_negatives}
                  />
                </CardContent>
              </Card>
            )}

            {/* ROC Curve (synthetic from metrics) */}
            {best && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base flex items-center gap-2">
                    <TrendingUp className="h-4 w-4 text-primary" />
                    Curva ROC (Estimada)
                    <InfoTooltip content="ROC = Receiver Operating Characteristic. Mostra o trade-off entre TPR (Recall) e FPR. Quanto mais próxima do canto superior-esquerdo, melhor. AUC=1.0 é perfeito, AUC=0.5 é aleatório." />
                  </CardTitle>
                  <CardDescription>
                    PR-AUC: {formatPercentage(best.pr_auc, 1)} · Recall: {formatPercentage(best.recall, 1)} · Curva sintética estimada a partir das métricas
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <ROCCurve
                    points={(() => {
                      // Generate synthetic ROC points from known metrics
                      const recall = best.recall
                      const tn = best.confusion_matrix?.[0]?.[0] ?? 0
                      const fp = best.confusion_matrix?.[0]?.[1] ?? 0
                      const fpr = fp / (fp + tn) || 0.05
                      const pts: ROCPoint[] = [
                        { fpr: 0, tpr: 0 },
                        { fpr: fpr * 0.2, tpr: recall * 0.5 },
                        { fpr: fpr * 0.5, tpr: recall * 0.75 },
                        { fpr: fpr * 0.8, tpr: recall * 0.9 },
                        { fpr, tpr: recall },
                        { fpr: fpr + (1 - fpr) * 0.3, tpr: recall + (1 - recall) * 0.5 },
                        { fpr: fpr + (1 - fpr) * 0.6, tpr: recall + (1 - recall) * 0.8 },
                        { fpr: 1, tpr: 1 },
                      ]
                      return pts
                    })()}
                  />
                </CardContent>
              </Card>
            )}

            {/* Model comparison table */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Comparativo de Modelos</CardTitle>
                <CardDescription>
                  {ranking.length} modelos avaliados · Métrica primária:{' '}
                  {comparison?.primary_metric?.toUpperCase() ?? '—'}
                </CardDescription>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <SkeletonRows rows={4} />
                ) : (
                  <div className="space-y-3">
                    {ranking
                      .slice()
                      .sort((a, b) => a.rank - b.rank)
                      .map((m) => {
                        const isSelected = m.model === comparison?.best_model
                        return (
                          <div
                            key={m.model}
                            className={`flex items-center gap-4 p-3 rounded-lg ${
                              isSelected
                                ? 'bg-primary/5 border border-primary/20'
                                : 'hover:bg-muted/50'
                            }`}
                          >
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2">
                                <Badge
                                  variant="outline"
                                  className="text-[10px] font-mono shrink-0"
                                >
                                  #{m.rank}
                                </Badge>
                                <span className="text-sm font-medium truncate">
                                  {displayModelName(m.model)}
                                </span>
                                {isSelected && (
                                  <Badge variant="default" className="text-[10px]">
                                    Selecionado
                                  </Badge>
                                )}
                              </div>
                            </div>
                            <div className="flex gap-4 sm:gap-6 text-sm shrink-0">
                              <div className="text-center">
                                <p className="text-[10px] text-muted-foreground">Recall</p>
                                <p className="font-mono font-medium">
                                  {formatPercentage(m.recall)}
                                </p>
                              </div>
                              <div className="text-center">
                                <p className="text-[10px] text-muted-foreground">Precision</p>
                                <p className="font-mono">{formatPercentage(m.precision)}</p>
                              </div>
                              <div className="text-center">
                                <p className="text-[10px] text-muted-foreground">F2</p>
                                <p className="font-mono">{formatPercentage(m.f2)}</p>
                              </div>
                              <div className="text-center hidden sm:block">
                                <p className="text-[10px] text-muted-foreground">PR-AUC</p>
                                <p className="font-mono">{formatPercentage(m.pr_auc)}</p>
                              </div>
                              <div className="text-center hidden sm:block">
                                <p className="text-[10px] text-muted-foreground">Brier</p>
                                <p className="font-mono">{m.brier_score.toFixed(3)}</p>
                              </div>
                            </div>
                          </div>
                        )
                      })}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* ================================================================
            TAB: Features
        ================================================================ */}
        <TabsContent value="features">
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Layers className="h-4 w-4 text-primary" />
                  Features do Modelo
                </CardTitle>
                <CardDescription>
                  {expectedFeatures.length} features esperadas pelo modelo
                </CardDescription>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <SkeletonRows rows={13} />
                ) : (
                  <div className="space-y-2">
                    {expectedFeatures.map((feat, i) => (
                      <div
                        key={feat}
                        className="flex items-center gap-3 p-2 rounded hover:bg-muted/50"
                      >
                        <span className="text-xs text-muted-foreground w-6">{i + 1}</span>
                        <span className="font-mono text-sm">{feat}</span>
                        <Badge variant="secondary" className="text-[10px] ml-auto">
                          {feat.includes('instituicao')
                            ? 'categorical'
                            : 'numeric'}
                        </Badge>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Shield className="h-4 w-4 text-red-500" />
                  Features Bloqueadas
                </CardTitle>
                <CardDescription>
                  Features que NÃO devem ser usadas (leakage / PII)
                </CardDescription>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <Skeleton className="h-8 w-full" />
                ) : (
                  <div className="flex flex-wrap gap-2">
                    {blockedFeatures.map((feat) => (
                      <Badge key={feat} variant="destructive" className="text-xs">
                        {feat}
                      </Badge>
                    ))}
                    {blockedFeatures.length === 0 && (
                      <p className="text-sm text-muted-foreground">
                        Nenhuma feature bloqueada registrada
                      </p>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <FlaskConical className="h-4 w-4 text-primary" />
                  Importância Relativa das Features
                  <InfoTooltip content="Importância estimada por heurística. Para valores reais, usar SHAP (SHapley Additive exPlanations) ou permutation importance." />
                </CardTitle>
                <CardDescription>
                  Valores ilustrativos — importância real requer análise SHAP
                </CardDescription>
              </CardHeader>
              <CardContent>
                <FeatureImportance
                  data={featureImportanceMock.map((f) => ({ feature: f.name, importance: f.importance }))}
                  height={Math.max(250, featureImportanceMock.length * 35)}
                />
                <p className="mt-4 text-[10px] text-muted-foreground text-center italic">
                  ⚠ Importâncias ilustrativas. Ordem baseada em heurística, não em SHAP values
                  reais.
                </p>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* ================================================================
            TAB: Ethics
        ================================================================ */}
        <TabsContent value="ethics">
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="h-5 w-5 text-primary" />
                  Privacidade e LGPD
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 grid-cols-1 sm:grid-cols-2">
                  {[
                    {
                      title: 'Dados Sensíveis',
                      desc: 'Nenhum dado pessoal identificável (PII) é armazenado nos logs da API. Campos como RA, nome, endereço são automaticamente filtrados.',
                      icon: '🔒',
                    },
                    {
                      title: 'Modo de Privacidade',
                      desc: 'O sistema opera em modo "aggregate_only" — apenas estatísticas agregadas são mantidas, sem valores individuais.',
                      icon: '📊',
                    },
                    {
                      title: 'Retenção de Dados',
                      desc: 'Logs de inferência são retidos por no máximo 30 dias, após o qual são automaticamente removidos.',
                      icon: '🗓️',
                    },
                    {
                      title: 'Auditoria',
                      desc: 'Todas as inferências geram registros de auditoria com hash dos inputs (sem dados reais) para rastreabilidade.',
                      icon: '📝',
                    },
                  ].map((item) => (
                    <div key={item.title} className="p-4 rounded-lg border">
                      <p className="font-medium text-sm flex items-center gap-2 mb-2">
                        <span>{item.icon}</span>
                        {item.title}
                      </p>
                      <p className="text-xs text-muted-foreground leading-relaxed">{item.desc}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5 text-amber-500" />
                  Considerações Éticas
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4 text-sm">
                <div className="p-4 rounded-lg bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800">
                  <p className="font-medium mb-2">⚠️ Decisão Humana Obrigatória</p>
                  <p className="text-xs text-muted-foreground">
                    O score de risco é uma <strong>ferramenta de apoio</strong> à decisão, NÃO um
                    veredicto final. Toda intervenção deve ser avaliada e aprovada por profissionais
                    qualificados (coordenadores pedagógicos, assistentes sociais).
                  </p>
                </div>

                <div className="space-y-3">
                  {[
                    {
                      title: 'Viéses Potenciais',
                      desc: 'O modelo é avaliado quanto a viéses por gênero, fase e instituição. Consulte a aba "Fairness" para métricas detalhadas de equidade por subgrupo.',
                    },
                    {
                      title: 'Transparência',
                      desc: 'Scores e critérios devem ser comunicados de forma clara aos responsáveis e equipe pedagógica.',
                    },
                    {
                      title: 'Direito à Contestação',
                      desc: 'Pais e responsáveis devem ter o direito de questionar e contestar classificações de risco.',
                    },
                    {
                      title: 'Reavaliação Periódica',
                      desc: 'O modelo deve ser reavaliado periodicamente para garantir que não está perpetuando desigualdades.',
                    },
                  ].map((item) => (
                    <div key={item.title} className="flex items-start gap-3 p-2">
                      <Clock className="h-4 w-4 text-muted-foreground mt-0.5 shrink-0" />
                      <div>
                        <p className="font-medium text-sm">{item.title}</p>
                        <p className="text-xs text-muted-foreground mt-0.5">{item.desc}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Assumptions from metadata */}
            {artifactMeta?.assumptions && artifactMeta.assumptions.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <ListChecks className="h-5 w-5 text-blue-500" />
                    Premissas do Modelo
                  </CardTitle>
                  <CardDescription>
                    Premissas registradas nos metadados do artefato
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {artifactMeta.assumptions.map((a) => (
                      <div
                        key={a}
                        className="flex items-start gap-3 p-2 rounded hover:bg-muted/50"
                      >
                        <Info className="h-4 w-4 text-blue-500 mt-0.5 shrink-0" />
                        <p className="text-sm text-muted-foreground">{a}</p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>

        {/* ================================================================
            TAB: Fairness
        ================================================================ */}
        <TabsContent value="fairness">
          <div className="space-y-6">
            {/* Header explanation */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Scale className="h-5 w-5 text-primary" />
                  Análise de Fairness
                </CardTitle>
                <CardDescription>
                  Avaliação de equidade do modelo por subgrupos demográficos.
                  Disparidade de <GlossaryTip term="Recall">recall</GlossaryTip> mede a diferença entre o melhor e pior
                  recall entre subgrupos — valores menores indicam maior equidade.
                </CardDescription>
              </CardHeader>
              <CardContent>
                {loading && !fairness ? (
                  <SkeletonRows rows={6} />
                ) : !fairness ? (
                  <div className="text-center py-8 text-muted-foreground">
                    <Scale className="h-12 w-12 mx-auto mb-3 opacity-30" />
                    <p className="text-sm">Dados de fairness não disponíveis</p>
                    <p className="text-xs mt-1">
                      Execute <code className="bg-muted px-1 py-0.5 rounded">scripts/compute_fairness.py</code> para gerar a análise
                    </p>
                  </div>
                ) : (
                  <div className="space-y-6">
                    {/* Overall metrics */}
                    <div className="p-4 rounded-lg bg-muted/30 border">
                      <h4 className="font-semibold text-sm mb-3">Métricas Globais (N = {fairness.overall.n})</h4>
                      <div className="grid gap-3 grid-cols-2 sm:grid-cols-4 text-center">
                        <div>
                          <p className="text-xs text-muted-foreground">Recall</p>
                          <p className="text-lg font-bold">{formatPercentage(fairness.overall.recall ?? 0)}</p>
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground">Precision</p>
                          <p className="text-lg font-bold">{formatPercentage(fairness.overall.precision ?? 0)}</p>
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground">F1</p>
                          <p className="text-lg font-bold">{formatPercentage(fairness.overall.f1 ?? 0)}</p>
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground">Prevalência</p>
                          <p className="text-lg font-bold">{formatPercentage(fairness.overall.prevalence)}</p>
                        </div>
                      </div>
                    </div>

                    {/* Disparity summary */}
                    <div>
                      <h4 className="font-semibold text-sm mb-3">Resumo de Disparidade (Recall)</h4>
                      <DisparitySummary
                        generoDisparity={
                          (fairness.subgroups.genero._disparity as { recall_disparity: number })
                            ?.recall_disparity ?? null
                        }
                        faseDisparity={
                          (fairness.subgroups.fase._disparity as { recall_disparity: number })
                            ?.recall_disparity ?? null
                        }
                        instituicaoDisparity={
                          (fairness.subgroups.instituicao._disparity as { recall_disparity: number })
                            ?.recall_disparity ?? null
                        }
                      />
                    </div>

                    {/* Detailed tables */}
                    <FairnessTable
                      title="Gênero"
                      description="Métricas por gênero do aluno"
                      group={fairness.subgroups.genero}
                      icon="👥"
                    />

                    <FairnessTable
                      title="Fase"
                      description="Métricas por fase/série escolar"
                      group={fairness.subgroups.fase}
                      icon="📚"
                    />

                    <FairnessTable
                      title="Instituição"
                      description="Métricas por tipo de instituição de ensino"
                      group={fairness.subgroups.instituicao}
                      icon="🏫"
                    />

                    {/* Interpretation guide */}
                    <div className="p-4 rounded-lg bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800">
                      <p className="font-medium text-sm mb-2">📖 Como interpretar</p>
                      <ul className="text-xs text-muted-foreground space-y-1.5">
                        <li>• <strong>Disparidade ≤ 5%</strong>: Excelente equidade — sem ação necessária</li>
                        <li>• <strong>Disparidade 5-10%</strong>: Aceitável — monitorar nas próximas versões</li>
                        <li>• <strong>Disparidade 10-15%</strong>: Atenção — investigar causas e considerar mitigação</li>
                        <li>• <strong>Disparidade &gt; 15%</strong>: Alto — ação corretiva recomendada (reamostragem, re-ponderação)</li>
                        <li>• Subgrupos com <strong>"—"</strong> não possuem amostras positivas suficientes para cálculo</li>
                      </ul>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* ================================================================
            TAB: Governance (NEW)
        ================================================================ */}
        <TabsContent value="governance">
          <div className="space-y-6">
            {/* Threshold & Selection Policy */}
            <div className="grid gap-6 grid-cols-1 lg:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Hash className="h-5 w-5 text-primary" />
                    Política de Threshold
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {loading ? (
                    <SkeletonRows rows={4} />
                  ) : (
                    <div className="space-y-3 text-sm">
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Objetivo</span>
                        <span className="font-medium">
                          {artifactMeta?.threshold_policy?.objective ?? '—'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Threshold Value</span>
                        <span className="font-mono">
                          {artifactMeta?.threshold_policy?.threshold_value ??
                            best?.threshold ??
                            '—'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Min Precision</span>
                        <span className="font-mono">
                          {artifactMeta?.threshold_policy?.min_precision ?? 'N/A'}
                        </span>
                      </div>
                      <Separator />
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Critério de Seleção</span>
                        <span className="font-medium">
                          {comparison?.selection_criteria ?? '—'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Métrica Primária</span>
                        <Badge variant="outline">
                          {comparison?.primary_metric?.toUpperCase() ?? '—'}
                        </Badge>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Settings2 className="h-5 w-5 text-primary" />
                    Constraints & Seleção
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {loading ? (
                    <SkeletonRows rows={5} />
                  ) : (
                    <div className="space-y-4 text-sm">
                      <div>
                        <h4 className="font-semibold mb-2">Restrições Aplicadas</h4>
                        {comparison?.constraints_applied ? (
                          <div className="space-y-2">
                            {Object.entries(comparison.constraints_applied).map(([k, v]) => (
                              <div
                                key={k}
                                className="flex justify-between p-2 rounded bg-muted/50"
                              >
                                <span className="font-mono text-xs">{k}</span>
                                <span className="font-mono font-medium">{String(v)}</span>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <p className="text-muted-foreground">Nenhuma restrição registrada</p>
                        )}
                      </div>
                      <Separator />
                      <div>
                        <h4 className="font-semibold mb-2">Modelo Selecionado</h4>
                        <div className="flex items-center gap-2">
                          <Badge variant="default">
                            {comparison?.best_model
                              ? displayModelName(comparison.best_model)
                              : '—'}
                          </Badge>
                          {best?.calibration_error != null && (
                            <span className="text-xs text-muted-foreground">
                              Erro de calibração: {best.calibration_error.toFixed(4)}
                            </span>
                          )}
                        </div>
                      </div>
                      <Separator />
                      <div>
                        <h4 className="font-semibold mb-2">Versionamento</h4>
                        <div className="space-y-1 text-xs text-muted-foreground">
                          <p>
                            Versão:{' '}
                            <Badge variant="outline" className="text-[10px]">
                              {artifactMeta?.model_version ?? metadata?.model_version ?? '—'}
                            </Badge>
                          </p>
                          <p>
                            Criado em:{' '}
                            {fmtDate(artifactMeta?.created_at ?? metadata?.created_at)}
                          </p>
                          <p>scikit-learn: {artifactMeta?.sklearn_version ?? artifactMeta?.libs_versions?.sklearn ?? '—'}</p>
                        </div>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* Premissas */}
            {artifactMeta?.assumptions && artifactMeta.assumptions.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <ListChecks className="h-5 w-5 text-blue-500" />
                    Premissas Registradas
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {artifactMeta.assumptions.map((a, i) => (
                      <div
                        key={i}
                        className="flex items-start gap-3 p-2 rounded bg-blue-50 dark:bg-blue-950/20"
                      >
                        <span className="text-xs font-mono text-blue-600 mt-0.5">{i + 1}</span>
                        <p className="text-sm">{a}</p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Model Report */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="h-5 w-5 text-primary" />
                  Relatório do Modelo
                </CardTitle>
                <CardDescription>
                  Documento gerado automaticamente — definição do problema, resultados, comparativo e limitações
                </CardDescription>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <SkeletonRows rows={12} />
                ) : report ? (
                  <div
                    className="prose prose-sm dark:prose-invert max-w-none text-sm leading-relaxed max-h-[600px] overflow-y-auto pr-2"
                    dangerouslySetInnerHTML={{ __html: renderMarkdown(report) }}
                  />
                ) : (
                  <p className="text-sm text-muted-foreground text-center py-8">
                    Relatório não disponível. Verifique o endpoint /artifacts/report.
                  </p>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* ================================================================
            TAB: Comparação (NEW)
        ================================================================ */}
        <TabsContent value="comparison">
          <div className="space-y-6">
            {/* Bump Ranking Chart */}
            {comparison && ranking.length > 1 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <TrendingUp className="h-5 w-5 text-primary" />
                    Ranking por Métrica
                    <InfoTooltip content="Bump chart mostra como a posição relativa de cada modelo muda conforme a métrica de avaliação. Linhas que sobem indicam melhoria de ranking." />
                  </CardTitle>
                  <CardDescription>
                    Posição relativa dos modelos por métrica — quanto menor, melhor
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <BumpRanking
                    data={(() => {
                      const metrics = ['Recall', 'Precision', 'F1', 'F2', 'PR-AUC']
                      const modelKeys = Object.keys(comparison.test_results ?? comparison.validation_results)
                      const bumpData: BumpSerie[] = modelKeys.map((key) => {
                        const test = comparison.test_results?.[key] ?? comparison.validation_results[key]
                        const vals = test ? [test.recall, test.precision, test.f1, test.f2, test.pr_auc] : [0, 0, 0, 0, 0]
                        return {
                          id: displayModelName(key),
                          data: metrics.map((m, i) => {
                            // Calculate rank for this metric
                            const allVals = modelKeys.map((k) => {
                              const t = comparison.test_results?.[k] ?? comparison.validation_results[k]
                              return t ? [t.recall, t.precision, t.f1, t.f2, t.pr_auc][i] : 0
                            })
                            const sorted = [...allVals].sort((a, b) => b - a)
                            const rank = sorted.indexOf(vals[i]) + 1
                            return { x: m, y: rank }
                          }),
                        }
                      })
                      return bumpData
                    })()}
                    height={280}
                  />
                </CardContent>
              </Card>
            )}

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <GitCompare className="h-5 w-5 text-primary" />
                  Validação vs Teste — Todos os Modelos
                </CardTitle>
                <CardDescription>
                  Clique em um modelo para visualizar sua matriz de confusão
                </CardDescription>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <SkeletonRows rows={6} />
                ) : comparison ? (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b">
                          <th className="text-left py-2 px-3 font-semibold" rowSpan={2}>
                            Modelo
                          </th>
                          <th
                            className="text-center py-1 px-2 font-semibold text-blue-600 dark:text-blue-400 border-b"
                            colSpan={5}
                          >
                            Validação
                          </th>
                          <th
                            className="text-center py-1 px-2 font-semibold text-emerald-600 dark:text-emerald-400 border-b"
                            colSpan={5}
                          >
                            Teste
                          </th>
                        </tr>
                        <tr className="border-b text-[10px] text-muted-foreground">
                          {['Recall', 'Prec', 'F1', 'F2', 'Brier'].map((h) => (
                            <th key={`v-${h}`} className="py-1 px-2 text-center font-medium">
                              {h}
                            </th>
                          ))}
                          {['Recall', 'Prec', 'F1', 'F2', 'Brier'].map((h) => (
                            <th key={`t-${h}`} className="py-1 px-2 text-center font-medium">
                              {h}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {Object.keys(comparison.validation_results).map((modelKey) => {
                          const val = comparison.validation_results[modelKey]
                          const test = comparison.test_results?.[modelKey]
                          const isSelected = selectedCompModel === modelKey
                          const isBest = modelKey === comparison.best_model

                          return (
                            <tr
                              key={modelKey}
                              onClick={() => setSelectedCompModel(modelKey)}
                              className={`border-b cursor-pointer transition-colors ${
                                isSelected
                                  ? 'bg-primary/5 border-primary/20'
                                  : 'hover:bg-muted/50'
                              }`}
                            >
                              <td className="py-2 px-3 font-medium whitespace-nowrap">
                                <div className="flex items-center gap-2">
                                  {displayModelName(modelKey)}
                                  {isBest && (
                                    <Badge variant="default" className="text-[9px]">
                                      Best
                                    </Badge>
                                  )}
                                </div>
                              </td>
                              {/* Validation */}
                              <td className="py-2 px-2 text-center font-mono text-xs">
                                {val ? formatPercentage(val.recall, 1) : '—'}
                              </td>
                              <td className="py-2 px-2 text-center font-mono text-xs">
                                {val ? formatPercentage(val.precision, 1) : '—'}
                              </td>
                              <td className="py-2 px-2 text-center font-mono text-xs">
                                {val ? formatPercentage(val.f1, 1) : '—'}
                              </td>
                              <td className="py-2 px-2 text-center font-mono text-xs">
                                {val ? formatPercentage(val.f2, 1) : '—'}
                              </td>
                              <td className="py-2 px-2 text-center font-mono text-xs">
                                {val ? val.brier_score.toFixed(3) : '—'}
                              </td>
                              {/* Test */}
                              <td className="py-2 px-2 text-center font-mono text-xs">
                                {test ? formatPercentage(test.recall, 1) : '—'}
                              </td>
                              <td className="py-2 px-2 text-center font-mono text-xs">
                                {test ? formatPercentage(test.precision, 1) : '—'}
                              </td>
                              <td className="py-2 px-2 text-center font-mono text-xs">
                                {test ? formatPercentage(test.f1, 1) : '—'}
                              </td>
                              <td className="py-2 px-2 text-center font-mono text-xs">
                                {test ? formatPercentage(test.f2, 1) : '—'}
                              </td>
                              <td className="py-2 px-2 text-center font-mono text-xs">
                                {test ? test.brier_score.toFixed(3) : '—'}
                              </td>
                            </tr>
                          )
                        })}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground text-center py-8">
                    Dados de comparação não disponíveis
                  </p>
                )}
              </CardContent>
            </Card>

            {/* Confusion matrix for selected model */}
            {selectedCompModel && comparison && (
              <div className="grid gap-6 grid-cols-1 lg:grid-cols-2">
                {/* Validation confusion matrix */}
                {comparison.validation_results[selectedCompModel]?.confusion_matrix && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base flex items-center gap-2">
                        <span className="text-blue-600 dark:text-blue-400">●</span>
                        Matriz de Confusão — Validação
                      </CardTitle>
                      <CardDescription>
                        {displayModelName(selectedCompModel)}
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <ConfusionMatrix
                        matrix={
                          comparison.validation_results[selectedCompModel].confusion_matrix
                        }
                        nSamples={comparison.validation_results[selectedCompModel].n_samples}
                        nPositive={comparison.validation_results[selectedCompModel].n_positive}
                        threshold={comparison.validation_results[selectedCompModel].threshold}
                        fn={comparison.validation_results[selectedCompModel].false_negatives}
                      />
                    </CardContent>
                  </Card>
                )}

                {/* Test confusion matrix */}
                {comparison.test_results?.[selectedCompModel]?.confusion_matrix && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base flex items-center gap-2">
                        <span className="text-emerald-600 dark:text-emerald-400">●</span>
                        Matriz de Confusão — Teste
                      </CardTitle>
                      <CardDescription>
                        {displayModelName(selectedCompModel)}
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <ConfusionMatrix
                        matrix={comparison.test_results[selectedCompModel].confusion_matrix}
                        nSamples={comparison.test_results[selectedCompModel].n_samples}
                        nPositive={comparison.test_results[selectedCompModel].n_positive}
                        threshold={comparison.test_results[selectedCompModel].threshold}
                        fn={comparison.test_results[selectedCompModel].false_negatives}
                      />
                    </CardContent>
                  </Card>
                )}
              </div>
            )}

            {/* Per-model detail cards */}
            {selectedCompModel && comparison && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">
                    Métricas Detalhadas — {displayModelName(selectedCompModel)}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid gap-6 grid-cols-1 sm:grid-cols-2">
                    {(
                      [
                        {
                          label: 'Validação',
                          data: comparison.validation_results[selectedCompModel],
                          color: 'text-blue-600 dark:text-blue-400',
                        },
                        {
                          label: 'Teste',
                          data: comparison.test_results?.[selectedCompModel],
                          color: 'text-emerald-600 dark:text-emerald-400',
                        },
                      ] as const
                    )
                      .filter((s) => s.data)
                      .map((section) => (
                        <div key={section.label}>
                          <h4 className={`font-semibold mb-3 ${section.color}`}>
                            {section.label}
                          </h4>
                          <div className="space-y-2 text-sm">
                            {(
                              [
                                ['Recall', section.data!.recall],
                                ['Precision', section.data!.precision],
                                ['F1', section.data!.f1],
                                ['F2', section.data!.f2],
                                ['PR-AUC', section.data!.pr_auc],
                                ['Brier Score', section.data!.brier_score],
                                ['Erro de Calibração', section.data!.calibration_error],
                              ] as [string, number][]
                            ).map(([name, val]) => (
                              <div
                                key={name}
                                className="flex justify-between p-1.5 rounded hover:bg-muted/50"
                              >
                                <span className="text-muted-foreground">{name}</span>
                                <span className="font-mono">
                                  {name.includes('Brier') || name.includes('Calibração')
                                    ? val?.toFixed(4) ?? '—'
                                    : val != null
                                      ? formatPercentage(val, 1)
                                      : '—'}
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>

        {/* ================================================================
            TAB: Reprodutibilidade (NEW)
        ================================================================ */}
        <TabsContent value="reproducibility">
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Fingerprint className="h-5 w-5 text-primary" />
                  Reprodutibilidade do Experimento
                  <InfoTooltip content="Informações necessárias para reproduzir exatamente o treinamento e resultados deste modelo. Essencial para auditoria e validação acadêmica." />
                </CardTitle>
                <CardDescription>
                  Todos os parâmetros necessários para replicar o treinamento
                </CardDescription>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <SkeletonRows rows={10} />
                ) : (
                  <div className="grid gap-6 grid-cols-1 lg:grid-cols-2">
                    <div>
                      <h4 className="font-semibold text-sm mb-3 flex items-center gap-2">
                        <Settings2 className="h-4 w-4 text-primary" />
                        Identificação do Artefato
                      </h4>
                      <div className="space-y-2 text-sm">
                        {[
                          ['Versão do Modelo', artifactMeta?.model_version ?? metadata?.model_version ?? '—'],
                          ['Algoritmo', comparison?.best_model ? displayModelName(comparison.best_model) : metadata?.model_family ?? '—'],
                          ['Framework', `scikit-learn ${artifactMeta?.sklearn_version ?? '—'}`],
                          ['Seed', String(artifactMeta?.seed ?? '—')],
                          ['Criado em', fmtDate(artifactMeta?.created_at ?? metadata?.created_at)],
                          ['Períodos de Treino', artifactMeta?.training_periods?.join(', ') ?? '—'],
                          ['Filtro de População', artifactMeta?.population_filter ?? '—'],
                        ].map(([label, value]) => (
                          <div key={label} className="flex justify-between p-2 rounded bg-muted/50">
                            <span className="text-muted-foreground">{label}</span>
                            <span className="font-mono text-xs">{value}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                    <div>
                      <h4 className="font-semibold text-sm mb-3 flex items-center gap-2">
                        <Hash className="h-4 w-4 text-primary" />
                        Configuração do Threshold
                      </h4>
                      <div className="space-y-2 text-sm">
                        {[
                          ['Threshold', String(best?.threshold ?? artifactMeta?.threshold_policy?.threshold_value ?? '—')],
                          ['Objetivo', artifactMeta?.threshold_policy?.objective ?? '—'],
                          ['Min Precision', String(artifactMeta?.threshold_policy?.min_precision ?? 'N/A')],
                          ['Métrica Primária', comparison?.primary_metric?.toUpperCase() ?? '—'],
                          ['Critério de Seleção', comparison?.selection_criteria ?? '—'],
                        ].map(([label, value]) => (
                          <div key={label} className="flex justify-between p-2 rounded bg-muted/50">
                            <span className="text-muted-foreground">{label}</span>
                            <span className="font-mono text-xs">{value}</span>
                          </div>
                        ))}
                      </div>
                      <div className="mt-4">
                        <h4 className="font-semibold text-sm mb-3 flex items-center gap-2">
                          <Layers className="h-4 w-4 text-primary" />
                          Features ({expectedFeatures.length})
                        </h4>
                        <div className="flex flex-wrap gap-1.5">
                          {expectedFeatures.map((f) => (
                            <Badge key={f} variant="secondary" className="text-[10px] font-mono">{f}</Badge>
                          ))}
                        </div>
                        {blockedFeatures.length > 0 && (
                          <div className="mt-3">
                            <p className="text-xs text-muted-foreground mb-1.5">Bloqueadas (leakage/PII):</p>
                            <div className="flex flex-wrap gap-1.5">
                              {blockedFeatures.map((f) => (
                                <Badge key={f} variant="destructive" className="text-[10px] font-mono">{f}</Badge>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Constraints */}
            {comparison?.constraints_applied && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base flex items-center gap-2">
                    <Shield className="h-4 w-4 text-primary" />
                    Restrições Aplicadas na Seleção
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid gap-3 grid-cols-1 sm:grid-cols-2 lg:grid-cols-4">
                    {Object.entries(comparison.constraints_applied).map(([k, v]) => (
                      <div key={k} className="p-3 rounded-lg border bg-card text-center">
                        <p className="text-[10px] text-muted-foreground font-mono">{k}</p>
                        <p className="text-lg font-bold mt-1">{String(v)}</p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Reprodução */}
            <Card className="">
              <CardContent className="p-5">
                <h3 className="font-semibold text-sm flex items-center gap-2 mb-3">
                  <BookOpen className="h-4 w-4 text-primary" />
                  Como Reproduzir
                </h3>
                <div className="space-y-2 text-xs text-muted-foreground">
                  <p>1. Clone o repositório e instale dependências: <code className="bg-muted px-1 rounded">pip install -r requirements.txt</code></p>
                  <p>2. Execute o pipeline completo: <code className="bg-muted px-1 rounded">python -m src.retrain</code></p>
                  <p>3. Os mesmos artefatos serão gerados em <code className="bg-muted px-1 rounded">artifacts/</code> com seed={artifactMeta?.seed ?? 42}</p>
                  <p>4. Compare métricas via <code className="bg-muted px-1 rounded">artifacts/model_comparison.json</code></p>
                  <p>5. Deploy via Docker: <code className="bg-muted px-1 rounded">docker compose up --build</code></p>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}
