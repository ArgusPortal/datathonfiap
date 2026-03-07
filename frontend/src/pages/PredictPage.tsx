import { useState, useCallback, useRef } from 'react'
import {
  Brain,
  Upload,
  Loader2,
  AlertCircle,
  CheckCircle2,
  FileSpreadsheet,
  Calculator,
  BookOpen,
  Users as UsersIcon,
  Download,
  Lightbulb,
  TrendingUp,
  Dices,
} from 'lucide-react'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
  Button,
  Input,
  Label,
  Select,
  Badge,
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
  Separator,
} from '@/components/ui'
import { RiskGauge } from '@/components/charts/RiskGauge'
import { ScoreDistribution } from '@/components/charts/ScoreDistribution'
import { RadarProfile } from '@/components/charts/RadarProfile'
import { InfoTooltip } from '@/components/shared/InfoTooltip'
import api from '@/services/api'
import { usePredictionStore } from '@/stores/predictionStore'
import type { PredictionResult, StudentFeatures } from '@/types'
import {
  getRiskLevel,
  getRiskBgClass,
  getRiskLabel,
  parseCSV,
  formatPercentage,
} from '@/lib/utils'
import { FEATURE_METADATA, FEATURE_GROUPS } from '@/lib/features'
import { ShapWaterfall, BusinessRulesCard } from '@/components/shared/Explainability'

export function PredictPage() {
  const [activeTab, setActiveTab] = useState('single')
  const [formData, setFormData] = useState<StudentFeatures>({})
  const [predictions, setPredictions] = useState<PredictionResult[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [requestId, setRequestId] = useState<string | null>(null)
  const [processingTime, setProcessingTime] = useState<number | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [batchFile, setBatchFile] = useState<string | null>(null)
  const [batchInstances, setBatchInstances] = useState<Record<string, unknown>[]>([])
  const { addPredictions } = usePredictionStore()
  const [_lastInstances, setLastInstances] = useState<Record<string, unknown>[]>([])

  const handleFieldChange = (key: string, value: string) => {
    setFormData((prev) => ({
      ...prev,
      [key]: value === '' ? null : isNaN(Number(value)) ? value : Number(value),
    }))
  }

  const handleRandomFill = () => {
    const rand = (min: number, max: number) => Math.random() * (max - min) + min
    const round = (v: number, d: number) => Number(v.toFixed(d))

    // Generate all 7 PEDE indicators (realistic 2-9 range)
    // to compute consistent media/std derived features
    const all7 = {
      iaa: round(rand(2, 9), 1),
      ian: round(rand(2, 9), 1),
      ida: round(rand(2, 9), 1),
      ieg: round(rand(2, 9), 1),
      ipp: round(rand(2, 9), 1),
      ips: round(rand(2, 9), 1),
      ipv: round(rand(2, 9), 1),
    }

    const vals = Object.values(all7)
    const mean = vals.reduce((a, b) => a + b, 0) / vals.length
    const std = Math.sqrt(vals.reduce((s, v) => s + (v - mean) ** 2, 0) / vals.length)

    setFormData({
      ian_2023: all7.ian,
      ida_2023: all7.ida,
      ipp_2023: all7.ipp,
      ips_2023: all7.ips,
      idade_2023: Math.floor(rand(7, 19)),
      delta_iaa_2022_2023: round(rand(-3, 3), 1),
      delta_ian_2022_2023: round(rand(-3, 3), 1),
      delta_ieg_2022_2023: round(rand(-3, 3), 1),
      delta_ipv_2022_2023: round(rand(-3, 3), 1),
      media_indicadores: round(mean, 2),
      std_indicadores: round(std, 2),
    })
  }

  const handleAutoFillDerived = () => {
    const indicators = ['iaa_2023', 'ian_2023', 'ida_2023', 'ieg_2023', 'ipp_2023', 'ips_2023', 'ipv_2023']
    const values = indicators
      .map((k) => formData[k])
      .filter((v): v is number => typeof v === 'number')

    if (values.length === 0) return

    const mean = values.reduce((a, b) => a + b, 0) / values.length
    const min = Math.min(...values)
    const max = Math.max(...values)
    const std = Math.sqrt(values.reduce((sum, v) => sum + (v - mean) ** 2, 0) / values.length)

    setFormData((prev) => ({
      ...prev,
      media_indicadores: Number(mean.toFixed(4)),
      min_indicador: Number(min.toFixed(4)),
      max_indicador: Number(max.toFixed(4)),
      std_indicadores: Number(std.toFixed(4)),
      range_indicadores: Number((max - min).toFixed(4)),
    }))
  }

  const handleSinglePredict = async () => {
    setLoading(true)
    setError(null)
    setPredictions([])

    try {
      const instance: Record<string, unknown> = {}
      Object.entries(formData).forEach(([k, v]) => {
        if (v !== null && v !== undefined && v !== '') {
          instance[k] = v
        }
      })

      const instances = [instance]
      const response = await api.predict({ instances })
      setPredictions(response.predictions)
      setRequestId(response.request_id)
      setProcessingTime(response.processing_time_ms)
      setLastInstances(instances)
      // Persist to store
      addPredictions(response.predictions, instances, response.request_id)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao realizar predição')
    } finally {
      setLoading(false)
    }
  }

  const handleFileUpload = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setBatchFile(file.name)
    const reader = new FileReader()
    reader.onload = (event) => {
      const text = event.target?.result as string
      const instances = parseCSV(text)
      setBatchInstances(instances)
    }
    reader.readAsText(file)
  }, [])

  const handleBatchPredict = async () => {
    if (batchInstances.length === 0) return

    setLoading(true)
    setError(null)
    setPredictions([])

    try {
      const response = await api.predict({ instances: batchInstances })
      setPredictions(response.predictions)
      setRequestId(response.request_id)
      setProcessingTime(response.processing_time_ms)
      setLastInstances(batchInstances)
      // Persist to store
      addPredictions(response.predictions, batchInstances, response.request_id)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao realizar predição em batch')
    } finally {
      setLoading(false)
    }
  }

  const handleExportResults = () => {
    if (predictions.length === 0) return

    const csv = [
      'risk_score,risk_label,risk_level,model_version',
      ...predictions.map(
        (p) =>
          `${p.risk_score},${p.risk_label},${getRiskLabel(getRiskLevel(p.risk_score))},${p.model_version}`,
      ),
    ].join('\n')

    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `predictions_${new Date().toISOString().slice(0, 10)}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  const groupIcon = (group: string) => {
    switch (group) {
      case 'performance': return <BookOpen className="h-4 w-4" />
      case 'demographic': return <UsersIcon className="h-4 w-4" />
      case 'temporal': return <TrendingUp className="h-4 w-4" />
      case 'derived': return <Calculator className="h-4 w-4" />
      default: return null
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-1">
        <h1 className="text-2xl font-bold tracking-tight">Predição de Risco</h1>
        <p className="text-muted-foreground text-sm">
          Avalie o risco de defasagem escolar para um aluno ou um grupo de alunos
        </p>
      </div>

      <Tabs defaultValue="single" value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="w-full sm:w-auto">
          <TabsTrigger value="single">
            <Brain className="h-4 w-4 mr-1.5" /> Aluno Individual
          </TabsTrigger>
          <TabsTrigger value="batch">
            <FileSpreadsheet className="h-4 w-4 mr-1.5" /> Batch (CSV)
          </TabsTrigger>
          <TabsTrigger value="rules">
            <BookOpen className="h-4 w-4 mr-1.5" /> Regras de Negócio
          </TabsTrigger>
        </TabsList>

        {/* Single prediction */}
        <TabsContent value="single">
          <div className="grid gap-6 lg:grid-cols-3">
            {/* Form */}
            <div className="lg:col-span-2 space-y-6">
              {(Object.keys(FEATURE_GROUPS) as Array<keyof typeof FEATURE_GROUPS>).map(
                (groupKey) => {
                  const group = FEATURE_GROUPS[groupKey]
                  const features = FEATURE_METADATA.filter((f) => f.group === groupKey)

                  return (
                    <Card key={groupKey}>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-base flex items-center gap-2">
                          {groupIcon(groupKey)}
                          {group.label}
                        </CardTitle>
                        <CardDescription>{group.description}</CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
                          {features.map((feat) => (
                            <div key={feat.key} className="space-y-1.5">
                              <Label htmlFor={feat.key} className="text-xs">
                                {feat.label}
                              </Label>
                              {feat.type === 'select' && feat.options ? (
                                <Select
                                  id={feat.key}
                                  value={String(formData[feat.key] ?? '')}
                                  onChange={(e) => handleFieldChange(feat.key, e.target.value)}
                                >
                                  <option value="">Selecione...</option>
                                  {feat.options.map((opt) => (
                                    <option key={opt.value} value={opt.value}>
                                      {opt.label}
                                    </option>
                                  ))}
                                </Select>
                              ) : (
                                <Input
                                  id={feat.key}
                                  type="number"
                                  step={feat.step}
                                  min={feat.min}
                                  max={feat.max}
                                  placeholder={feat.description}
                                  value={formData[feat.key] ?? ''}
                                  onChange={(e) => handleFieldChange(feat.key, e.target.value)}
                                />
                              )}
                            </div>
                          ))}
                        </div>
                        {groupKey === 'derived' && (
                          <Button
                            variant="outline"
                            size="sm"
                            className="mt-4"
                            onClick={handleAutoFillDerived}
                          >
                            <Calculator className="h-3.5 w-3.5 mr-1.5" />
                            Calcular Automaticamente
                          </Button>
                        )}
                      </CardContent>
                    </Card>
                  )
                },
              )}

              <div className="flex flex-wrap gap-3">
                <Button
                  onClick={handleSinglePredict}
                  disabled={loading}
                  className="w-full sm:w-auto"
                  size="lg"
                >
                  {loading ? (
                    <Loader2 className="h-4 w-4 animate-spin mr-2" />
                  ) : (
                    <Brain className="h-4 w-4 mr-2" />
                  )}
                  Avaliar Risco
                </Button>
                <Button
                  variant="outline"
                  onClick={handleRandomFill}
                  disabled={loading}
                  className="w-full sm:w-auto"
                  size="lg"
                >
                  <Dices className="h-4 w-4 mr-2" />
                  Preencher Aleatório
                </Button>
              </div>
            </div>

            {/* Results sidebar */}
            <div className="space-y-4">
              <Card className="sticky top-4">
                <CardHeader>
                  <CardTitle className="text-base">Resultado</CardTitle>
                </CardHeader>
                <CardContent>
                  {error && (
                    <div className="flex items-center gap-2 text-destructive mb-4">
                      <AlertCircle className="h-4 w-4" />
                      <p className="text-sm">{error}</p>
                    </div>
                  )}

                  {predictions.length > 0 ? (
                    <div className="space-y-4">
                      <RiskGauge score={predictions[0].risk_score} size="lg" />
                      <div className="text-center">
                        <Badge
                          className={getRiskBgClass(
                            getRiskLevel(predictions[0].risk_score),
                          )}
                        >
                          {getRiskLabel(getRiskLevel(predictions[0].risk_score))}
                        </Badge>
                      </div>
                      <Separator />
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Score</span>
                          <span className="font-mono font-medium">
                            {formatPercentage(predictions[0].risk_score)}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Label</span>
                          <span className="font-medium">
                            {predictions[0].risk_label === 1 ? 'Em Risco' : 'Ok'}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Modelo</span>
                          <span className="font-mono text-xs">
                            {predictions[0].model_version}
                          </span>
                        </div>
                        {processingTime && (
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Tempo</span>
                            <span className="font-mono text-xs">
                              {processingTime.toFixed(1)}ms
                            </span>
                          </div>
                        )}
                        {requestId && (
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Request</span>
                            <span className="font-mono text-[10px] truncate max-w-[120px]">
                              {requestId}
                            </span>
                          </div>
                        )}
                      </div>

                      {predictions[0].risk_score >= 0.7 && (
                        <div className="mt-4 p-3 rounded-lg bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-800">
                          <p className="text-xs text-red-700 dark:text-red-400 font-medium flex items-center gap-1.5">
                            <AlertCircle className="h-3.5 w-3.5" />
                            Ação Recomendada
                          </p>
                          <p className="text-xs text-red-600 dark:text-red-500 mt-1">
                            Aluno deve ser priorizado para programas de reforço, mentoria
                            intensiva e acompanhamento familiar.
                          </p>
                        </div>
                      )}

                      {/* Explanation section */}
                      <div className="mt-4 p-3 rounded-lg bg-muted/50 border">
                        <p className="text-xs font-medium flex items-center gap-1.5 mb-2">
                          <Lightbulb className="h-3.5 w-3.5 text-amber-500" />
                          Por que este resultado?
                        </p>
                        <div className="text-xs text-muted-foreground space-y-1">
                          {(() => {
                            const score = predictions[0].risk_score
                            const level = getRiskLevel(score)
                            const factors: string[] = []
                            const feat = formData

                            if (typeof feat.ian_2023 === 'number' && feat.ian_2023 < 5) {
                              factors.push(`IAN baixo (${feat.ian_2023}) indica defasagem na adequação de nível`)
                            }
                            if (typeof feat.ieg_2023 === 'number' && feat.ieg_2023 < 5) {
                              factors.push(`IEG baixo (${feat.ieg_2023}) indica baixo engajamento`)
                            }
                            if (typeof feat.ida_2023 === 'number' && feat.ida_2023 < 5) {
                              factors.push(`IDA baixo (${feat.ida_2023}) indica fraco desempenho acadêmico`)
                            }
                            if (typeof feat.ipv_2023 === 'number' && feat.ipv_2023 < 5) {
                              factors.push(`IPV baixo (${feat.ipv_2023}) indica distância do ponto de virada`)
                            }
                            if (typeof feat.iaa_2023 === 'number' && feat.iaa_2023 < 5) {
                              factors.push(`IAA baixo (${feat.iaa_2023}) indica autoavaliação desfavorável`)
                            }

                            if (factors.length === 0) {
                              if (level === 'high') {
                                factors.push('Combinação dos indicadores sugere alto risco de defasagem')
                              } else if (level === 'medium') {
                                factors.push('Alguns indicadores sugerem atenção moderada')
                              } else {
                                factors.push('Indicadores gerais sugerem baixo risco')
                              }
                            }

                            return (
                              <>
                                {factors.slice(0, 3).map((f, i) => (
                                  <p key={i}>• {f}</p>
                                ))}
                                <p className="mt-2 italic">
                                  Um score de {formatPercentage(score)} significa{' '}
                                  {level === 'high' ? 'alta probabilidade de defasagem escolar. A Passos Mágicos recomenda acompanhamento individualizado.' :
                                   level === 'medium' ? 'risco moderado que requer monitoramento contínuo.' :
                                   'baixa probabilidade de defasagem. Manter acompanhamento regular.'}
                                </p>
                              </>
                            )
                          })()}
                        </div>
                      </div>

                      {/* SHAP-like waterfall */}
                      <div className="mt-4 p-3 rounded-lg bg-muted/50 border">
                        <p className="text-xs font-medium flex items-center gap-1.5 mb-3">
                          <Calculator className="h-3.5 w-3.5 text-primary" />
                          Contribuição dos Indicadores
                          <InfoTooltip content="Mostra quanto cada indicador contribuiu para aumentar (vermelho) ou diminuir (verde) o score de risco final. Baseado em análise SHAP simplificada." />
                        </p>
                        <ShapWaterfall features={formData} riskScore={predictions[0].risk_score} />
                      </div>

                      {/* Radar profile */}
                      {(() => {
                        const indicators = ['iaa_2023', 'ian_2023', 'ida_2023', 'ieg_2023', 'ipp_2023', 'ips_2023', 'ipv_2023']
                        const hasIndicators = indicators.some(k => typeof formData[k] === 'number')
                        if (!hasIndicators) return null
                        const radarData = indicators.map(k => ({
                          indicator: k.replace('_2023', '').toUpperCase(),
                          'Este Aluno': typeof formData[k] === 'number' ? Number(formData[k]) : 0,
                          'Média PM': 5.5,
                        }))
                        return (
                          <div className="mt-4 p-3 rounded-lg bg-muted/50 border">
                            <p className="text-xs font-medium flex items-center gap-1.5 mb-3">
                              <BookOpen className="h-3.5 w-3.5 text-primary" />
                              Perfil do Aluno vs Média PM
                              <InfoTooltip content="Radar comparando os indicadores deste aluno com a média geral da Passos Mágicos. Valores mais próximos do centro indicam pior desempenho." />
                            </p>
                            <RadarProfile data={radarData} keys={['Este Aluno', 'Média PM']} maxValue={10} height={260} />
                          </div>
                        )
                      })()}
                    </div>
                  ) : (
                    <div className="text-center py-8 text-muted-foreground">
                      <Brain className="h-12 w-12 mx-auto mb-3 opacity-20" />
                      <p className="text-sm">
                        Preencha os dados do aluno e clique em "Avaliar Risco"
                      </p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </div>
        </TabsContent>

        {/* Batch prediction */}
        <TabsContent value="batch">
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Upload className="h-4 w-4" />
                  Upload de Arquivo CSV
                </CardTitle>
                <CardDescription>
                  Faça upload de um arquivo CSV com os dados dos alunos. O arquivo deve
                  conter colunas correspondentes às features do modelo.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div
                    className="border-2 border-dashed rounded-lg p-8 text-center cursor-pointer hover:border-primary/50 transition-colors"
                    onClick={() => fileInputRef.current?.click()}
                  >
                    <Upload className="h-8 w-8 mx-auto mb-3 text-muted-foreground" />
                    <p className="text-sm font-medium">
                      Clique para selecionar ou arraste um arquivo CSV
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">
                      Máximo: 1000 instâncias por arquivo
                    </p>
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept=".csv"
                      className="hidden"
                      onChange={handleFileUpload}
                    />
                  </div>

                  {batchFile && (
                    <div className="flex items-center gap-3 p-3 rounded-lg bg-muted">
                      <FileSpreadsheet className="h-5 w-5 text-primary" />
                      <div>
                        <p className="text-sm font-medium">{batchFile}</p>
                        <p className="text-xs text-muted-foreground">
                          {batchInstances.length} instâncias carregadas
                        </p>
                      </div>
                      <CheckCircle2 className="h-4 w-4 text-green-500 ml-auto" />
                    </div>
                  )}

                  <div className="flex gap-3">
                    <Button
                      onClick={handleBatchPredict}
                      disabled={loading || batchInstances.length === 0}
                    >
                      {loading ? (
                        <Loader2 className="h-4 w-4 animate-spin mr-2" />
                      ) : (
                        <Brain className="h-4 w-4 mr-2" />
                      )}
                      Processar {batchInstances.length} Alunos
                    </Button>
                    {predictions.length > 0 && (
                      <Button variant="outline" onClick={handleExportResults}>
                        <Download className="h-4 w-4 mr-2" />
                        Exportar Resultados
                      </Button>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>

            {error && (
              <div className="flex items-center gap-2 text-destructive p-4 border border-destructive/20 rounded-lg">
                <AlertCircle className="h-4 w-4" />
                <p className="text-sm">{error}</p>
              </div>
            )}

            {/* Batch results */}
            {predictions.length > 0 && (
              <>
                {/* Summary stats */}
                <div className="grid gap-4 grid-cols-1 sm:grid-cols-4">
                  <Card>
                    <CardContent className="p-4 text-center">
                      <p className="text-2xl font-bold">{predictions.length}</p>
                      <p className="text-xs text-muted-foreground">Total Avaliados</p>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="p-4 text-center">
                      <p className="text-2xl font-bold text-red-500">
                        {predictions.filter((p) => getRiskLevel(p.risk_score) === 'high').length}
                      </p>
                      <p className="text-xs text-muted-foreground">Alto Risco</p>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="p-4 text-center">
                      <p className="text-2xl font-bold text-amber-500">
                        {predictions.filter((p) => getRiskLevel(p.risk_score) === 'medium').length}
                      </p>
                      <p className="text-xs text-muted-foreground">Risco Moderado</p>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="p-4 text-center">
                      <p className="text-2xl font-bold text-green-500">
                        {predictions.filter((p) => getRiskLevel(p.risk_score) === 'low').length}
                      </p>
                      <p className="text-xs text-muted-foreground">Baixo Risco</p>
                    </CardContent>
                  </Card>
                </div>

                {/* Distribution chart */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Distribuição dos Scores</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ScoreDistribution predictions={predictions} height={300} />
                  </CardContent>
                </Card>

                {/* Results table */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Resultados Detalhados</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="border-b">
                            <th className="text-left py-2 px-3 font-medium">#</th>
                            <th className="text-left py-2 px-3 font-medium">Score</th>
                            <th className="text-left py-2 px-3 font-medium">Risco</th>
                            <th className="text-left py-2 px-3 font-medium">Label</th>
                            <th className="text-left py-2 px-3 font-medium">Modelo</th>
                          </tr>
                        </thead>
                        <tbody>
                          {predictions.map((p, i) => {
                            const level = getRiskLevel(p.risk_score)
                            return (
                              <tr key={i} className="border-b last:border-0 hover:bg-muted/50">
                                <td className="py-2 px-3 text-muted-foreground">{i + 1}</td>
                                <td className="py-2 px-3 font-mono">
                                  {formatPercentage(p.risk_score)}
                                </td>
                                <td className="py-2 px-3">
                                  <Badge className={getRiskBgClass(level)}>
                                    {getRiskLabel(level)}
                                  </Badge>
                                </td>
                                <td className="py-2 px-3">
                                  {p.risk_label === 1 ? 'Em Risco' : 'Ok'}
                                </td>
                                <td className="py-2 px-3 text-xs font-mono text-muted-foreground">
                                  {p.model_version}
                                </td>
                              </tr>
                            )
                          })}
                        </tbody>
                      </table>
                    </div>
                  </CardContent>
                </Card>
              </>
            )}
          </div>
        </TabsContent>

        {/* Business Rules */}
        <TabsContent value="rules">
          <BusinessRulesCard />
        </TabsContent>
      </Tabs>
    </div>
  )
}
