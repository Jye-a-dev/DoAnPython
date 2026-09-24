"use client";

import * as React from "react";

interface ReviewFormProps {
  correctedText: string;
  onCorrectedTextChange: (text: string) => void;
  accuracyScore: number;
  onAccuracyScoreChange: (score: number) => void;
  reviewNotes: string;
  onReviewNotesChange: (notes: string) => void;
}

export function ReviewForm({
  correctedText,
  onCorrectedTextChange,
  accuracyScore,
  onAccuracyScoreChange,
  reviewNotes,
  onReviewNotesChange,
}: ReviewFormProps) {
  return (
    <div className="space-y-3 pt-2 border-t border-border">
      <div className="space-y-1">
        <label className="text-xs font-semibold text-foreground">
          Nhãn Văn Bản Hiệu Chỉnh (Ground Truth Text) *
        </label>
        <input
          type="text"
          value={correctedText}
          onChange={(e) => onCorrectedTextChange(e.target.value)}
          placeholder="Nhập nội dung nhãn tiếng Việt chuẩn..."
          className="h-9 w-full rounded-md border border-border bg-background px-3 text-xs focus:outline-none focus:ring-1 focus:ring-primary font-medium"
        />
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div className="space-y-1">
          <label className="text-xs font-medium text-foreground">
            Độ tin cậy chuẩn hoá (0.0 - 1.0)
          </label>
          <input
            type="number"
            step="0.05"
            min="0"
            max="1.0"
            value={accuracyScore}
            onChange={(e) => onAccuracyScoreChange(parseFloat(e.target.value) || 0.95)}
            className="h-8 w-full rounded-md border border-border bg-background px-3 font-mono text-xs focus:outline-none focus:ring-1 focus:ring-primary"
          />
        </div>

        <div className="space-y-1">
          <label className="text-xs font-medium text-foreground">
            Ghi chú đối soát
          </label>
          <input
            type="text"
            value={reviewNotes}
            onChange={(e) => onReviewNotesChange(e.target.value)}
            placeholder="VD: Đã hiệu chỉnh theo VLM bóc tách ngữ cảnh..."
            className="h-8 w-full rounded-md border border-border bg-background px-3 text-xs focus:outline-none focus:ring-1 focus:ring-primary"
          />
        </div>
      </div>
    </div>
  );
}

