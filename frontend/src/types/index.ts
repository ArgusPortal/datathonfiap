// ==========================================
// API Types - Matching FastAPI backend schema
// ==========================================

// --- Prediction ---
export interface StudentFeatures {
  iaa_2023?: number | null
  ian_2023?: number | null
  ida_2023?: number | null
  ieg_2023?: number | null
  ipp_2023?: number | null
  ips_2023?: number | null
  ipv_2023?: number | null
  fase_2023?: string | null
  idade_2023?: number | null
  instituicao_2023?: string | null
  media_indicadores?: number | null
  std_indicadores?: number | null
  max_indicador?: number | null
  min_indicador?: number | null
  range_indicadores?: number | null
  [key: string]: number | string | null | undefined
}

export interface PredictRequest {
  instances: Record<string, unknown>[]
}

export interface PredictionResult {
  risk_score: number
  risk_label: number
  model_version: string
}

export interface PredictResponse {
  predictions: PredictionResult[]
  request_id: string
  processing_time_ms: number
}

// --- Health ---
export interface HealthResponse {
  status: 'healthy' | 'degraded'
  model_loaded: boolean
  model_version: string | null
  uptime_seconds: number
}

// --- Metadata ---
export interface MetadataResponse {
  model_version: string
  model_family: string
  threshold: number
  expected_features: string[]
  calibration: string | null
  created_at: string | null
}

// --- Metrics (matches metrics.get_summary()) ---
export interface MetricsResponse {
  uptime_seconds: number
  requests: {
    total: number
    success: number
    error: number
    rate_per_minute: number
  }
  latency_ms: {
    p50: number | null
    p95: number | null
    p99: number | null
    mean: number | null
  }
  predictions: {
    total: number
    positive: number
    negative: number
  }
  model: {
    version: string
    loaded_at: number
  }
  slo: SLOResponse
}

// --- SLO (matches metrics.get_slo_status()) ---
export interface SLOResponse {
  latency_p95_ms: number | null
  latency_slo_ms: number
  latency_slo_met: boolean
  error_rate: number
  error_rate_slo: number
  error_rate_slo_met: boolean
  overall_healthy: boolean
}

// --- Frontend-specific types ---
export type RiskLevel = 'low' | 'medium' | 'high'

export interface StudentPrediction extends PredictionResult {
  id: string
  timestamp: string
  features: StudentFeatures
  risk_level: RiskLevel
  pedra?: string
}

export interface DashboardStats {
  totalPredictions: number
  highRiskCount: number
  avgRiskScore: number
  modelStatus: 'healthy' | 'degraded' | 'offline'
}

// Feature metadata for form rendering
export interface FeatureMetadata {
  key: string
  label: string
  description: string
  type: 'number' | 'select'
  min?: number
  max?: number
  step?: number
  options?: { value: string; label: string }[]
  group: 'performance' | 'demographic' | 'derived'
}

// --- Artifact types ---
export interface ModelComparisonData {
  ranking: Array<{
    model: string
    recall: number
    precision: number
    f1: number
    f2: number
    pr_auc: number
    brier_score: number
    threshold: number
    rank: number
  }>
  best_model: string
  best_metrics: {
    recall: number
    precision: number
    f1: number
    f2: number
    confusion_matrix: number[][]
    true_negatives: number
    false_positives: number
    false_negatives: number
    true_positives: number
    pr_auc: number
    n_samples: number
    n_positive: number
    n_negative: number
    baseline_rate: number
    model_name: string
    brier_score: number
    calibration_error: number
    threshold: number
  }
  primary_metric: string
  constraints_applied: { min_recall: number }
  validation_results: Record<string, ModelResult>
  test_results: Record<string, ModelResult>
  selection_criteria: string
}

export interface ModelResult {
  recall: number
  precision: number
  f1: number
  f2: number
  confusion_matrix: number[][]
  true_negatives: number
  false_positives: number
  false_negatives: number
  true_positives: number
  pr_auc: number
  n_samples?: number
  n_positive?: number
  n_negative?: number
  baseline_rate?: number
  model_name: string
  brier_score: number
  calibration_error: number
  threshold?: number
  fpr?: number
}

export interface ArtifactMetadata {
  model_version: string
  created_at: string
  seed: number
  sklearn_version: string
  target_definition: string
  training_periods: string[]
  population_filter: string
  expected_features: string[]
  blocked_features: string[]
  threshold_policy: {
    objective: string
    min_precision: number | null
    threshold_value: number
  }
  assumptions: string[]
}

// --- Drift types ---
export interface DriftStatus {
  status: string
  features: Record<string, {
    psi: number
    status: 'green' | 'yellow' | 'red'
    baseline_dist: Record<string, number>
    current_dist: Record<string, number>
  }>
  score_drift: {
    status: 'green' | 'yellow' | 'red' | 'insufficient_data'
    psi: number
    baseline_dist?: Record<string, number>
    current_dist?: Record<string, number>
  }
  missing_rates?: {
    baseline: Record<string, number>
    current: Record<string, number>
  }
  overall_status: 'green' | 'yellow' | 'red'
  n_baseline_events?: number
  n_current_events?: number
  message?: string
}

// --- Inference History ---
export interface InferenceEvent {
  timestamp: string
  request_id: string
  model_version: string
  batch_stats: {
    n_instances: number
    missing_summary: Record<string, number>
    feature_distribution: Record<string, Record<string, number>>
  }
  prediction_summary: {
    n_predictions: number
    n_high_risk: number
    mean_score: number
    score_bins: {
      low: number
      medium: number
      high: number
    }
  }
}

// --- Audit ---
export interface AuditRecord {
  timestamp: string
  action: string
  request_id: string | null
  details: Record<string, unknown>
  git_sha: string
}
