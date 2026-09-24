"use client";

import * as React from "react";
import Image from "next/image";
import { Eye, Loader2, Sparkles, ThumbsUp } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { resolveMediaUrl } from "@/lib/api-client";
import type { ReviewQueueItem, VLMSuggestion } from "@/types";

interface ReviewVlmSectionProps {
  selectedItem: ReviewQueueItem;
  vlmSuggestion: VLMSuggestion | null;
  isLoadingVLM: boolean;
  onFetchVLM: () => void;
  onApplySuggestion: () => void;
}

export function ReviewVlmSection({
  selectedItem,
  vlmSuggestion,
  isLoadingVLM,
  onFetchVLM,
  onApplySuggestion,
}: ReviewVlmSectionProps) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      {/* Captured Camera Photo */}
      <div className="space-y-1.5">
        <span className="text-xs font-semibold text-muted-foreground flex items-center gap-1">
          <Eye className="h-3.5 w-3.5 text-blue-500" />
          <span>Ảnh Chụp Camera Thực Tế</span>
        </span>
        <div className="relative aspect-video rounded-xl overflow-hidden border border-border bg-black/40">
          {selectedItem.image_url ? (
            <Image
              src={resolveMediaUrl(selectedItem.image_url)}
              alt="Annotated Scan"
              fill
              className="object-contain"
            />
          ) : (
            <div className="h-full w-full flex items-center justify-center text-xs text-muted-foreground">
              Không có ảnh khả dụng
            </div>
          )}
        </div>
      </div>

      {/* Model Comparison: YOLO vs VLM */}
      <div className="space-y-3 flex flex-col justify-between">
        <div className="space-y-2">
          <span className="text-xs font-semibold text-muted-foreground">
            Đối Soát Nhãn Nhận Diện
          </span>

          {/* Current YOLO Label */}
          <div className="p-3 rounded-lg border border-border bg-muted/30 space-y-1">
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground">Dự đoán hiện tại (YOLO):</span>
              <Badge variant="secondary" className="font-mono text-[10px]">
                {Math.round(selectedItem.confidence_score * 100)}%
              </Badge>
            </div>
            <p className="text-xs font-semibold text-foreground">
              {selectedItem.raw_detected_text}
            </p>
          </div>

          {/* VLM Suggestion Box */}
          <div className="p-3 rounded-lg border border-indigo-500/30 bg-indigo-500/5 space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="text-indigo-400 font-medium flex items-center gap-1">
                <Sparkles className="h-3.5 w-3.5 text-indigo-400" />
                AI Suggestion (VLM):
              </span>
              {vlmSuggestion ? (
                <Badge className="bg-emerald-500/15 text-emerald-500 border border-emerald-500/30 font-mono text-[10px]">
                  {Math.round(vlmSuggestion.confidence * 100)}% Conf
                </Badge>
              ) : (
                <Button
                  onClick={onFetchVLM}
                  disabled={isLoadingVLM}
                  size="sm"
                  variant="outline"
                  className="h-6 text-[10px] gap-1 text-indigo-400 border-indigo-500/30 hover:bg-indigo-500/10 cursor-pointer"
                >
                  {isLoadingVLM ? (
                    <Loader2 className="h-3 w-3 animate-spin" />
                  ) : (
                    <Sparkles className="h-3 w-3" />
                  )}
                  <span>Kích hoạt VLM</span>
                </Button>
              )}
            </div>

            {vlmSuggestion ? (
              <div className="space-y-2">
                <p className="text-xs font-semibold text-foreground">
                  {vlmSuggestion.suggested_label}
                </p>
                <p className="text-[11px] text-muted-foreground italic">
                  &quot;{vlmSuggestion.explanation}&quot;
                </p>
                <Button
                  onClick={onApplySuggestion}
                  size="sm"
                  className="w-full h-7 text-xs bg-indigo-600 hover:bg-indigo-500 text-white gap-1.5 cursor-pointer"
                >
                  <ThumbsUp className="h-3.5 w-3.5" />
                  <span>1-Click Approve Suggestion</span>
                </Button>
              </div>
            ) : (
              <p className="text-[11px] text-muted-foreground">
                Bấm &quot;Kích hoạt VLM&quot; để bóc tách ngữ cảnh chi tiết (ví dụ: &quot;laptop đang gập&quot; vs &quot;cuốn sách&quot;).
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

