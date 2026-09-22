import { apiClient } from "@/lib/api-client";
import type { CartResponse, Order } from "@/types";

export interface AddToCartPayload {
  product_id: string;
  quantity?: number;
  record_id?: string;
}

export interface CheckoutPayload {
  shipping_address: string;
  phone_number: string;
}

export const cartService = {
  getCart: () =>
    apiClient.get<CartResponse>("/cart"),

  addItem: (payload: AddToCartPayload) =>
    apiClient.post("/cart/items", payload),

  updateQuantity: (itemId: string, quantity: number) =>
    apiClient.put(`/cart/items/${itemId}`, { quantity }),

  removeItem: (itemId: string) =>
    apiClient.put(`/cart/items/${itemId}`, { quantity: 0 }),

  clearCart: () =>
    apiClient.delete("/cart"),

  checkout: (payload: CheckoutPayload) =>
    apiClient.post<Order>("/orders/checkout", payload),
};

