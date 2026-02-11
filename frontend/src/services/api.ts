import type {
  HealthResponse,
  MetadataResponse,
  MetricsResponse,
  PredictRequest,
  PredictResponse,
  SLOResponse,
  ModelComparisonData,
  ArtifactMetadata,
  DriftStatus,
  InferenceEvent,
  AuditRecord,
  FairnessAnalysis,
} from '@/types'

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api'

class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string,
    public requestId?: string,
  ) {
    super(detail)
    this.name = 'ApiError'
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${path}`

  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Erro de rede' }))
    throw new ApiError(response.status, error.detail || 'Erro desconhecido', error.request_id)
  }

  return response.json()
}

export const api = {
  // Health & Status
  health: () => request<HealthResponse>('/health'),
  ready: () => request<{ ready: boolean; model_version?: string }>('/ready'),

  // Model
  metadata: () => request<MetadataResponse>('/metadata'),

  // Prediction
  predict: (data: PredictRequest) =>
    request<PredictResponse>('/predict', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  // Observability
  metrics: () => request<MetricsResponse>('/metrics?format=json'),
  slo: () => request<SLOResponse>('/slo'),

  // Artifacts
  artifactMetrics: () => request<ModelComparisonData>('/artifacts/metrics'),
  artifactMetadata: () => request<ArtifactMetadata>('/artifacts/metadata'),
  artifactReport: () => request<{ content: string; format: string }>('/artifacts/report'),
  artifactFairness: () => request<FairnessAnalysis>('/artifacts/fairness'),

  // Inference history
  inferenceHistory: (limit = 200) =>
    request<{ events: InferenceEvent[]; total: number }>(`/inference/history?limit=${limit}`),

  // Drift
  driftStatus: () => request<DriftStatus>('/drift/status'),

  // Audit
  auditRecent: (limit = 50) =>
    request<{ records: AuditRecord[]; summary: Record<string, unknown> }>(`/audit/recent?limit=${limit}`),

  // EDA (Exploratory Data Analysis)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  eda: () => request<any>('/analysis/eda'),
}

export { ApiError }
export default api
