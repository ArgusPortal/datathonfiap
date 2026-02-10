import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard,
  Brain,
  Users,
  Activity,
  FileText,
  Moon,
  Sun,
  Shield,
  Menu,
  X,
  Keyboard,
  FlaskConical,
  Heart,
  Sparkles,
} from 'lucide-react'
import { useState, useCallback, useMemo, useRef } from 'react'
import { Button } from '@/components/ui'
import { useTheme, useKeyboardShortcuts, GLOBAL_SHORTCUTS } from '@/hooks'
import { cn } from '@/lib/utils'
import { GlossaryButton } from '@/components/shared/Glossary'
import { Footer } from '@/components/layout/Footer'

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard, shortcut: 'd' },
  { name: 'Predição', href: '/predict', icon: Brain, shortcut: 'p' },
  { name: 'Alunos', href: '/students', icon: Users, shortcut: 's' },
  { name: 'Análise', href: '/analysis', icon: FlaskConical, shortcut: 'a' },
  { name: 'Monitoramento', href: '/monitoring', icon: Activity, shortcut: 'm' },
  { name: 'Modelo', href: '/model', icon: FileText, shortcut: 'i' },
  { name: 'Sobre', href: '/about', icon: Heart, shortcut: 'o' },
]

export function Layout() {
  const { theme, toggleTheme } = useTheme()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [showShortcuts, setShowShortcuts] = useState(false)
  const navigate = useNavigate()
  const pendingGRef = useRef(false)

  // Two-key 'g' + letter navigation
  const handleGoKey = useCallback((key: string) => {
    const nav = navigation.find((n) => n.shortcut === key)
    if (nav) navigate(nav.href)
  }, [navigate])

  const shortcuts = useMemo(
    () => [
      { key: 'g', handler: () => { pendingGRef.current = true; setTimeout(() => { pendingGRef.current = false }, 1000) }, description: 'Go prefix' },
      ...navigation.map((n) => ({
        key: n.shortcut,
        handler: () => { if (pendingGRef.current) { handleGoKey(n.shortcut); pendingGRef.current = false } },
        description: `Go to ${n.name}`,
      })),
      { key: '?', shift: true, handler: () => setShowShortcuts((v) => !v), description: 'Show shortcuts' },
    ],
    [handleGoKey],
  )

  useKeyboardShortcuts(shortcuts)

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-50 w-64 bg-card border-r transform transition-transform duration-200 lg:translate-x-0 lg:static lg:z-0 flex flex-col',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full',
        )}
      >
        {/* Logo */}
        <div className="flex h-16 items-center gap-3 px-6 border-b">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary shadow-sm">
            <Sparkles className="h-5 w-5 text-white" />
          </div>
          <div className="flex flex-col">
            <span className="text-sm font-bold leading-tight text-foreground">Passos Mágicos</span>
            <span className="text-[10px] text-muted-foreground leading-tight">
              Predição de Risco v2.0
            </span>
          </div>
          <Button
            variant="ghost"
            size="icon"
            className="ml-auto lg:hidden"
            onClick={() => setSidebarOpen(false)}
          >
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {navigation.map((item) => (
            <NavLink
              key={item.href}
              to={item.href}
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) =>
                cn(
                  'group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-150',
                  isActive
                    ? 'bg-primary/10 text-primary shadow-sm border border-primary/10'
                    : 'text-muted-foreground hover:text-foreground hover:bg-accent',
                )
              }
            >
              {({ isActive }) => (
                <>
                  <div className={cn(
                    'flex h-7 w-7 items-center justify-center rounded-md transition-colors',
                    isActive ? 'bg-primary text-primary-foreground shadow-sm' : 'bg-muted group-hover:bg-accent',
                  )}>
                    <item.icon className="h-3.5 w-3.5" />
                  </div>
                  <span>{item.name}</span>
                  {isActive && (
                    <span className="ml-auto h-1.5 w-1.5 rounded-full bg-primary animate-pulse" />
                  )}
                </>
              )}
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        <div className="border-t p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-green-500 status-dot-active" />
              <span className="text-xs text-muted-foreground">API Online</span>
            </div>
            <div className="flex items-center gap-1">
              <Button variant="ghost" size="icon" onClick={toggleTheme} title={theme === 'dark' ? 'Modo Claro' : 'Modo Escuro'}>
                {theme === 'dark' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
              </Button>
            </div>
          </div>
          <div className="mt-3 text-[10px] text-muted-foreground flex items-center gap-1">
            <Shield className="h-3 w-3" />
            LGPD Compliant · v2.0.0
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top bar */}
        <header className="h-16 border-b bg-card flex items-center gap-4 px-4 lg:px-6">
          <Button
            variant="ghost"
            size="icon"
            className="lg:hidden"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu className="h-5 w-5" />
          </Button>
          <div className="flex-1" />
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <GlossaryButton />
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowShortcuts(true)}
              className="hidden sm:inline-flex gap-1"
              title="Atalhos de teclado (Shift+?)"
            >
              <Keyboard className="h-3.5 w-3.5" />
            </Button>
            <div className="hidden sm:flex items-center gap-1.5">
              <div className="h-1.5 w-1.5 rounded-full bg-green-500 status-dot-active" />
              Modelo <span className="font-mono font-semibold">v2.0.0</span>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto p-4 lg:p-6">
          <Outlet />
          <Footer />
        </main>
      </div>

      {/* Keyboard shortcuts modal */}
      {showShortcuts && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={() => setShowShortcuts(false)}>
          <div className="w-full max-w-sm mx-4 rounded-lg border bg-card p-6 shadow-lg" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-sm flex items-center gap-2">
                <Keyboard className="h-4 w-4 text-primary" />
                Atalhos de Teclado
              </h3>
              <Button variant="ghost" size="icon" onClick={() => setShowShortcuts(false)}>
                <X className="h-4 w-4" />
              </Button>
            </div>
            <div className="space-y-2">
              {GLOBAL_SHORTCUTS.map((s) => (
                <div key={s.key} className="flex items-center justify-between py-1">
                  <span className="text-xs text-muted-foreground">{s.description}</span>
                  <kbd className="px-2 py-0.5 text-[10px] font-mono bg-muted rounded border">{s.label}</kbd>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
