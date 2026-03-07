import { useState } from 'react'
import { BookOpen, X, Search } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle, Button } from '@/components/ui'

interface GlossaryEntry {
  term: string
  abbrev?: string
  definition: string
  category: 'indicador' | 'modelo' | 'metrica' | 'negocio'
}

const GLOSSARY_ENTRIES: GlossaryEntry[] = [
  // Indicadores
  { term: 'IAN', abbrev: 'IAN', definition: 'Indicador de Adequação de Nível — mede se o aluno está no nível escolar adequado para sua idade.', category: 'indicador' },
  { term: 'IEG', abbrev: 'IEG', definition: 'Indicador de Engajamento — avalia a participação e interesse do aluno nas atividades do programa.', category: 'indicador' },
  { term: 'IDA', abbrev: 'IDA', definition: 'Indicador de Desempenho Acadêmico — reflete as notas e performance escolar do aluno.', category: 'indicador' },
  { term: 'IPV', abbrev: 'IPV', definition: 'Indicador de Ponto de Virada — mede a proximidade do aluno de atingir uma transformação significativa.', category: 'indicador' },
  { term: 'IAA', abbrev: 'IAA', definition: 'Indicador de Autoavaliação — captura a autopercepção do aluno sobre seu desempenho.', category: 'indicador' },
  { term: 'IPP', abbrev: 'IPP', definition: 'Indicador Psicopedagógico — avalia aspectos psicopedagógicos do desenvolvimento do aluno.', category: 'indicador' },
  { term: 'IPS', abbrev: 'IPS', definition: 'Indicador Psicossocial — mede aspectos psicossociais e emocionais do aluno.', category: 'indicador' },
  { term: 'INDE', abbrev: 'INDE', definition: 'Índice de Desenvolvimento Educacional — indicador composto calculado com pesos: IAN×0.1 + IDA×0.2 + IEG×0.2 + IAA×0.1 + IPS×0.1 + IPP×0.1 + IPV×0.2.', category: 'indicador' },

  // Modelo
  { term: 'Score de Risco', definition: 'Probabilidade (0 a 1) de um aluno apresentar defasagem escolar no próximo período. Quanto maior, maior o risco.', category: 'modelo' },
  { term: 'Threshold', definition: 'Ponto de corte (0.3499) acima do qual o modelo classifica como "alto risco". Otimizado para maximizar recall.', category: 'modelo' },
  { term: 'Calibração', definition: 'Processo (sigmoid) que ajusta as probabilidades do modelo para serem mais próximas da realidade.', category: 'modelo' },
  { term: 'HistGradientBoosting', definition: 'Algoritmo de ensemble que constrói árvores de decisão sequencialmente, cada uma corrigindo os erros da anterior. Usa histogramas para acelerar o treino.', category: 'modelo' },
  { term: 'Feature', definition: 'Variável de entrada do modelo. Ex: IAN, IEG, idade, fase. São os dados usados para fazer a predição.', category: 'modelo' },

  // Métricas
  { term: 'Recall', definition: 'Proporção de alunos realmente em risco que foram corretamente identificados. Recall = TP / (TP + FN). Meta: ≥ 75%.', category: 'metrica' },
  { term: 'Precision', definition: 'Proporção de alertas de risco que são corretos. Precision = TP / (TP + FP). Mede a confiabilidade dos alertas.', category: 'metrica' },
  { term: 'F2-Score', definition: 'Média harmônica ponderada que dá 2× mais peso ao Recall do que à Precision. Métrica principal de seleção do modelo.', category: 'metrica' },
  { term: 'PR-AUC', definition: 'Área sob a curva Precision-Recall. Quanto mais perto de 1, melhor o modelo diferencia risco de não-risco.', category: 'metrica' },
  { term: 'Brier Score', definition: 'Mede quão calibradas são as probabilidades. Varia de 0 (perfeito) a 1 (péssimo). Menor é melhor.', category: 'metrica' },
  { term: 'PSI', definition: 'Population Stability Index — mede quanto a distribuição de uma feature mudou em relação ao baseline. < 0.1 estável, 0.1–0.25 atenção, > 0.25 drift significativo.', category: 'metrica' },
  { term: 'SLO', definition: 'Service Level Objective — meta de qualidade do serviço (ex: latência p95 ≤ 300ms, taxa de erro ≤ 1%).', category: 'metrica' },

  // Negócio
  { term: 'Pedra', definition: 'Classificação qualitativa do INDE: Quartzo (< 6.1), Ágata (6.1–7.2), Ametista (7.2–8.2), Topázio (8.2–10.0).', category: 'negocio' },
  { term: 'Defasagem', definition: 'Situação em que o aluno está atrasado em relação ao nível escolar esperado para sua idade.', category: 'negocio' },
  { term: 'Ponto de Virada', definition: 'Momento em que o aluno demonstra mudança significativa de comportamento e desempenho, sinalizando progresso sustentável.', category: 'negocio' },
  { term: 'Falso Negativo (FN)', definition: 'Aluno que ESTÁ em risco mas o modelo NÃO identificou. É o erro mais grave neste contexto — a criança não recebe atendimento.', category: 'negocio' },
  { term: 'Falso Positivo (FP)', definition: 'Aluno que NÃO está em risco mas recebeu alerta. Menos grave — gera trabalho extra mas não deixa ninguém sem atendimento.', category: 'negocio' },
]

const CATEGORY_LABELS: Record<string, string> = {
  indicador: 'Indicadores',
  modelo: 'Modelo',
  metrica: 'Métricas',
  negocio: 'Negócio',
}

const CATEGORY_COLORS: Record<string, string> = {
  indicador: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
  modelo: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400',
  metrica: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
  negocio: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400',
}

/**
 * Inline glossary tooltip — wrap any text to show a tooltip on hover.
 */
export function GlossaryTip({ term, children }: { term: string; children: React.ReactNode }) {
  const entry = GLOSSARY_ENTRIES.find(
    (e) => e.term.toLowerCase() === term.toLowerCase() || e.abbrev?.toLowerCase() === term.toLowerCase(),
  )
  if (!entry) return <>{children}</>

  return (
    <span className="relative group/tip inline-block">
      <span className="underline decoration-dotted decoration-muted-foreground/50 cursor-help">
        {children}
      </span>
      <span className="absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 p-3 rounded-lg border bg-popover text-popover-foreground shadow-lg text-xs opacity-0 pointer-events-none group-hover/tip:opacity-100 group-hover/tip:pointer-events-auto transition-opacity duration-200">
        <span className="font-semibold block mb-1">{entry.term}</span>
        <span className="text-muted-foreground leading-relaxed">{entry.definition}</span>
        <span className="absolute top-full left-1/2 -translate-x-1/2 -mt-1 border-4 border-transparent border-t-popover" />
      </span>
    </span>
  )
}

/**
 * Full glossary panel — a searchable, categorized list of all terms.
 */
export function GlossaryPanel({ onClose }: { onClose?: () => void }) {
  const [search, setSearch] = useState('')
  const [activeCategory, setActiveCategory] = useState<string | null>(null)

  const filtered = GLOSSARY_ENTRIES.filter((e) => {
    const matchSearch =
      search === '' ||
      e.term.toLowerCase().includes(search.toLowerCase()) ||
      e.definition.toLowerCase().includes(search.toLowerCase())
    const matchCategory = activeCategory === null || e.category === activeCategory
    return matchSearch && matchCategory
  })

  const categories = ['indicador', 'modelo', 'metrica', 'negocio'] as const

  return (
    <Card className="max-h-[80vh] flex flex-col">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <BookOpen className="h-5 w-5 text-primary" />
            Glossário
          </CardTitle>
          {onClose && (
            <Button variant="ghost" size="icon" onClick={onClose}>
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>
        {/* Search */}
        <div className="relative mt-2">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
          <input
            type="text"
            placeholder="Buscar termo..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full h-9 pl-9 pr-3 text-sm border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </div>
        {/* Category filters */}
        <div className="flex flex-wrap gap-1.5 mt-2">
          <div className="flex flex-wrap gap-1.5">
            <button
              onClick={() => setActiveCategory(null)}
              className={`px-2.5 py-1 rounded-full text-xs font-medium transition-colors ${
                activeCategory === null
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted text-muted-foreground hover:bg-muted/80'
              }`}
            >
              Todos ({GLOSSARY_ENTRIES.length})
            </button>
            {categories.map((cat) => {
              const count = GLOSSARY_ENTRIES.filter((e) => e.category === cat).length
              return (
                <button
                  key={cat}
                  onClick={() => setActiveCategory(activeCategory === cat ? null : cat)}
                  className={`px-2.5 py-1 rounded-full text-xs font-medium transition-colors ${
                    activeCategory === cat
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-muted text-muted-foreground hover:bg-muted/80'
                  }`}
                >
                  {CATEGORY_LABELS[cat]} ({count})
                </button>
              )
            })}
          </div>
        </div>
      </CardHeader>
      <CardContent className="overflow-y-auto flex-1 pt-0">
        <div className="space-y-2">
          {filtered.length === 0 ? (
            <p className="text-sm text-muted-foreground py-4 text-center">
              Nenhum termo encontrado.
            </p>
          ) : (
            filtered.map((entry) => (
              <div
                key={entry.term}
                className="p-3 rounded-lg border hover:bg-muted/30 transition-colors"
              >
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-semibold text-sm">{entry.term}</span>
                  {entry.abbrev && entry.abbrev !== entry.term && (
                    <span className="text-xs text-muted-foreground font-mono">({entry.abbrev})</span>
                  )}
                  <span
                    className={`px-1.5 py-0.5 rounded text-[10px] font-medium ml-auto ${CATEGORY_COLORS[entry.category]}`}
                  >
                    {CATEGORY_LABELS[entry.category]}
                  </span>
                </div>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  {entry.definition}
                </p>
              </div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  )
}

/**
 * Glossary button that opens glossary in a floating panel.
 */
export function GlossaryButton() {
  const [open, setOpen] = useState(false)

  return (
    <>
      <Button
        variant="outline"
        size="sm"
        onClick={() => setOpen(!open)}
        className="gap-1.5"
      >
        <BookOpen className="h-3.5 w-3.5" />
        Glossário
      </Button>
      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 animate-fade-in" onClick={() => setOpen(false)}>
          <div className="w-full max-w-xl mx-4 animate-scale-in" onClick={(e) => e.stopPropagation()}>
            <GlossaryPanel onClose={() => setOpen(false)} />
          </div>
        </div>
      )}
    </>
  )
}
