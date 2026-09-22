"use client";

import { create } from "zustand";
import axios from "axios";
import { resolveMediaUrl } from "@/lib/api-client";
import { detectionService, productService } from "@/services";
import { DetectionResult, Product } from "@/types";
import { toast } from "sonner";

interface VisualSearchState {
  isOpen: boolean;
  selectedFile: File | null;
  previewUrl: string | null;
  isDetecting: boolean;
  isLoadingMatches: boolean;
  detectionResult: DetectionResult | null;
  matchedProducts: Product[];
  audioUrl: string | null;

  openModal: () => void;
  closeModal: () => void;
  setSelectedFile: (file: File | null) => void;
  uploadAndDetect: (file: File) => Promise<void>;
  reset: () => void;
}

export const useVisualSearchStore = create<VisualSearchState>((set) => ({
  isOpen: false,
  selectedFile: null,
  previewUrl: null,
  isDetecting: false,
  isLoadingMatches: false,
  detectionResult: null,
  matchedProducts: [],
  audioUrl: null,

  openModal: () => set({ isOpen: true }),
  closeModal: () => set({ isOpen: false }),

  setSelectedFile: (file: File | null) => {
    if (!file) {
      set({ selectedFile: null, previewUrl: null });
      return;
    }
    const preview = URL.createObjectURL(file);
    set({ selectedFile: file, previewUrl: preview });
  },

  uploadAndDetect: async (file: File) => {
    const preview = URL.createObjectURL(file);
    set({
      selectedFile: file,
      previewUrl: preview,
      isDetecting: true,
      detectionResult: null,
      matchedProducts: [],
      audioUrl: null,
    });

    try {
      const formData = new FormData();
      formData.append("file", file);

      // 1. Gửi ảnh lên Gateway /detect
      const detectResponse = await detectionService.detect(formData);

      const result = detectResponse.data;
      const resolvedAudio = resolveMediaUrl(result.audio_url);

      set({
        detectionResult: result,
        audioUrl: resolvedAudio,
        isDetecting: false,
        isLoadingMatches: true,
      });

      // 2. Tự động phát âm thanh tóm tắt TTS nếu có
      if (resolvedAudio && typeof window !== "undefined") {
        try {
          const audio = new Audio(resolvedAudio);
          audio.play().catch(() => {
            // Trình duyệt có thể chặn autoplay nếu chưa có tương tác
          });
        } catch {
          // Lỗi phát âm thanh không chặn luồng hiển thị
        }
      }

      // 3. Gọi /products/match-from-scan với record_id
      try {
        const matchResponse = await productService.matchFromScan(result.id);
        set({
          matchedProducts: matchResponse.data || [],
          isLoadingMatches: false,
        });
        toast.success(`Phát hiện ${result.objects?.length || 0} vật thể trong ảnh!`);
      } catch {
        set({ matchedProducts: [], isLoadingMatches: false });
      }
    } catch (error: unknown) {
      set({
        isDetecting: false,
        isLoadingMatches: false,
      });
      let errorDetail = "Nhận diện vật thể thất bại.";
      if (axios.isAxiosError(error) && error.response?.data?.detail) {
        errorDetail = String(error.response.data.detail);
      }
      toast.error(errorDetail);
    }
  },

  reset: () =>
    set({
      selectedFile: null,
      previewUrl: null,
      isDetecting: false,
      isLoadingMatches: false,
      detectionResult: null,
      matchedProducts: [],
      audioUrl: null,
    }),
}));