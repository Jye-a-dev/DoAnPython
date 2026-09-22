"use client";

import { create } from "zustand";
import axios from "axios";
import { apiClient } from "@/lib/api-client";
import { CartItem, CartResponse, Order } from "@/types";
import { toast } from "sonner";

interface CartState {
  items: CartItem[];
  totalItems: number;
  totalAmount: number;
  isOpen: boolean;
  isLoading: boolean;
  isCheckingOut: boolean;
  confirmationAudioUrl: string | null;

  openCart: () => void;
  closeCart: () => void;
  fetchCart: () => Promise<void>;
  addToCart: (productId: string, quantity?: number, recordId?: string) => Promise<void>;
  updateQuantity: (itemId: string, quantity: number) => Promise<void>;
  removeItem: (itemId: string) => Promise<void>;
  clearCart: () => Promise<void>;
  checkout: (shippingAddress: string, phoneNumber: string) => Promise<Order | null>;
}

export const useCartStore = create<CartState>((set, get) => ({
  items: [],
  totalItems: 0,
  totalAmount: 0,
  isOpen: false,
  isLoading: false,
  isCheckingOut: false,
  confirmationAudioUrl: null,

  openCart: () => set({ isOpen: true }),
  closeCart: () => set({ isOpen: false }),

  fetchCart: async () => {
    set({ isLoading: true });
    try {
      const response = await apiClient.get<CartResponse>("/cart");
      set({
        items: response.data.items || [],
        totalItems: response.data.total_items || 0,
        totalAmount: response.data.total_amount || 0,
        isLoading: false,
      });
    } catch {
      set({ isLoading: false });
    }
  },

  addToCart: async (productId: string, quantity: number = 1, recordId?: string) => {
    try {
      await apiClient.post("/cart/items", {
        product_id: productId,
        quantity,
        record_id: recordId,
      });
      toast.success("Đã thêm vào giỏ hàng thành công!");
      await get().fetchCart();
    } catch (error: unknown) {
      let msg = "Không thể thêm vào giỏ hàng.";
      if (axios.isAxiosError(error) && error.response?.data?.detail) {
        msg = String(error.response.data.detail);
      }
      toast.error(msg);
      throw error;
    }
  },

  updateQuantity: async (itemId: string, quantity: number) => {
    try {
      await apiClient.put(`/cart/items/${itemId}`, { quantity });
      await get().fetchCart();
    } catch (error: unknown) {
      let msg = "Lỗi cập nhật giỏ hàng.";
      if (axios.isAxiosError(error) && error.response?.data?.detail) {
        msg = String(error.response.data.detail);
      }
      toast.error(msg);
    }
  },

  removeItem: async (itemId: string) => {
    try {
      await apiClient.put(`/cart/items/${itemId}`, { quantity: 0 });
      toast.success("Đã bỏ sản phẩm khỏi giỏ.");
      await get().fetchCart();
    } catch (error: unknown) {
      let msg = "Lỗi xóa sản phẩm.";
      if (axios.isAxiosError(error) && error.response?.data?.detail) {
        msg = String(error.response.data.detail);
      }
      toast.error(msg);
    }
  },

  clearCart: async () => {
    try {
      await apiClient.delete("/cart");
      set({ items: [], totalItems: 0, totalAmount: 0 });
      toast.success("Đã dọn sạch giỏ hàng.");
    } catch (error: unknown) {
      let msg = "Lỗi làm sạch giỏ hàng.";
      if (axios.isAxiosError(error) && error.response?.data?.detail) {
        msg = String(error.response.data.detail);
      }
      toast.error(msg);
    }
  },

  checkout: async (shippingAddress: string, phoneNumber: string) => {
    set({ isCheckingOut: true, confirmationAudioUrl: null });
    try {
      const response = await apiClient.post<Order>("/orders/checkout", {
        shipping_address: shippingAddress,
        phone_number: phoneNumber,
      });
      const order = response.data;
      set({
        items: [],
        totalItems: 0,
        totalAmount: 0,
        isCheckingOut: false,
        confirmationAudioUrl: order.audio_confirmation_url || null,
      });
      toast.success("Đặt hàng thành công!");
      return order;
    } catch (error: unknown) {
      set({ isCheckingOut: false });
      let msg = "Thanh toán thất bại.";
      if (axios.isAxiosError(error) && error.response?.data?.detail) {
        msg = String(error.response.data.detail);
      }
      toast.error(msg);
      return null;
    }
  },
}));
