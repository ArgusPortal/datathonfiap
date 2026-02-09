import { useState, useMemo, useCallback } from 'react'
import {
  Users,
  Search,
  Filter,
  ArrowUpDown,
  AlertTriangle,
  CheckCircle2,
  AlertCircle,
  Download,
  Trash2,
  Info,
  Gem,
  Radar,
} from 'lucide-react'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Input,
  Button,
  Badge,
  Select,
  Separator,
} from '@/components/ui'
import { RiskGauge } from '@/components/charts/RiskGauge'
import { RadarProfile } from '@/components/charts/RadarProfile'
import { InfoTooltip } from '@/components/shared/InfoTooltip'
import type { StudentPrediction, RiskLevel } from '@/types'
import {
  getRiskBgClass,
  getRiskLabel,
  formatPercentage,
  getPedraBgClass,
} from '@/lib/utils'
import { usePredictionStore } from '@/stores/predictionStore'

function riskIcon(level: RiskLevel) {
  switch (level) {
    case 'high':
      return <AlertTriangle className="h-3.5 w-3.5" />
    case 'medium':
      return <AlertCircle className="h-3.5 w-3.5" />
    case 'low':
      return <CheckCircle2 className="h-3.5 w-3.5" />
  }
}

export function StudentsPage() {
  const { predictions, clearPredictions } = usePredictionStore()

  const [search, setSearch] = useState('')
  const [riskFilter, setRiskFilter] = useState<RiskLevel | 'all'>('all')
  const [phaseFilter, setPhaseFilter] = useState<string>('all')
  const [sortBy, setSortBy] = useState<'score' | 'date'>('score')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc')
  const [selectedStudent, setSelectedStudent] = useState<StudentPrediction | null>(null)

  const filtered = useMemo(() => {
    let result = [...predictions]

    if (search) {
      const q = search.toLowerCase()
      result = result.filter(
        (s) =>
          s.id.toLowerCase().includes(q) ||
          s.features.fase_2023?.toString().includes(q) ||
          s.features.instituicao_2023?.toString().includes(q),
      )
    }

    if (riskFilter !== 'all') {
      result = result.filter((s) => s.risk_level === riskFilter)
    }

    if (phaseFilter !== 'all') {
      result = result.filter((s) => String(s.features.fase_2023) === phaseFilter)
    }

    result.sort((a, b) => {
      const mul = sortDir === 'asc' ? 1 : -1
      if (sortBy === 'score') return (a.risk_score - b.risk_score) * mul
      return (new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()) * mul
    })

    return result
  }, [predictions, search, riskFilter, phaseFilter, sortBy, sortDir])

  const stats = useMemo(() => {
    if (predictions.length === 0) return { high: 0, medium: 0, low: 0, avg: 0, total: 0 }
    const high = predictions.filter((s) => s.risk_level === 'high').length
    const medium = predictions.filter((s) => s.risk_level === 'medium').length
    const low = predictions.filter((s) => s.risk_level === 'low').length
    const avg = predictions.reduce((sum, s) => sum + s.risk_score, 0) / predictions.length
    return { high, medium, low, avg, total: predictions.length }
  }, [predictions])

  const phases = useMemo(() => {
    const set = new Set<string>()
    predictions.forEach((p) => {
      const f = p.features.fase_2023
      if (f != null) set.add(String(f))
    })
    return Array.from(set).sort()
  }, [predictions])

  const handleExportCSV = useCallback(() => {
    if (predictions.length === 0) return

    const headers = [
      'id',
      'timestamp',
      'risk_score',
      'risk_label',
      'risk_level',
      'pedra',
      'model_version',
      'fase_2023',
      'idade_2023',
      'instituicao_2023',
      'iaa_2023',
      'ian_2023',
      'ida_2023',
      'ieg_2023',
      'ipp_2023',
      'ips_2023',
      'ipv_2023',
    ]

    const rows = filtered.map((s) =>
      [
        s.id,
        s.timestamp,
        s.risk_score,
        s.risk_label,
        s.risk_level,
        s.pedra ?? '',
        s.model_version,
        s.features.fase_2023 ?? '',
        s.features.idade_2023 ?? '',
        s.features.instituicao_2023 ?? '',
        s.features.iaa_2023 ?? '',
        s.features.ian_2023 ?? '',
        s.features.ida_2023 ?? '',
        s.features.ieg_2023 ?? '',
        s.features.ipp_2023 ?? '',
        s.features.ips_2023 ?? '',
        s.features.ipv_2023 ?? '',
      ].join(','),
    )

    const csv = [headers.join(','), ...rows].join('\n')
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `alunos_predicoes_${new Date().toISOString().slice(0, 10)}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }, [predictions, filtered])

  const handleClear = useCallback(() => {
    if (window.confirm('Tem certeza que deseja limpar todas as predições? Esta ação não pode ser desfeita.')) {
      clearPredictions()
      setSelectedStudent(null)
    }
  }, [clearPredictions])

  // Empty state
  if (predictions.length === 0) {
    return (
      <div className="space-y-6">
        <div className="flex flex-col gap-1">
          <h1 className="text-2xl font-bold tracking-tight">Alunos Avaliados</h1>
          <p className="text-muted-foreground text-sm">
            Histórico de predições e acompanhamento de risco dos alunos
          </p>
        </div>
        <Card>
          <CardContent className="p-12 text-center">
            <Info className="h-16 w-16 mx-auto mb-4 text-muted-foreground opacity-30" />
            <h2 className="text-lg font-semibold mb-2">Nenhuma predição realizada ainda</h2>
            <p className="text-sm text-muted-foreground max-w-md mx-auto">
              Nenhuma predição realizada ainda. Vá para a página de Predição para avaliar alunos.
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex flex-col gap-1">
          <h1 className="text-2xl font-bold tracking-tight">Alunos Avaliados</h1>
          <p className="text-muted-foreground text-sm">
            Histórico de predições e acompanhamento de risco dos alunos
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={handleExportCSV}>
            <Download className="h-3.5 w-3.5 mr-1.5" />
            Exportar CSV
          </Button>
          <Button variant="outline" size="sm" onClick={handleClear} className="text-red-600 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-950/20">
            <Trash2 className="h-3.5 w-3.5 mr-1.5" />
            Limpar Tudo
          </Button>
        </div>
      </div>

      {/* Summary */}
      <div className="grid gap-4 grid-cols-2 sm:grid-cols-5">
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-xl font-bold">{stats.total}</p>
            <p className="text-xs text-muted-foreground">Total</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-xl font-bold text-red-500">{stats.high}</p>
            <p className="text-xs text-muted-foreground">Alto Risco</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-xl font-bold text-amber-500">{stats.medium}</p>
            <p className="text-xs text-muted-foreground">Moderado</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-xl font-bold text-green-500">{stats.low}</p>
            <p className="text-xs text-muted-foreground">Baixo Risco</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-xl font-bold">{formatPercentage(stats.avg)}</p>
            <p className="text-xs text-muted-foreground">Score Médio</p>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-wrap gap-3 items-center">
            <div className="relative flex-1 min-w-[200px]">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Buscar por ID..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9"
              />
            </div>
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-muted-foreground" />
              <Select
                value={riskFilter}
                onChange={(e) => setRiskFilter(e.target.value as RiskLevel | 'all')}
                className="w-[140px]"
              >
                <option value="all">Todos os Riscos</option>
                <option value="high">Alto Risco</option>
                <option value="medium">Moderado</option>
                <option value="low">Baixo Risco</option>
              </Select>
              <Select
                value={phaseFilter}
                onChange={(e) => setPhaseFilter(e.target.value)}
                className="w-[120px]"
              >
                <option value="all">Todas Fases</option>
                {phases.map((p) => (
                  <option key={p} value={p}>Fase {p}</option>
                ))}
              </Select>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setSortDir(sortDir === 'asc' ? 'desc' : 'asc')}
            >
              <ArrowUpDown className="h-3.5 w-3.5 mr-1.5" />
              {sortBy === 'score' ? 'Score' : 'Data'}{' '}
              {sortDir === 'desc' ? '↓' : '↑'}
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSortBy(sortBy === 'score' ? 'date' : 'score')}
            >
              Ordenar por: {sortBy === 'score' ? 'Score' : 'Data'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Students grid */}
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <div className="space-y-2">
            {filtered.length === 0 ? (
              <Card>
                <CardContent className="p-8 text-center">
                  <Users className="h-12 w-12 mx-auto mb-3 text-muted-foreground opacity-30" />
                  <p className="text-sm text-muted-foreground">
                    Nenhum aluno encontrado com os filtros selecionados
                  </p>
                </CardContent>
              </Card>
            ) : (
              filtered.map((student) => (
                <Card
                  key={student.id}
                  className={`cursor-pointer transition-all hover:shadow-md ${
                    selectedStudent?.id === student.id ? 'ring-2 ring-primary' : ''
                  }`}
                  onClick={() => setSelectedStudent(student)}
                >
                  <CardContent className="p-4">
                    <div className="flex items-center gap-4">
                      <RiskGauge score={student.risk_score} size="sm" showLabel={false} />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-sm font-mono font-medium truncate">
                            {student.id.slice(0, 16)}
                          </span>
                          <Badge className={getRiskBgClass(student.risk_level)}>
                            {riskIcon(student.risk_level)}
                            <span className="ml-1">{getRiskLabel(student.risk_level)}</span>
                          </Badge>
                          {student.pedra && (
                            <Badge className={getPedraBgClass(student.pedra)}>
                              <Gem className="h-3 w-3 mr-1" />
                              {student.pedra}
                            </Badge>
                          )}
                        </div>
                        <div className="flex gap-3 mt-1 text-xs text-muted-foreground">
                          <span>Fase {student.features.fase_2023 ?? '—'}</span>
                          <span>·</span>
                          <span>{student.features.idade_2023 ?? '—'} anos</span>
                          <span>·</span>
                          <span>Inst. {student.features.instituicao_2023 ?? '—'}</span>
                        </div>
                      </div>
                      <div className="text-right shrink-0">
                        <p className="text-lg font-bold font-mono">
                          {formatPercentage(student.risk_score)}
                        </p>
                        <p className="text-[10px] text-muted-foreground">
                          {new Date(student.timestamp).toLocaleDateString('pt-BR')}
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
          </div>
          <p className="mt-4 text-xs text-muted-foreground text-center">
            Mostrando {filtered.length} de {predictions.length} alunos
          </p>
        </div>

        {/* Detail panel */}
        <div>
          <Card className="sticky top-4">
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Radar className="h-4 w-4" />
                Detalhes do Aluno
              </CardTitle>
            </CardHeader>
            <CardContent>
              {selectedStudent ? (
                <div className="space-y-4">
                  <RiskGauge score={selectedStudent.risk_score} size="md" />
                  <div className="flex items-center justify-center gap-2">
                    <Badge className={getRiskBgClass(selectedStudent.risk_level)}>
                      {getRiskLabel(selectedStudent.risk_level)}
                    </Badge>
                    {selectedStudent.pedra && (
                      <Badge className={getPedraBgClass(selectedStudent.pedra)}>
                        <Gem className="h-3 w-3 mr-1" />
                        {selectedStudent.pedra}
                      </Badge>
                    )}
                  </div>

                  <Separator />

                  {/* Radar Profile */}
                  <div className="space-y-1">
                    <h4 className="font-semibold text-xs text-muted-foreground uppercase tracking-wide flex items-center gap-1">
                      Perfil de Indicadores
                      <InfoTooltip content="Radar comparando os indicadores deste aluno com a média geral dos alunos da Passos Mágicos. Valores de 0 a 10." />
                    </h4>
                    <RadarProfile
                      data={[
                        { indicator: 'IAA', 'Este Aluno': Number(selectedStudent.features.iaa_2023 ?? 0), 'Média PM': 5.5 },
                        { indicator: 'IAN', 'Este Aluno': Number(selectedStudent.features.ian_2023 ?? 0), 'Média PM': 5.5 },
                        { indicator: 'IDA', 'Este Aluno': Number(selectedStudent.features.ida_2023 ?? 0), 'Média PM': 5.5 },
                        { indicator: 'IEG', 'Este Aluno': Number(selectedStudent.features.ieg_2023 ?? 0), 'Média PM': 5.5 },
                        { indicator: 'IPP', 'Este Aluno': Number(selectedStudent.features.ipp_2023 ?? 0), 'Média PM': 5.5 },
                        { indicator: 'IPS', 'Este Aluno': Number(selectedStudent.features.ips_2023 ?? 0), 'Média PM': 5.5 },
                        { indicator: 'IPV', 'Este Aluno': Number(selectedStudent.features.ipv_2023 ?? 0), 'Média PM': 5.5 },
                      ]}
                      keys={['Este Aluno', 'Média PM']}
                      height={240}
                      maxValue={10}
                    />
                    <div className="flex items-center justify-center gap-4 text-[10px] text-muted-foreground">
                      <span className="flex items-center gap-1">
                        <span className="inline-block w-2.5 h-2.5 rounded-full" style={{ backgroundColor: '#1e3a5f' }} />
                        Este Aluno
                      </span>
                      <span className="flex items-center gap-1">
                        <span className="inline-block w-2.5 h-2.5 rounded-full" style={{ backgroundColor: '#f97316' }} />
                        Média PM
                      </span>
                    </div>
                  </div>

                  <Separator />

                  {/* Compact indicators list */}
                  <div className="space-y-2 text-sm">
                    <h4 className="font-semibold text-xs text-muted-foreground uppercase tracking-wide">
                      Valores dos Indicadores
                    </h4>
                    <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
                      {[
                        { label: 'IAA', key: 'iaa_2023' as const, description: 'Auto-Avaliação' },
                        { label: 'IAN', key: 'ian_2023' as const, description: 'Avaliação Nota' },
                        { label: 'IDA', key: 'ida_2023' as const, description: 'Desempenho Acadêmico' },
                        { label: 'IEG', key: 'ieg_2023' as const, description: 'Engajamento' },
                        { label: 'IPP', key: 'ipp_2023' as const, description: 'Psicopedagógico' },
                        { label: 'IPS', key: 'ips_2023' as const, description: 'Psicossocial' },
                        { label: 'IPV', key: 'ipv_2023' as const, description: 'Ponto de Virada' },
                      ].map(({ label, key, description }) => {
                        const value = selectedStudent.features[key] as number | null | undefined
                        return (
                          <div key={label} className="flex justify-between" title={description}>
                            <span className="text-muted-foreground">{label}</span>
                            <span className="font-mono font-medium">
                              {value != null ? value.toFixed(1) : '—'}
                            </span>
                          </div>
                        )
                      })}
                    </div>
                  </div>

                  <Separator />

                  <div className="space-y-1.5 text-xs">
                    <h4 className="font-semibold text-xs text-muted-foreground uppercase tracking-wide mb-2">
                      Dados Demográficos
                    </h4>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Fase</span>
                      <span>{selectedStudent.features.fase_2023 ?? '—'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Idade</span>
                      <span>{selectedStudent.features.idade_2023 ?? '—'} anos</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Instituição</span>
                      <span>{selectedStudent.features.instituicao_2023 ?? '—'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Classificação Pedra</span>
                      <span>
                        {selectedStudent.pedra ? (
                          <Badge className={`text-[10px] px-1.5 py-0 ${getPedraBgClass(selectedStudent.pedra)}`}>
                            {selectedStudent.pedra}
                          </Badge>
                        ) : (
                          '—'
                        )}
                      </span>
                    </div>
                  </div>

                  <Separator />

                  <div className="space-y-1.5 text-xs">
                    <h4 className="font-semibold text-xs text-muted-foreground uppercase tracking-wide mb-2">
                      Predição
                    </h4>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Score de Risco</span>
                      <span className="font-mono font-medium">
                        {formatPercentage(selectedStudent.risk_score)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Modelo</span>
                      <span className="font-mono">{selectedStudent.model_version}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Avaliado em</span>
                      <span>
                        {new Date(selectedStudent.timestamp).toLocaleString('pt-BR')}
                      </span>
                    </div>
                  </div>

                  {selectedStudent.risk_level === 'high' && (
                    <>
                      <Separator />
                      <div className="p-3 rounded-lg bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-800">
                        <p className="text-xs text-red-700 dark:text-red-400 font-medium flex items-center gap-1">
                          <AlertTriangle className="h-3.5 w-3.5" />
                          Ação Recomendada
                        </p>
                        <p className="text-xs text-red-600 dark:text-red-500 mt-1">
                          Priorizar para reforço escolar e acompanhamento familiar.
                        </p>
                      </div>
                    </>
                  )}
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  <Users className="h-12 w-12 mx-auto mb-3 opacity-20" />
                  <p className="text-sm">Selecione um aluno para ver os detalhes</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
