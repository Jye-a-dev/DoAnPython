import { apiClient } from "@/lib/api-client";
import type { Product, Category, ProductStats } from "@/types";

export interface ProductQueryParams {
  limit?: number;
  skip?: number;
  category_id?: string;
  search?: string;
}

export const productService = {
  getAll: (params?: ProductQueryParams) =>
    apiClient.get<Product[]>("/products", { params }),

  getById: (id: string) =>
    apiClient.get<Product>(`/products/${id}`),

  getCategories: () =>
    apiClient.get<Category[]>("/categories"),

  matchFromScan: (recordId: string) =>
    apiClient.post<Product[]>("/products/match-from-scan", { record_id: recordId }),

  getStats: () =>
    apiClient.get<ProductStats>("/products/stats"),
};

