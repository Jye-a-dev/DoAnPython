import { apiClient } from "@/lib/api-client";
import type {
  ProductStats,
  OrderStats,
  DetectionRecord,
  ReviewQueueItem,
  VLMSuggestion,
  TTSPreviewResponse,
  SubmitReviewPayload,
  SubmitReviewResponse,
  AutoTagResponse,
  InventoryForecastResponse,
  ModelDriftResponse,
  ErrorClustersResponse,
  CopilotQueryResult,
  ExecutiveDailyBriefingResponse,
} from "@/types";

export const adminService = {
  // Existing Dashboard Metrics
  getProductStats: () =>
    apiClient.get<ProductStats>("/products/stats"),

  getOrderStats: () =>
    apiClient.get<OrderStats>("/orders/stats"),

  getDetectionHistory: (params?: { limit?: number; skip?: number; status?: string }) =>
    apiClient.get<DetectionRecord[]>("/ocr-records", { params }),

  // Module 1: AI Review & Neural TTS
  getReviewQueue: (params?: { limit?: number; skip?: number }) =>
    apiClient.get<ReviewQueueItem[]>("/ocr-records", {
      params: { ...params, status: "pending" },
    }),

  getVLMSuggestion: (recordId: string) =>
    apiClient.post<VLMSuggestion>(`/ocr-records/${recordId}/vlm-suggest`),

  previewTTS: (text: string) =>
    apiClient.post<TTSPreviewResponse>("/ocr-reviews/preview-tts", { text }),

  submitReview: (payload: SubmitReviewPayload) =>
    apiClient.post<SubmitReviewResponse>("/ocr-reviews", payload),

  // Module 2: Products & Visual Auto-Tagging & Inventory Forecasting
  autoTagProduct: (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return apiClient.post<AutoTagResponse>("/products/auto-tag", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },

  getInventoryForecast: () =>
    apiClient.get<InventoryForecastResponse>("/products/inventory-forecast"),

  // Module 3: MLOps Drift & Clustering
  getModelDrift: () =>
    apiClient.get<ModelDriftResponse>("/mlops/drift-alert"),

  getErrorClusters: () =>
    apiClient.get<ErrorClustersResponse>("/mlops/error-clusters"),

  exportRetrainDataset: (clusterId?: string) =>
    apiClient.get<Blob>("/mlops/export-dataset", {
      params: clusterId ? { cluster_id: clusterId } : undefined,
      responseType: "blob",
    }),

  // Module 4: Safe Text-to-SQL Copilot & Executive Briefing
  queryCopilot: (query: string) =>
    apiClient.post<CopilotQueryResult>("/copilot/query", { query }),

  getDailyBriefing: () =>
    apiClient.get<ExecutiveDailyBriefingResponse>("/copilot/daily-briefing"),
};
