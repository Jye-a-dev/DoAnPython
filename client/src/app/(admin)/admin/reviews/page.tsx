"use client";

import * as React from "react";
import { CheckCircle2, RefreshCw } from "lucide-react";
import { toast } from "sonner";
import { adminService } from "@/services/admin.service";
import { resolveMediaUrl } from "@/lib/api-client";
import type { ReviewQueueItem, VLMSuggestion } from "@/types";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  ReviewEmptyState,
  ReviewInspector,
  ReviewQueueList,
} from "@/components/admin/reviews";

export default function AdminReviewsPage() {
  const [items, setItems] = React.useState<ReviewQueueItem[]>([]);
  const [isLoading, setIsLoading] = React.useState(true);
  const [selectedItem, setSelectedItem] = React.useState<ReviewQueueItem | null>(null);

  // VLM State
  const [isLoadingVLM, setIsLoadingVLM] = React.useState(false);
  const [vlmSuggestion, setVlmSuggestion] = React.useState<VLMSuggestion | null>(null);

  // Review Form State
  const [correctedText, setCorrectedText] = React.useState("");
  const [accuracyScore, setAccuracyScore] = React.useState(0.95);
  const [reviewNotes, setReviewNotes] = React.useState("");

  // TTS Audio Player State
  const [previewAudioUrl, setPreviewAudioUrl] = React.useState<string | null>(null);
  const [isSynthesizingTTS, setIsSynthesizingTTS] = React.useState(false);
  const [isPlayingAudio, setIsPlayingAudio] = React.useState(false);
  const audioRef = React.useRef<HTMLAudioElement | null>(null);

  const [isSubmitting, setIsSubmitting] = React.useState(false);

  const selectRecord = React.useCallback((item: ReviewQueueItem) => {
    setSelectedItem(item);
    setCorrectedText(item.raw_detected_text);
    setAccuracyScore(item.confidence_score >= 0.85 ? item.confidence_score : 0.95);
    setReviewNotes("");
    setVlmSuggestion(null);
    setPreviewAudioUrl(null);
    setIsPlayingAudio(false);
    if (audioRef.current) {
      audioRef.current.pause();
    }
  }, []);

  const loadQueue = React.useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await adminService.getReviewQueue({ limit: 50 });
      const rawList = res.data || [];
      const mapped: ReviewQueueItem[] = rawList.map((rec) => {
        let conf = 0.8;
        if (rec.objects && rec.objects.length > 0) {
          conf = Math.min(...rec.objects.map((o) => o.confidence || 0.8));
        }
        return {
          id: rec.id,
          user_id: rec.user_id || "anonymous",
          image_url: rec.image_url,
          summary: rec.summary || rec.raw_detected_text || "Không có tóm tắt",
          raw_detected_text: rec.raw_detected_text || rec.summary || "",
          objects: rec.objects || [],
          status: (rec.status as "pending" | "approved" | "rejected") || "pending",
          confidence_score: conf,
          created_at: rec.created_at,
        };
      });
      setItems(mapped);
      if (mapped.length > 0 && !selectedItem) {
        selectRecord(mapped[0]);
      }
    } catch {
      toast.error("Không thể tải hàng đợi kiểm duyệt.");
    } finally {
      setIsLoading(false);
    }
  }, [selectedItem, selectRecord]);

  React.useEffect(() => {
    loadQueue();
  }, [loadQueue]);

  const handleFetchVLM = async () => {
    if (!selectedItem) return;
    setIsLoadingVLM(true);
    try {
      const res = await adminService.getVLMSuggestion(selectedItem.id);
      setVlmSuggestion(res.data);
      toast.success("AI đã phân tích xong ngữ cảnh vật thể!");
    } catch {
      toast.error("Không thể bóc tách ngữ cảnh VLM.");
    } finally {
      setIsLoadingVLM(false);
    }
  };

  const handleApplySuggestion = () => {
    if (!vlmSuggestion) return;
    setCorrectedText(vlmSuggestion.suggested_label);
    setAccuracyScore(vlmSuggestion.confidence || 0.95);
    setReviewNotes(vlmSuggestion.explanation);
    toast.info("Đã áp dụng đề xuất nhãn ngữ cảnh từ VLM!");
  };

  const handlePreviewTTS = async () => {
    const textToSpeak = correctedText.trim();
    if (!textToSpeak) {
      toast.error("Vui lòng nhập văn bản trước khi nghe thử.");
      return;
    }

    setIsSynthesizingTTS(true);
    try {
      const res = await adminService.previewTTS(textToSpeak);
      const url = resolveMediaUrl(res.data.audio_url);
      setPreviewAudioUrl(url);

      if (audioRef.current) {
        audioRef.current.src = url;
        audioRef.current.play().then(() => setIsPlayingAudio(true)).catch(() => {});
      }
      toast.success("Đã sinh giọng đọc Neural TTS (vi-VN-HoaiMyNeural)!");
    } catch {
      toast.error("Tổng hợp giọng đọc TTS thất bại.");
    } finally {
      setIsSynthesizingTTS(false);
    }
  };

  const toggleAudio = () => {
    if (!audioRef.current) return;
    if (isPlayingAudio) {
      audioRef.current.pause();
      setIsPlayingAudio(false);
    } else {
      audioRef.current.play().then(() => setIsPlayingAudio(true)).catch(() => {});
    }
  };

  const handleSubmitReview = async () => {
    if (!selectedItem) return;
    if (!correctedText.trim()) {
      toast.error("Nhãn hiệu chỉnh không được để trống.");
      return;
    }

    setIsSubmitting(true);
    try {
      await adminService.submitReview({
        record_id: selectedItem.id,
        corrected_text: correctedText.trim(),
        accuracy_score: accuracyScore,
        review_notes: reviewNotes.trim() || undefined,
      });

      toast.success(`Đã duyệt và lưu bản ghi #${selectedItem.id.slice(0, 8)} thành công!`);
      const nextQueue = items.filter((i) => i.id !== selectedItem.id);
      setItems(nextQueue);
      if (nextQueue.length > 0) {
        selectRecord(nextQueue[0]);
      } else {
        setSelectedItem(null);
      }
    } catch {
      toast.error("Lỗi khi gửi thẩm định lên Gateway.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-6">
        <div>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="gap-1 px-2.5 py-0.5 text-cyan-500 border-cyan-500/30">
              <CheckCircle2 className="h-3.5 w-3.5" />
              OCR & LABEL AUDIT
            </Badge>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">
              Kiểm Duyệt & Hiệu Chỉnh AI Nâng Cao
            </h1>
          </div>
          <p className="text-xs sm:text-sm text-muted-foreground mt-1">
            Gợi ý nhãn ngữ cảnh qua VLM Florence-2 / Gemini Vision, thẩm định 1-click và sinh giọng đọc Neural TTS.
          </p>
        </div>

        <Button
          onClick={loadQueue}
          variant="outline"
          size="sm"
          disabled={isLoading}
          className="gap-1.5 cursor-pointer text-xs"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${isLoading ? "animate-spin" : ""}`} />
          <span>Làm mới hàng đợi ({items.length})</span>
        </Button>
      </div>

      {items.length === 0 && !isLoading ? (
        <ReviewEmptyState />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <ReviewQueueList
            items={items}
            selectedItem={selectedItem}
            onSelect={selectRecord}
          />

          <div className="lg:col-span-8">
            {selectedItem && (
              <ReviewInspector
                selectedItem={selectedItem}
                vlmSuggestion={vlmSuggestion}
                isLoadingVLM={isLoadingVLM}
                onFetchVLM={handleFetchVLM}
                onApplySuggestion={handleApplySuggestion}
                correctedText={correctedText}
                onCorrectedTextChange={setCorrectedText}
                accuracyScore={accuracyScore}
                onAccuracyScoreChange={setAccuracyScore}
                reviewNotes={reviewNotes}
                onReviewNotesChange={setReviewNotes}
                previewAudioUrl={previewAudioUrl}
                isSynthesizingTTS={isSynthesizingTTS}
                isPlayingAudio={isPlayingAudio}
                onPreviewTTS={handlePreviewTTS}
                onToggleAudio={toggleAudio}
                onAudioEnded={() => setIsPlayingAudio(false)}
                onAudioError={() => setIsPlayingAudio(false)}
                audioRef={audioRef}
                isSubmitting={isSubmitting}
                onSubmitReview={handleSubmitReview}
              />
            )}
          </div>
        </div>
      )}
    </div>
  );
}
