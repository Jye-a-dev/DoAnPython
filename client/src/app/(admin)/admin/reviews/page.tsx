"use client";

import * as React from "react";
import Image from "next/image";
import {
  CheckCircle2,
  RefreshCw,
  Sparkles,
  Volume2,
  Play,
  Pause,
  ThumbsUp,
  Check,
  Eye,
  Loader2,
} from "lucide-react";
import { toast } from "sonner";
import { adminService } from "@/services/admin.service";
import { resolveMediaUrl } from "@/lib/api-client";
import type { ReviewQueueItem, VLMSuggestion } from "@/types";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";

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
  }, [selectedItem]);

  React.useEffect(() => {
    loadQueue();
  }, [loadQueue]);

  const selectRecord = (item: ReviewQueueItem) => {
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
  };

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
      // Remove reviewed item from queue
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
        <Card className="border-border bg-card/60 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="text-base font-semibold flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-cyan-500" />
              Hàng đợi kiểm duyệt nhãn AI
            </CardTitle>
            <CardDescription className="text-xs">
              Các phát hiện có độ tin cậy thấp hoặc ở trạng thái chờ duyệt
            </CardDescription>
          </CardHeader>
          <CardContent className="py-12 flex flex-col items-center justify-center text-center space-y-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-500">
              <CheckCircle2 className="h-6 w-6" />
            </div>
            <h3 className="font-semibold text-sm text-foreground">Hàng đợi đang trống</h3>
            <p className="text-xs text-muted-foreground max-w-sm">
              Mọi kết quả nhận diện camera gần đây đều đã được duyệt hoặc đạt độ tin cậy cao. Không có nhãn nào cần can thiệp.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column: Queue Items List */}
          <div className="lg:col-span-4 space-y-3">
            <div className="flex items-center justify-between text-xs text-muted-foreground px-1">
              <span>Bản ghi chờ duyệt</span>
              <span className="font-mono font-semibold">{items.length} items</span>
            </div>

            <div className="space-y-2 max-h-[700px] overflow-y-auto pr-1">
              {items.map((item) => {
                const isSelected = selectedItem?.id === item.id;
                const isLowConf = item.confidence_score < 0.85;
                return (
                  <div
                    key={item.id}
                    onClick={() => selectRecord(item)}
                    className={`p-3 rounded-xl border transition-all cursor-pointer flex gap-3 items-center ${
                      isSelected
                        ? "border-primary bg-primary/5 shadow-sm"
                        : "border-border bg-card/60 hover:bg-muted/40"
                    }`}
                  >
                    <div className="relative h-14 w-14 rounded-lg overflow-hidden border border-border bg-muted shrink-0">
                      {item.image_url ? (
                        <Image
                          src={resolveMediaUrl(item.image_url)}
                          alt="Scan Photo"
                          fill
                          className="object-cover"
                        />
                      ) : (
                        <div className="h-full w-full flex items-center justify-center text-[10px] text-muted-foreground">
                          No IMG
                        </div>
                      )}
                    </div>

                    <div className="flex-1 min-w-0 space-y-1">
                      <div className="flex items-center justify-between gap-1">
                        <span className="text-xs font-semibold text-foreground truncate">
                          {item.raw_detected_text || "Chưa có nhãn"}
                        </span>
                        <Badge
                          variant={isLowConf ? "destructive" : "secondary"}
                          className="text-[10px] px-1.5 py-0 font-mono shrink-0"
                        >
                          {Math.round(item.confidence_score * 100)}%
                        </Badge>
                      </div>
                      <p className="text-[11px] text-muted-foreground font-mono truncate">
                        ID: {item.id.slice(0, 8)}...
                      </p>
                      <div className="flex items-center gap-1.5 text-[10px] text-muted-foreground">
                        <span>{new Date(item.created_at).toLocaleTimeString("vi-VN")}</span>
                        <span>•</span>
                        <span className="text-amber-500 font-medium">Chờ duyệt</span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Right Column: Deep Inspection & Audit Player Card */}
          <div className="lg:col-span-8">
            {selectedItem ? (
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
                  {/* Photo & Bounding Box Inspection */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
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

                    {/* Compare Badges: Current YOLO vs VLM Suggestion */}
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

                        {/* VLM Suggestion Badge */}
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
                                onClick={handleFetchVLM}
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
                                onClick={handleApplySuggestion}
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

                  {/* Form: Corrected Text & Score */}
                  <div className="space-y-3 pt-2 border-t border-border">
                    <div className="space-y-1">
                      <label className="text-xs font-semibold text-foreground">
                        Nhãn Văn Bản Hiệu Chỉnh (Ground Truth Text) *
                      </label>
                      <input
                        type="text"
                        value={correctedText}
                        onChange={(e) => setCorrectedText(e.target.value)}
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
                          onChange={(e) => setAccuracyScore(parseFloat(e.target.value) || 0.95)}
                          className="h-8 w-full rounded-md border border-border bg-background px-3 font-mono text-xs focus:outline-none focus:ring-1 focus:ring-primary"
                        />
                      </div>

                      <div className="space-y-1">
                        <label className="text-xs font-medium text-foreground">Ghi chú đối soát</label>
                        <input
                          type="text"
                          value={reviewNotes}
                          onChange={(e) => setReviewNotes(e.target.value)}
                          placeholder="VD: Đã hiệu chỉnh theo VLM bóc tách ngữ cảnh..."
                          className="h-8 w-full rounded-md border border-border bg-background px-3 text-xs focus:outline-none focus:ring-1 focus:ring-primary"
                        />
                      </div>
                    </div>
                  </div>

                  {/* HTML5 Audio Player & Neural TTS Preview */}
                  <div className="p-3.5 rounded-xl border border-border bg-muted/20 space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-500/10 text-indigo-500">
                          <Volume2 className="h-4 w-4" />
                        </div>
                        <div>
                          <span className="text-xs font-semibold text-foreground">
                            One-Click Neural TTS Preview Player
                          </span>
                          <p className="text-[10px] text-muted-foreground font-mono">
                            Voice: vi-VN-HoaiMyNeural (Edge-TTS Fallback)
                          </p>
                        </div>
                      </div>

                      <Button
                        onClick={handlePreviewTTS}
                        disabled={isSynthesizingTTS || !correctedText.trim()}
                        size="sm"
                        variant="outline"
                        className="h-7 text-xs gap-1.5 cursor-pointer text-indigo-500 border-indigo-500/30 hover:bg-indigo-500/10"
                      >
                        {isSynthesizingTTS ? (
                          <Loader2 className="h-3 w-3 animate-spin" />
                        ) : (
                          <RefreshCw className="h-3 w-3" />
                        )}
                        <span>Nghe thử phát âm</span>
                      </Button>
                    </div>

                    {/* Audio Controller Bar */}
                    <div className="flex items-center gap-3 p-2 rounded-lg bg-background border border-border/80">
                      <Button
                        onClick={toggleAudio}
                        disabled={!previewAudioUrl}
                        size="icon"
                        variant="ghost"
                        className="h-8 w-8 text-primary cursor-pointer shrink-0"
                      >
                        {isPlayingAudio ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                      </Button>

                      <div className="flex-1 min-w-0">
                        <div className="h-2 rounded-full bg-muted overflow-hidden relative">
                          <div
                            className={`h-full bg-indigo-500 rounded-full ${
                              isPlayingAudio ? "animate-pulse w-full" : previewAudioUrl ? "w-full" : "w-0"
                            }`}
                          />
                        </div>
                      </div>

                      <span className="text-[11px] font-mono text-muted-foreground shrink-0">
                        {previewAudioUrl ? "Sẵn sàng" : "Chưa sinh audio"}
                      </span>

                      {/* Hidden Native Audio Element */}
                      <audio
                        ref={audioRef}
                        onEnded={() => setIsPlayingAudio(false)}
                        onError={() => setIsPlayingAudio(false)}
                        className="hidden"
                      />
                    </div>
                  </div>

                  {/* Commit Action Buttons */}
                  <div className="flex items-center justify-end gap-3 pt-2 border-t border-border">
                    <Button
                      onClick={handleSubmitReview}
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
            ) : null}
          </div>
        </div>
      )}
    </div>
  );
}
