import { lazy, Suspense } from 'react'
import { Routes, Route, useLocation } from 'react-router-dom'
import { Layout } from '@/components/layout/Layout'

const DashboardPage = lazy(() => import('@/pages/DashboardPage').then(m => ({ default: m.DashboardPage })))
const PredictPage = lazy(() => import('@/pages/PredictPage').then(m => ({ default: m.PredictPage })))
const StudentsPage = lazy(() => import('@/pages/StudentsPage').then(m => ({ default: m.StudentsPage })))
const AnalysisPage = lazy(() => import('@/pages/AnalysisPage').then(m => ({ default: m.AnalysisPage })))
const MonitoringPage = lazy(() => import('@/pages/MonitoringPage').then(m => ({ default: m.MonitoringPage })))
const ModelPage = lazy(() => import('@/pages/ModelPage').then(m => ({ default: m.ModelPage })))
const AboutPage = lazy(() => import('@/pages/AboutPage').then(m => ({ default: m.AboutPage })))

/** Themed page loader with PM shimmer skeletons */
function PageLoader() {
  return (
    <div className="space-y-6 p-6 animate-fade-in-up">
      {/* Hero skeleton */}
      <div className="rounded-xl hero-gradient p-8 space-y-3">
        <div className="h-6 w-48 rounded-md skeleton-shimmer" />
        <div className="h-4 w-96 max-w-full rounded-md skeleton-shimmer" />
        <div className="flex gap-2 mt-4">
          <div className="h-6 w-20 rounded-full skeleton-shimmer" />
          <div className="h-6 w-24 rounded-full skeleton-shimmer" />
        </div>
      </div>
      {/* Cards skeleton */}
      <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className={`rounded-xl border bg-card p-5 space-y-2 stagger-${i + 1} animate-fade-in-up`}>
            <div className="h-4 w-24 rounded skeleton-shimmer" />
            <div className="h-8 w-16 rounded skeleton-shimmer" />
            <div className="h-3 w-32 rounded skeleton-shimmer" />
          </div>
        ))}
      </div>
      {/* Content skeleton */}
      <div className="grid gap-6 grid-cols-1 lg:grid-cols-2">
        <div className="rounded-xl border bg-card p-6 space-y-3 stagger-5 animate-fade-in-up">
          <div className="h-5 w-40 rounded skeleton-shimmer" />
          <div className="h-48 w-full rounded-lg skeleton-shimmer" />
        </div>
        <div className="rounded-xl border bg-card p-6 space-y-3 stagger-6 animate-fade-in-up">
          <div className="h-5 w-40 rounded skeleton-shimmer" />
          <div className="h-48 w-full rounded-lg skeleton-shimmer" />
        </div>
      </div>
    </div>
  )
}

/** Wraps lazy pages with a fade-in animation on mount */
function AnimatedPage({ children }: { children: React.ReactNode }) {
  const location = useLocation()
  return (
    <div key={location.pathname} className="animate-fade-in-up">
      {children}
    </div>
  )
}

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Suspense fallback={<PageLoader />}><AnimatedPage><DashboardPage /></AnimatedPage></Suspense>} />
        <Route path="/predict" element={<Suspense fallback={<PageLoader />}><AnimatedPage><PredictPage /></AnimatedPage></Suspense>} />
        <Route path="/students" element={<Suspense fallback={<PageLoader />}><AnimatedPage><StudentsPage /></AnimatedPage></Suspense>} />
        <Route path="/analysis" element={<Suspense fallback={<PageLoader />}><AnimatedPage><AnalysisPage /></AnimatedPage></Suspense>} />
        <Route path="/monitoring" element={<Suspense fallback={<PageLoader />}><AnimatedPage><MonitoringPage /></AnimatedPage></Suspense>} />
        <Route path="/model" element={<Suspense fallback={<PageLoader />}><AnimatedPage><ModelPage /></AnimatedPage></Suspense>} />
        <Route path="/about" element={<Suspense fallback={<PageLoader />}><AnimatedPage><AboutPage /></AnimatedPage></Suspense>} />
      </Route>
    </Routes>
  )
}
