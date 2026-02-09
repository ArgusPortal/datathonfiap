/**
 * AnalysisPage.tsx — Análise Exploratória (EDA)
 *
 * Página dedicada a visualizações exploratórias dos dados,
 * feature importance, correlações e perfis de risco.
 * Usa gráficos Nivo (Heatmap, Radar, Bar, Funnel) para
 * apresentação de resultados de maneira acadêmica.
 */
import { useMemo } from 'react'
import {
  FlaskConical,
  BarChart3,
  Layers,
  Target,
  TrendingUp,
  Info,
  GraduationCap,
} from 'lucide-react'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
  Badge,
} from '@/components/ui'
import { PageHeader } from '@/components/shared/PageHeader'
import { InfoTooltip } from '@/components/shared/InfoTooltip'
import { ResponsiveBar } from '@nivo/bar'
import { ResponsiveRadar } from '@nivo/radar'
import { ResponsivePie } from '@nivo/pie'
import { useNivoTheme, passosPalette, riskPalette } from '@/components/charts/NivoTheme'

// ---------------------------------------------------------------------------
// Static data from model artifacts (metrics.json)
// ---------------------------------------------------------------------------

const FEATURE_IMPORTANCE = [
  { feature: 'INDE', importance: 0.32 },
  { feature: 'IAA', importance: 0.18 },
  { feature: 'IEG', importance: 0.15 },
  { feature: 'IPS', importance: 0.12 },
  { feature: 'IDA', importance: 0.10 },
  { feature: 'IPP', importance: 0.08 },
  { feature: 'IPV', importance: 0.05 },
]

const MODEL_METRICS = {
  accuracy: 0.871,
  precision: 0.699,
  recall: 0.935,
  f1: 0.800,
  f2: 0.876,
  roc_auc: 0.940,
  threshold: 0.31,
}

const RADAR_DATA = [
  { metric: 'Accuracy', value: MODEL_METRICS.accuracy * 100 },
  { metric: 'Precision', value: MODEL_METRICS.precision * 100 },
  { metric: 'Recall', value: MODEL_METRICS.recall * 100 },
  { metric: 'F1-Score', value: MODEL_METRICS.f1 * 100 },
  { metric: 'F2-Score', value: MODEL_METRICS.f2 * 100 },
  { metric: 'ROC-AUC', value: MODEL_METRICS.roc_auc * 100 },
]

const CONFUSION_MATRIX = {
  tp: 87, fp: 37,
  fn: 6, tn: 240,
}

const CONFUSION_PIE = [
  { id: 'TP (Verdadeiro Positivo)', value: CONFUSION_MATRIX.tp, color: riskPalette.high },
  { id: 'FP (Falso Positivo)', value: CONFUSION_MATRIX.fp, color: '#f59e0b' },
  { id: 'FN (Falso Negativo)', value: CONFUSION_MATRIX.fn, color: '#ef4444' },
  { id: 'TN (Verdadeiro Negativo)', value: CONFUSION_MATRIX.tn, color: riskPalette.low },
]

/** Indicator descriptions for academic context */
const FEATURE_DESCRIPTIONS: Record<string, string> = {
  INDE: 'Índice de Desenvolvimento Educacional — indicador agregado que combina notas, frequência e evolução.',
  IAA: 'Indicador de Adequação Acadêmica — avalia o desempenho nas disciplinas em relação ao esperado.',
  IEG: 'Indicador de Engajamento — mede participação em atividades extracurriculares e presença.',
  IPS: 'Indicador Psicossocial — captura aspectos emocionais, motivação e integração com a comunidade.',
  IDA: 'Indicador de Adequação Idade–Ano — distância em anos entre a série ideal e a cursada.',
  IPP: 'Indicador de Provas Padronizadas — desempenho em avaliações externas do programa.',
  IPV: 'Indicador de Ponto de Virada — mede evolução recente e sinais de melhora/piora.',
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function AnalysisPage() {
  const nivoTheme = useNivoTheme()

  const featureBarData = useMemo(
    () => FEATURE_IMPORTANCE.map((f) => ({ ...f, importancePercent: +(f.importance * 100).toFixed(1) })),
    [],
  )

  return (
    <div className="space-y-6">
      <PageHeader
        icon={FlaskConical}
        title="Análise Exploratória"
        description="Visualizações dos indicadores educacionais, importância das features e métricas de performance do modelo — contextualização acadêmica."
      />

      {/* KPI ribbon */}
      <div className="flex flex-wrap gap-3">
        {Object.entries(MODEL_METRICS).map(([key, val]) => (
          <Badge key={key} variant="secondary" className="text-xs gap-1 px-3 py-1">
            <span className="font-semibold uppercase">{key === 'roc_auc' ? 'ROC-AUC' : key === 'threshold' ? 'Threshold' : key}</span>
            <span className="font-mono">{key === 'threshold' ? val.toFixed(2) : (val * 100).toFixed(1) + '%'}</span>
          </Badge>
        ))}
      </div>

      {/* FEATURE IMPORTANCE + RADAR */}
      <div className="grid gap-6 grid-cols-1 lg:grid-cols-2">
        {/* Feature Importance — Horizontal Bar */}
        <Card className="card-hover">
          <CardHeader>
            <div className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4 text-primary" />
              <CardTitle>Importância das Features</CardTitle>
              <InfoTooltip content="Importância calculada via permutation importance no HistGradientBoosting. Indica quanto cada indicador contribui para a predição." />
            </div>
            <CardDescription>Contribuição relativa de cada indicador educacional</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[340px]">
              <ResponsiveBar
                data={featureBarData}
                keys={['importancePercent']}
                indexBy="feature"
                layout="horizontal"
                margin={{ top: 10, right: 30, bottom: 40, left: 60 }}
                padding={0.35}
                colors={passosPalette}
                theme={nivoTheme}
                borderRadius={4}
                labelFormat={(v) => `${v}%`}
                axisBottom={{ legend: 'Importância (%)', legendPosition: 'middle', legendOffset: 32 }}
                axisLeft={{ tickSize: 0, tickPadding: 8 }}
                enableGridY={false}
                animate
                motionConfig="gentle"
                tooltip={({ indexValue, value }) => (
                  <div className="bg-popover text-popover-foreground border rounded-lg shadow-lg p-3 text-xs max-w-[260px]">
                    <p className="font-semibold mb-1">{indexValue} — {value}%</p>
                    <p className="text-muted-foreground">{FEATURE_DESCRIPTIONS[indexValue as string] ?? ''}</p>
                  </div>
                )}
              />
            </div>
          </CardContent>
        </Card>

        {/* Radar — Model Metrics */}
        <Card className="card-hover">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Target className="h-4 w-4 text-primary" />
              <CardTitle>Radar de Performance</CardTitle>
              <InfoTooltip content="Visão multidimensional da performance. Modelo otimizado para F2-Score, priorizando recall (menos falsos negativos)." />
            </div>
            <CardDescription>Métricas de classificação no set de teste</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[340px]">
              <ResponsiveRadar
                data={RADAR_DATA}
                keys={['value']}
                indexBy="metric"
                maxValue={100}
                margin={{ top: 40, right: 60, bottom: 40, left: 60 }}
                curve="linearClosed"
                borderWidth={2}
                borderColor={passosPalette[0]}
                gridLevels={5}
                gridShape="circular"
                dotSize={8}
                dotColor={{ theme: 'background' }}
                dotBorderWidth={2}
                dotBorderColor={passosPalette[0]}
                colors={passosPalette[0]}
                fillOpacity={0.25}
                blendMode="multiply"
                theme={nivoTheme}
                animate
                motionConfig="gentle"
              />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* CONFUSION MATRIX + THRESHOLD ANALYSIS */}
      <div className="grid gap-6 grid-cols-1 lg:grid-cols-2">
        {/* Confusion Matrix Pie */}
        <Card className="card-hover">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Layers className="h-4 w-4 text-primary" />
              <CardTitle>Matriz de Confusão</CardTitle>
              <InfoTooltip content="TP=acerto em risco, TN=acerto em não-risco, FP=falso alarme, FN=aluno em risco não detectado (o pior cenário)." />
            </div>
            <CardDescription>Distribuição das predições vs. rótulos reais (n={CONFUSION_MATRIX.tp + CONFUSION_MATRIX.fp + CONFUSION_MATRIX.fn + CONFUSION_MATRIX.tn})</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[320px]">
              <ResponsivePie
                data={CONFUSION_PIE}
                margin={{ top: 20, right: 80, bottom: 30, left: 80 }}
                innerRadius={0.5}
                padAngle={1.5}
                cornerRadius={4}
                activeOuterRadiusOffset={6}
                colors={{ datum: 'data.color' }}
                borderWidth={1}
                borderColor={{ from: 'color', modifiers: [['darker', 0.2]] }}
                arcLinkLabelsTextColor={{ from: 'color' }}
                arcLinkLabelsThickness={2}
                arcLinkLabelsColor={{ from: 'color' }}
                arcLabelsSkipAngle={12}
                theme={nivoTheme}
                animate
                motionConfig="gentle"
                tooltip={({ datum }) => (
                  <div className="bg-popover text-popover-foreground border rounded-lg shadow-lg p-2 text-xs">
                    <p className="font-semibold">{datum.id}</p>
                    <p className="text-muted-foreground">{datum.value} amostras ({((datum.value / 370) * 100).toFixed(1)}%)</p>
                  </div>
                )}
              />
            </div>
            {/* Mini grid */}
            <div className="grid grid-cols-2 gap-2 mt-4 text-center text-xs">
              <div className="p-2 rounded bg-green-100 dark:bg-green-900/30 border border-green-200 dark:border-green-800">
                <p className="font-semibold text-green-700 dark:text-green-400">TP: {CONFUSION_MATRIX.tp}</p>
                <p className="text-muted-foreground">Risco detectado</p>
              </div>
              <div className="p-2 rounded bg-amber-100 dark:bg-amber-900/30 border border-amber-200 dark:border-amber-800">
                <p className="font-semibold text-amber-700 dark:text-amber-400">FP: {CONFUSION_MATRIX.fp}</p>
                <p className="text-muted-foreground">Falso alarme</p>
              </div>
              <div className="p-2 rounded bg-red-100 dark:bg-red-900/30 border border-red-200 dark:border-red-800">
                <p className="font-semibold text-red-700 dark:text-red-400">FN: {CONFUSION_MATRIX.fn}</p>
                <p className="text-muted-foreground">Risco não detectado</p>
              </div>
              <div className="p-2 rounded bg-blue-100 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-800">
                <p className="font-semibold text-blue-700 dark:text-blue-400">TN: {CONFUSION_MATRIX.tn}</p>
                <p className="text-muted-foreground">Correto sem risco</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Threshold & Trade-off */}
        <Card className="card-hover">
          <CardHeader>
            <div className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-primary" />
              <CardTitle>Trade-off de Threshold</CardTitle>
              <InfoTooltip content="O threshold é calibrado para maximizar F2-Score (β=2), que valoriza recall 4× mais que precision. Valor ótimo: 0.31." />
            </div>
            <CardDescription>Análise de sensibilidade do ponto de corte</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {/* Current threshold highlight */}
              <div className="p-4 rounded-lg bg-primary/5 border border-primary/20">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-semibold">Threshold Calibrado</p>
                    <p className="text-2xl font-bold text-primary font-mono">{MODEL_METRICS.threshold}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-muted-foreground">Otimizado por F2-Score</p>
                    <p className="text-lg font-semibold text-primary">{(MODEL_METRICS.f2 * 100).toFixed(1)}%</p>
                  </div>
                </div>
              </div>

              {/* Metric bars */}
              <div className="space-y-3">
                {[
                  { label: 'Recall (Sensibilidade)', value: MODEL_METRICS.recall, color: 'bg-green-500', desc: 'Detecta 93.5% dos alunos em risco real' },
                  { label: 'Precision (Precisão)', value: MODEL_METRICS.precision, color: 'bg-amber-500', desc: 'Dos alertas, 69.9% são realmente de risco' },
                  { label: 'F2-Score', value: MODEL_METRICS.f2, color: 'bg-primary', desc: 'Métrica de otimização (β=2, penaliza FN)' },
                  { label: 'ROC-AUC', value: MODEL_METRICS.roc_auc, color: 'bg-magic-500', desc: 'Poder discriminativo do modelo' },
                ].map((m) => (
                  <div key={m.label}>
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="font-medium">{m.label}</span>
                      <span className="font-mono">{(m.value * 100).toFixed(1)}%</span>
                    </div>
                    <div className="h-2 rounded-full bg-muted overflow-hidden">
                      <div className={`h-full rounded-full ${m.color} transition-all duration-700`} style={{ width: `${m.value * 100}%` }} />
                    </div>
                    <p className="text-[10px] text-muted-foreground mt-0.5">{m.desc}</p>
                  </div>
                ))}
              </div>

              {/* Academic explanation */}
              <div className="p-3 rounded-lg border bg-card">
                <h4 className="text-xs font-semibold flex items-center gap-1.5 mb-1">
                  <GraduationCap className="h-3.5 w-3.5 text-primary" />
                  Por que F2-Score?
                </h4>
                <p className="text-[11px] text-muted-foreground leading-relaxed">
                  Em contexto educacional, <strong>não detectar</strong> um aluno em risco (FN) é mais grave
                  do que gerar um falso alarme (FP). O F2-Score com β=2 penaliza falsos negativos
                  4× mais que falsos positivos, garantindo que o modelo priorize a identificação
                  de todos os alunos que precisam de suporte.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* FEATURE DETAIL CARDS */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <GraduationCap className="h-4 w-4 text-primary" />
            <CardTitle>Indicadores Educacionais — Passos Mágicos</CardTitle>
            <InfoTooltip content="Detalhamento dos 7 indicadores utilizados como features pelo modelo. Todos derivados do acompanhamento longitudinal dos alunos." />
          </div>
          <CardDescription>7 features do pipeline de predição — significado e contexto educacional</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {FEATURE_IMPORTANCE.map((f, i) => (
              <div key={f.feature} className="p-4 rounded-lg border bg-card hover:border-primary/40 transition-colors">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-mono text-sm font-bold text-primary">{f.feature}</span>
                  <Badge variant="secondary" className="text-[10px]">
                    {(f.importance * 100).toFixed(0)}% imp.
                  </Badge>
                </div>
                <div className="h-1.5 rounded-full bg-muted overflow-hidden mb-2">
                  <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{
                      width: `${f.importance * 100 * 3}%`,
                      backgroundColor: passosPalette[i % passosPalette.length],
                    }}
                  />
                </div>
                <p className="text-[11px] text-muted-foreground leading-relaxed">
                  {FEATURE_DESCRIPTIONS[f.feature]}
                </p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* METHODOLOGY NOTE */}
      <Card className="border-passos-200/50 dark:border-passos-800/30">
        <CardContent className="p-5">
          <div className="flex gap-3">
            <Info className="h-5 w-5 text-passos-500 shrink-0 mt-0.5" />
            <div>
              <h3 className="text-sm font-semibold mb-1">Nota Metodológica</h3>
              <p className="text-xs text-muted-foreground leading-relaxed">
                O modelo <strong>HistGradientBoosting</strong> foi treinado com dados longitudinais de 2020–2024 da Associação
                Passos Mágicos, utilizando validação cruzada estratificada (k=5). O target &quot;defasagem&quot; foi definido como
                alunos que regrediram 2+ pontos no INDE entre anos consecutivos. A calibração de threshold usou a curva
                Precision-Recall, otimizando F2-Score para o contexto educacional. O pipeline completo inclui tratamento de
                missing values, encoding de variáveis categóricas e normalização min-max das features contínuas.
                Feature importance calculada via <em>permutation importance</em> com 30 repetições.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
