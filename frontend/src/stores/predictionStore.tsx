import { createContext, useContext, useCallback, useState, useEffect, type ReactNode } from 'react'
import type { StudentPrediction, StudentFeatures, PredictionResult, RiskLevel } from '@/types'
import { getRiskLevel, generateId } from '@/lib/utils'

// Business rules: classify students by Pedra based on INDE/indicators
function classifyPedra(features: StudentFeatures): string | undefined {
  const indicators = ['iaa_2023', 'ian_2023', 'ida_2023', 'ieg_2023', 'ipp_2023', 'ips_2023', 'ipv_2023'] as const
  const values = indicators
    .map((k) => features[k])
    .filter((v): v is number => typeof v === 'number' && !isNaN(v))

  if (values.length === 0) return undefined

  // Approximate INDE using available indicators with standard weights
  const weights: Record<string, number> = {
    ian_2023: 0.10,
    ida_2023: 0.20,
    ieg_2023: 0.20,
    iaa_2023: 0.10,
    ips_2023: 0.10,
    ipp_2023: 0.10,
    ipv_2023: 0.20,
  }

  let weightedSum = 0
  let totalWeight = 0
  for (const k of indicators) {
    const val = features[k]
    if (typeof val === 'number' && !isNaN(val)) {
      const w = weights[k] || 0.14
      weightedSum += val * w
      totalWeight += w
    }
  }

  if (totalWeight === 0) return undefined
  const inde = weightedSum / totalWeight

  if (inde < 3.0) return 'Quartzo'
  if (inde < 6.1) return 'Quartzo'
  if (inde < 7.2) return 'Ágata'
  if (inde < 8.2) return 'Ametista'
  return 'Topázio'
}

const STORAGE_KEY = 'passos-magicos-predictions'
const MAX_PREDICTIONS = 5000

function loadFromStorage(): StudentPrediction[] {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      return JSON.parse(stored)
    }
  } catch {
    // corrupted data
  }
  return []
}

function saveToStorage(predictions: StudentPrediction[]) {
  try {
    const trimmed = predictions.slice(-MAX_PREDICTIONS)
    localStorage.setItem(STORAGE_KEY, JSON.stringify(trimmed))
  } catch {
    // quota exceeded - trim more
    try {
      const trimmed = predictions.slice(-500)
      localStorage.setItem(STORAGE_KEY, JSON.stringify(trimmed))
    } catch {
      // give up
    }
  }
}

interface PredictionStore {
  predictions: StudentPrediction[]
  addPredictions: (
    results: PredictionResult[],
    instances: Record<string, unknown>[],
    requestId: string,
  ) => void
  clearPredictions: () => void
  getStudentHistory: (features: StudentFeatures) => StudentPrediction[]
}

const PredictionStoreContext = createContext<PredictionStore | null>(null)

export function PredictionStoreProvider({ children }: { children: ReactNode }) {
  const [predictions, setPredictions] = useState<StudentPrediction[]>(loadFromStorage)

  // Save to localStorage whenever predictions change
  useEffect(() => {
    saveToStorage(predictions)
  }, [predictions])

  const addPredictions = useCallback(
    (results: PredictionResult[], instances: Record<string, unknown>[], requestId: string) => {
      const newPredictions: StudentPrediction[] = results.map((result, idx) => {
        const features = (instances[idx] || {}) as StudentFeatures
        const riskLevel: RiskLevel = getRiskLevel(result.risk_score)
        return {
          ...result,
          id: `${requestId}-${idx}-${generateId()}`,
          timestamp: new Date().toISOString(),
          features,
          risk_level: riskLevel,
          pedra: classifyPedra(features),
        }
      })

      setPredictions((prev) => [...prev, ...newPredictions])
    },
    [],
  )

  const clearPredictions = useCallback(() => {
    setPredictions([])
    localStorage.removeItem(STORAGE_KEY)
  }, [])

  const getStudentHistory = useCallback(
    (features: StudentFeatures): StudentPrediction[] => {
      // Match by key feature combination
      const key = `${features.fase_2023}-${features.idade_2023}-${features.instituicao_2023}`
      return predictions.filter((p) => {
        const pKey = `${p.features.fase_2023}-${p.features.idade_2023}-${p.features.instituicao_2023}`
        return pKey === key
      })
    },
    [predictions],
  )

  return (
    <PredictionStoreContext.Provider
      value={{ predictions, addPredictions, clearPredictions, getStudentHistory }}
    >
      {children}
    </PredictionStoreContext.Provider>
  )
}

export function usePredictionStore(): PredictionStore {
  const ctx = useContext(PredictionStoreContext)
  if (!ctx) {
    throw new Error('usePredictionStore must be used within PredictionStoreProvider')
  }
  return ctx
}
