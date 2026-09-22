import { apiClient } from "@/lib/api-client";
import type { ProductStats, OrderStats, DetectionRecord } from "@/types";

export const adminService = {
  getProductStats: () =>
    apiClient.get<ProductStats>("/products/stats"),

  getOrderStats: () =>
    apiClient.get<OrderStats>("/orders/stats"),

  getDetectionHistory: (params?: { limit?: number; skip?: number }) =>
    apiClient.get<{ records: DetectionRecord[] }>("/history", { params }),
};

