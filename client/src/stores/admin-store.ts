"use client";

import { create } from "zustand";
import type {
  ReviewQueueItem,
  InventoryForecastItem,
  ExecutiveDailyBriefingResponse,
} from "@/types";

interface AdminState {
  // Copilot Command Palette State
  isCopilotOpen: boolean;
  openCopilot: () => void;
  closeCopilot: () => void;
  toggleCopilot: () => void;

  // Review Queue Cache & Real-Time Removal
  reviewQueue: ReviewQueueItem[];
  setReviewQueue: (items: ReviewQueueItem[]) => void;
  removeReviewItem: (recordId: string) => void;

  // Inventory High Demand Alerts Cache
  inventoryForecast: InventoryForecastItem[];
  setInventoryForecast: (items: InventoryForecastItem[]) => void;

  // Executive Daily Briefing
  briefing: ExecutiveDailyBriefingResponse | null;
  setBriefing: (briefing: ExecutiveDailyBriefingResponse | null) => void;
}

export const useAdminStore = create<AdminState>((set) => ({
  isCopilotOpen: false,
  openCopilot: () => set({ isCopilotOpen: true }),
  closeCopilot: () => set({ isCopilotOpen: false }),
  toggleCopilot: () => set((state) => ({ isCopilotOpen: !state.isCopilotOpen })),

  reviewQueue: [],
  setReviewQueue: (items) => set({ reviewQueue: items }),
  removeReviewItem: (recordId) =>
    set((state) => ({
      reviewQueue: state.reviewQueue.filter((item) => item.id !== recordId),
    })),

  inventoryForecast: [],
  setInventoryForecast: (items) => set({ inventoryForecast: items }),

  briefing: null,
  setBriefing: (briefing) => set({ briefing }),
}));

