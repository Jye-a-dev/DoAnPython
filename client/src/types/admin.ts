import type { DetectionObject } from "./index";

export interface VLMSuggestion {
  suggested_label: string;
  confidence: number;
  explanation: string;
  suggested_class_name: string;
  box?: {
    xmin: number;
    ymin: number;
    xmax: number;
    ymax: number;
  };
}

export interface ReviewQueueItem {
  id: string;
  user_id: string;
  image_url: string;
  summary: string;
  raw_detected_text: string;
  objects: DetectionObject[];
  status: "pending" | "approved" | "rejected";
  confidence_score: number;
  created_at: string;
  vlm_suggestion?: VLMSuggestion | null;
}

export interface TTSPreviewResponse {
  audio_url: string;
  status: string;
}

export interface SubmitReviewPayload {
  record_id: string;
  corrected_text: string;
  accuracy_score: number;
  review_notes?: string;
}

export interface SubmitReviewResponse {
  id: string;
  record_id: string;
  admin_id: string;
  corrected_text: string;
  corrected_audio_url: string;
  accuracy_score: number;
  review_notes?: string;
  reviewed_at: string;
}

export interface AutoTagResponse {
  class_name: string;
  tag: string;
  label_vi: string;
  suggested_category_id: string | null;
  suggested_category_name: string | null;
  confidence: number;
  summary: string;
}

export interface InventoryForecastItem {
  product_id: string;
  sku: string | null;
  name: string;
  class_name: string;
  stock_quantity: number;
  scan_count_7d: number;
  daily_scan_rate: number;
  stockout_eta_days: number | null;
  urgency: "CRITICAL" | "HIGH" | "MODERATE" | "NORMAL";
  warning_badge: string | null;
}

export interface InventoryForecastResponse {
  items: InventoryForecastItem[];
  high_demand_count: number;
  cached_at: string;
}

export interface OOVTermItem {
  term: string;
  occurrences: number;
  last_seen: string;
  suggested_category?: string;
}

export interface RetrainQueueItem {
  record_id: string;
  image_url: string;
  raw_detected_text: string;
  corrected_text: string;
  confidence: number;
  reason: string;
  reviewed_at: string;
}

export interface ModelDriftResponse {
  drift_score: number; // Percentage 0 - 100
  total_analyzed: number;
  low_confidence_count: number;
  corrected_count: number;
  oov_terms: OOVTermItem[];
  retrain_queue: RetrainQueueItem[];
}

export interface ErrorClusterItem {
  cluster_id: string;
  cluster_name: string;
  description: string;
  count: number;
  record_ids: string[];
}

export interface ErrorClustersResponse {
  clusters: ErrorClusterItem[];
  total_flagged: number;
}

export interface CopilotQueryPayload {
  query: string;
}

export interface CopilotQueryResult {
  query: string;
  intent: string;
  safe_sql: string | null;
  count: number;
  results: Record<string, unknown>[];
  route_suggestion: string | null;
  explanation: string;
}

export interface ExecutiveDailyBriefingResponse {
  summary: string;
  metrics: {
    scans_today: number;
    low_stock_count: number;
    pending_reviews_count: number;
    revenue_today: number;
    at_risk_classes: string[];
  };
  generated_at: string;
}

