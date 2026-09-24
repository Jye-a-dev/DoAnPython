"use client";

import * as React from "react";
import { Check, Loader2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { ReviewQueueItem, VLMSuggestion } from "@/types";
import { ReviewVlmSection } from "./review-vlm-section";
import { ReviewForm } from "./review-form";
import { ReviewTTSPlayer } from "./review-tts-player";

interface ReviewInspectorProps {
  selectedItem: ReviewQueueItem;
  vlmSuggestion: VLMSuggestion | null;
  isLoadingVLM: boolean;
  onFetchVLM: () => void;
  onApplySuggestion: () => void;
  correctedText: string;
  onCorrectedTextChange: (text: string) => void;
  accuracyScore: number;
  onAccuracyScoreChange: (score: number) => void;
  reviewNotes: string;
  onReviewNotesChange: (notes: string) => void;
  previewAudioUrl: string | null;
  isSynthesizingTTS: boolean;
  isPlayingAudio: boolean;
  onPreviewTTS: () => void;
  onToggleAudio: () => void;
  onAudioEnded: () => void;
  onAudioError: () => void;
  audioRef: React.RefObject<HTMLAudioElement | null>;
  isSubmitting: boolean;
  onSubmitReview: () => void;
}

export function ReviewInspector({
  selectedItem,
  vlmSuggestion,
  isLoadingVLM,
  onFetchVLM,
  onApplySuggestion,
  correctedText,
  onCorrectedTextChange,
  accuracyScore,
  onAccuracyScoreChange,
  reviewNotes,
  onReviewNotesChange,
  previewAudioUrl,
  isSynthesizingTTS,
  isPlayingAudio,
  onPreviewTTS,
  onToggleAudio,
  onAudioEnded,
  onAudioError,
  audioRef,
  isSubmitting,
  onSubmitReview,
}: ReviewInspectorProps) {
  return (
    <Card className="border-border bg-card/80 backdrop-blur-md">
      <CardHeader className="pb-4 border-b border-border/70">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <CardTitle className="text-base font-semibold flex items-center gap-2">
              <span>Thẩm Định Bản Ghi:</span>
              <span className="font-mono text-cyan-500 text-sm">{selectedItem.id}</span>
            </CardTitle>
            <CardDescription className="text-xs">
              Thời điểm quét: {new Date(selectedItem.created_at).toLocaleString("vi-VN")}
            </CardDescription>
          </div>
          <Badge variant="outline" className="border-cyan-500/40 text-cyan-500 text-xs self-start">
            3-Phase Isolation Active
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="p-5 space-y-5">
        <ReviewVlmSection
          selectedItem={selectedItem}
          vlmSuggestion={vlmSuggestion}
          isLoadingVLM={isLoadingVLM}
          onFetchVLM={onFetchVLM}
          onApplySuggestion={onApplySuggestion}
        />

        <ReviewForm
          correctedText={correctedText}
          onCorrectedTextChange={onCorrectedTextChange}
          accuracyScore={accuracyScore}
          onAccuracyScoreChange={onAccuracyScoreChange}
          reviewNotes={reviewNotes}
          onReviewNotesChange={onReviewNotesChange}
        />

        <ReviewTTSPlayer
          previewAudioUrl={previewAudioUrl}
          isSynthesizing={isSynthesizingTTS}
          isPlaying={isPlayingAudio}
          canSynthesize={Boolean(correctedText.trim())}
          onSynthesize={onPreviewTTS}
          onTogglePlay={onToggleAudio}
          onEnded={onAudioEnded}
          onError={onAudioError}
          audioRef={audioRef}
        />

        <div className="flex items-center justify-end gap-3 pt-2 border-t border-border">
          <Button
            onClick={onSubmitReview}
            disabled={isSubmitting}
            className="bg-emerald-600 hover:bg-emerald-500 text-white gap-2 cursor-pointer text-xs"
          >
            {isSubmitting ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Check className="h-4 w-4" />
            )}
            <span>Phê duyệt & Lưu vào DB</span>
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

