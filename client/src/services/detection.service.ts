import { apiClient } from "@/lib/api-client";
import type { DetectionResult, DetectionRecord } from "@/types";

export interface HistoryQueryParams {
  limit?: number;
  skip?: number;
}

export const detectionService = {
  detect: (formData: FormData) =>
    apiClient.post<DetectionResult>("/detect", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),

  getHistory: (params?: HistoryQueryParams) =>
    apiClient.get<{ records: DetectionRecord[] }>("/history", { params }),
};

