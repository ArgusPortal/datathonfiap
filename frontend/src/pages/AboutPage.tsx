/**
 * AboutPage.tsx — Sobre / Institucional
 *
 * Página dedicada à contextualização da Passos Mágicos,
 * ODS da ONU, arquitetura técnica e equipe do projeto.
 * Inspirada no site passosmagicos.org.br com storytelling.
 */
import {
  Heart,
  GraduationCap,
  Calendar,
  Users,
  Globe,
  Code2,
  Database,
  Server,
  Shield,
  BarChart3,
  Sparkles,
  ExternalLink,
  BookOpen,
  Target,
  Cpu,
} from 'lucide-react'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
  Badge,
} from '@/components/ui'
import { InfoTooltip } from '@/components/shared/InfoTooltip'
import { ODSList } from '@/components/shared/ODSBadge'
import { HeroSection } from '@/components/shared/HeroSection'

// ---------------------------------------------------------------------------
// Data
// ---------------------------------------------------------------------------

const TIMELINE = [
  { year: '1992', event: 'Fundação da Associação Passos Mágicos por Dimetri Ivanoff em Embu-Guaçu, SP.', icon: Heart },
  { year: '2016', event: 'Expansão do modelo de educação para mais de 1.000 alunos atendidos.', icon: Users },
  { year: '2020', event: 'Início da coleta de dados longitudinais padronizados (INDE, IAA, IEG, etc).', icon: Database },
  { year: '2025', event: 'Datathon FIAP — desenvolvimento do modelo preditivo de defasagem.', icon: BarChart3 },
  { year: '2026', event: 'Deploy do sistema fullstack com monitoramento MLOps e dashboard.', icon: Server },
]

const TECH_STACK = [
  { category: 'Backend', items: ['Python 3.11', 'FastAPI', 'scikit-learn', 'RandomForest + Calibração', 'Uvicorn'] },
  { category: 'Frontend', items: ['React 18', 'TypeScript 5', 'Vite 6', 'Tailwind CSS', 'Nivo.rocks', 'Radix UI'] },
  { category: 'MLOps', items: ['Drift Detection (PSI)', 'SLO Framework', 'Prometheus Metrics', 'Inference Logging'] },
  { category: 'Infra', items: ['Docker Multi-stage', 'Nginx', 'LGPD Compliance', 'Rate Limiting', 'CORS'] },
]

const ARCHITECTURE = [
  { label: 'Ingestão', desc: 'CSV → Preprocessing → Feature Engineering', icon: Database, color: 'text-passos-500' },
  { label: 'Treinamento', desc: 'StratifiedKFold → RandomForest → Calibração Sigmoid', icon: Cpu, color: 'text-magic-500' },
  { label: 'Servindo', desc: 'FastAPI → /predict → Score + Risco + SHAP', icon: Server, color: 'text-green-500' },
  { label: 'Monitoramento', desc: 'Drift PSI · SLO · Métricas · Audit Trail', icon: Target, color: 'text-amber-500' },
  { label: 'Interface', desc: 'React Dashboard → Nivo Charts → PDF Export', icon: BarChart3, color: 'text-red-500' },
]

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function AboutPage() {
  return (
    <div className="space-y-6">
      {/* HERO */}
      <HeroSection
        title="Sobre o Projeto"
        subtitle="Transformando dados educacionais em oportunidades — Tecnologia e Machine Learning a serviço da Associação Passos Mágicos."
        badge="Datathon FIAP 2026"
        compact
      />

      {/* ODS */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Globe className="h-4 w-4 text-primary" />
            <CardTitle>Objetivos de Desenvolvimento Sustentável (ODS)</CardTitle>
            <InfoTooltip content="Os 17 ODS da ONU são uma agenda global. A Passos Mágicos contribui diretamente com 5 deles." />
          </div>
          <CardDescription>
            A Passos Mágicos impacta 5 ODS da ONU, integrando educação, igualdade de gênero e redução da pobreza.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ODSList size="lg" />
        </CardContent>
      </Card>

      {/* ABOUT PM */}
      <div className="grid gap-6 grid-cols-1 lg:grid-cols-2">
        <Card className="card-hover">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Heart className="h-4 w-4 text-red-500" />
              <CardTitle>Associação Passos Mágicos</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground leading-relaxed">
              Fundada em 1992 em Embu-Guaçu (SP) por <strong>Dimetri Ivanoff</strong>,
              a Passos Mágicos transforma a vida de crianças e jovens em situação de
              vulnerabilidade social por meio da educação. Utilizando uma metodologia
              própria que vai além do reforço escolar, a ONG trabalha desenvolvimento
              emocional, cultural e social dos alunos.
            </p>
            <div className="mt-4 flex flex-wrap gap-2">
              <Badge variant="secondary" className="text-xs">📍 Embu-Guaçu, SP</Badge>
              <Badge variant="secondary" className="text-xs">📚 +1.000 alunos</Badge>
              <Badge variant="secondary" className="text-xs">🎓 30+ anos</Badge>
            </div>
            <a
              href="https://passosmagicos.org.br"
              target="_blank"
              rel="noopener noreferrer"
              className="mt-4 inline-flex items-center gap-1.5 text-xs text-primary hover:underline"
            >
              <ExternalLink className="h-3 w-3" />
              passosmagicos.org.br
            </a>
          </CardContent>
        </Card>

        <Card className="card-hover">
          <CardHeader>
            <div className="flex items-center gap-2">
              <BookOpen className="h-4 w-4 text-primary" />
              <CardTitle>Contexto do Projeto</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground leading-relaxed">
              Este sistema foi desenvolvido no contexto do <strong>Datathon FIAP 2026</strong>,
              com o objetivo de aplicar técnicas de Machine Learning para predizer o risco de
              <strong> defasagem escolar</strong> dos alunos da Passos Mágicos. A predição
              antecipada permite intervenção pedagógica precoce, otimizando recursos e
              maximizando impacto educacional.
            </p>
            <div className="mt-4 space-y-2">
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <Sparkles className="h-3.5 w-3.5 text-magic-500" />
                Modelo: RandomForestClassifier + CalibratedClassifierCV (scikit-learn)
              </div>
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <Target className="h-3.5 w-3.5 text-amber-500" />
                Target: em_risco_2024 (classificação binária, threshold 0.2814)
              </div>
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <Shield className="h-3.5 w-3.5 text-green-500" />
                Conformidade LGPD — dados sensíveis nunca armazenados
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* TIMELINE */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Calendar className="h-4 w-4 text-primary" />
            <CardTitle>Linha do Tempo</CardTitle>
          </div>
          <CardDescription>Da fundação da ONG ao deploy do modelo preditivo</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="relative">
            <div className="absolute left-5 top-0 bottom-0 w-0.5 bg-border" />
            <div className="space-y-6">
              {TIMELINE.map((t) => (
                <div key={t.year} className="relative flex gap-4 items-start">
                  <div className="relative z-10 flex h-10 w-10 shrink-0 items-center justify-center rounded-full border-2 border-primary bg-card">
                    <t.icon className="h-4 w-4 text-primary" />
                  </div>
                  <div>
                    <p className="text-sm font-bold text-primary">{t.year}</p>
                    <p className="text-sm text-muted-foreground">{t.event}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* ARCHITECTURE */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Code2 className="h-4 w-4 text-primary" />
            <CardTitle>Arquitetura do Sistema</CardTitle>
            <InfoTooltip content="Pipeline end-to-end: desde a ingestão dos dados CSV até a interface web. Totalmente containerizado via Docker." />
          </div>
          <CardDescription>Pipeline de ML em produção — 5 estágios</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-5">
            {ARCHITECTURE.map((a) => (
              <div key={a.label} className="flex flex-col items-center text-center p-4 rounded-lg border bg-card hover:border-primary/30 transition-colors">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-muted mb-3">
                  <a.icon className={`h-5 w-5 ${a.color}`} />
                </div>
                <p className="text-sm font-semibold mb-1">{a.label}</p>
                <p className="text-[11px] text-muted-foreground leading-relaxed">{a.desc}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* TECH STACK */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Cpu className="h-4 w-4 text-primary" />
            <CardTitle>Stack Tecnológico</CardTitle>
          </div>
          <CardDescription>Tecnologias utilizadas no desenvolvimento do sistema</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-4">
            {TECH_STACK.map((s) => (
              <div key={s.category} className="p-4 rounded-lg border bg-card">
                <h4 className="text-sm font-semibold mb-2">{s.category}</h4>
                <div className="flex flex-wrap gap-1.5">
                  {s.items.map((item) => (
                    <Badge key={item} variant="secondary" className="text-[10px]">{item}</Badge>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* CREDITS */}
      <Card className="border-passos-200/50 dark:border-passos-800/30">
        <CardContent className="p-5">
          <div className="flex items-center gap-3">
            <GraduationCap className="h-5 w-5 text-passos-500" />
            <div>
              <p className="text-sm font-semibold">Datathon FIAP 2026 — Passos Mágicos</p>
              <p className="text-xs text-muted-foreground">
                Projeto acadêmico desenvolvido como parte do programa de Pós-Graduação em Machine Learning Engineering da FIAP (MLET5).
                Todos os dados são tratados em conformidade com a LGPD.
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                Desenvolvido por: <strong>Argus Portal</strong>
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
