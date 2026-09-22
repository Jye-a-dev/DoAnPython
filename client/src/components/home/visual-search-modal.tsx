"use client";

import * as React from "react";
import Image from "next/image";
import {
  Camera,
  UploadCloud,
  X,
  Sparkles,
  Volume2,
  RefreshCw,
  ShoppingBag,
  CheckCircle2,
} from "lucide-react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useVisualSearchStore } from "@/stores/visual-search-store";
import { resolveMediaUrl } from "@/lib/api-client";
import { ProductCard } from "@/components/product/product-card";

export function VisualSearchModal() {
  const {
    isOpen,
    closeModal,
    previewUrl,
    isDetecting,
    isLoadingMatches,
    detectionResult,
    matchedProducts,
    audioUrl,
    uploadAndDetect,
    reset,
  } = useVisualSearchStore();

  const fileInputRef = React.useRef<HTMLInputElement | null>(null);
  const [isDragOver, setIsDragOver] = React.useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      uploadAndDetect(file);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file) {
      uploadAndDetect(file);
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  const handleReset = () => {
    reset();
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && closeModal()}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto p-6 z-50">
        <DialogHeader className="flex flex-row items-center justify-between border-b pb-4">
          <DialogTitle className="flex items-center gap-2 text-xl font-bold">
            <Sparkles className="h-5 w-5 text-primary" />
            <span>AI Camera-to-Shop Visual Search</span>
          </DialogTitle>
          <Button variant="ghost" size="icon" onClick={closeModal} className="h-8 w-8 rounded-full">
            <X className="h-4 w-4" />
          </Button>
        </DialogHeader>

        {/* State 1: Image Upload / Dropzone */}
        {!previewUrl && !isDetecting && (
          <div
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onClick={() => fileInputRef.current?.click()}
            className={`cursor-pointer rounded-2xl border-2 border-dashed p-10 text-center transition-all ${
              isDragOver
                ? "border-primary bg-primary/10 scale-[0.99]"
                : "border-border hover:border-primary/50 hover:bg-muted/30"
            }`}
          >
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              accept="image/jpeg,image/png,image/webp"
              className="hidden"
            />
            <div className="flex flex-col items-center justify-center space-y-4">
              <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10 text-primary">
                <UploadCloud className="h-8 w-8" />
              </div>
              <div className="space-y-1">
                <p className="text-base font-semibold text-foreground">
                  Kéo thả ảnh vào đây hoặc bấm để tải lên
                </p>
                <p className="text-xs text-muted-foreground">
                  Hỗ trợ định dạng JPG, PNG, WEBP (Tối đa 15MB)
                </p>
              </div>
              <Button size="sm" variant="outline" className="gap-2">
                <Camera className="h-4 w-4" />
                Chọn tệp từ thiết bị
              </Button>
            </div>
          </div>
        )}

        {/* State 2: Processing Skeleton */}
        {isDetecting && (
          <div className="space-y-6 py-8">
            <div className="flex flex-col items-center justify-center space-y-3 text-center">
              <RefreshCw className="h-8 w-8 animate-spin text-primary" />
              <p className="font-semibold text-base">Đang truyền tải đến YOLO Model & AI Pipeline...</p>
              <p className="text-xs text-muted-foreground">
                Đang nhận diện bounding box, tổng hợp tóm tắt và tạo giọng đọc tiếng Việt.
              </p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Skeleton className="aspect-square w-full rounded-2xl" />
              <div className="space-y-4">
                <Skeleton className="h-8 w-3/4 rounded-md" />
                <Skeleton className="h-20 w-full rounded-md" />
                <Skeleton className="h-10 w-full rounded-md" />
                <Skeleton className="h-32 w-full rounded-md" />
              </div>
            </div>
          </div>
        )}

        {/* State 3: Detection Completed Result */}
        {detectionResult && (
          <div className="space-y-6 pt-2">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-start">
              {/* Left Column: Annotated Image */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Ảnh Nhận Diện Bounding Box
                  </span>
                  <Badge variant="outline" className="text-[11px]">
                    {detectionResult.objects?.length || 0} vật thể
                  </Badge>
                </div>
                <div className="relative aspect-square w-full overflow-hidden rounded-2xl border bg-black/5">
                  <Image
                    src={
                      resolveMediaUrl(
                        detectionResult.annotated_image_url || detectionResult.image_url
                      ) || previewUrl!
                    }
                    alt="Detected Objects"
                    fill
                    sizes="(max-width: 768px) 100vw, 50vw"
                    className="object-contain"
                  />
                </div>
              </div>

              {/* Right Column: Vietnamese Summary & Voice Audio */}
              <div className="space-y-4 flex flex-col justify-between">
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                    <h3 className="font-bold text-lg">Kết Quả Phân Tích AI</h3>
                  </div>

                  {/* Summary Text */}
                  <div className="rounded-xl border bg-muted/30 p-3.5 space-y-1">
                    <span className="text-xs font-semibold text-primary">Tóm tắt tiếng Việt:</span>
                    <p className="text-sm text-foreground leading-relaxed">
                      {detectionResult.summary || "Đã nhận diện thành công các vật thể trong khung hình."}
                    </p>
                  </div>

                  {/* Audio Player */}
                  {audioUrl && (
                    <div className="rounded-xl border border-primary/20 bg-primary/5 p-3.5 space-y-2">
                      <div className="flex items-center gap-2 text-xs font-semibold text-primary">
                        <Volume2 className="h-4 w-4" />
                        <span>Giọng đọc xác nhận AI (TTS):</span>
                      </div>
                      <audio controls autoPlay src={audioUrl} className="w-full h-9" />
                    </div>
                  )}

                  {/* Detected Object Badges */}
                  <div className="space-y-2">
                    <span className="text-xs font-semibold text-muted-foreground">Vật thể định vị:</span>
                    <div className="flex flex-wrap gap-1.5">
                      {detectionResult.objects?.map((obj, idx) => (
                        <Badge key={idx} variant="secondary" className="text-xs gap-1 py-1">
                          <span className="font-semibold">{obj.label_vi || obj.name}</span>
                          <span className="text-muted-foreground text-[10px]">
                            ({(obj.confidence * 100).toFixed(0)}%)
                          </span>
                        </Badge>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Reset / Scan again CTA */}
                <div className="pt-4 border-t flex items-center justify-end gap-3">
                  <Button variant="outline" size="sm" onClick={handleReset} className="gap-1.5">
                    <RefreshCw className="h-4 w-4" />
                    Quét ảnh khác
                  </Button>
                </div>
              </div>
            </div>

            {/* Bottom Row: Matched Store Products */}
            <div className="border-t pt-6 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <ShoppingBag className="h-5 w-5 text-primary" />
                  <h4 className="font-bold text-base">Sản Phẩm Khớp Trong Kho Hàng</h4>
                </div>
                <span className="text-xs text-muted-foreground">
                  {matchedProducts.length} sản phẩm tương ứng
                </span>
              </div>

              {isLoadingMatches ? (
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                  <Skeleton className="h-48 rounded-xl" />
                  <Skeleton className="h-48 rounded-xl" />
                  <Skeleton className="h-48 rounded-xl" />
                </div>
              ) : matchedProducts.length > 0 ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
                  {matchedProducts.map((product) => (
                    <ProductCard key={product.id} product={product} highlightMatch={true} />
                  ))}
                </div>
              ) : (
                <div className="rounded-xl border border-dashed p-6 text-center text-muted-foreground text-sm">
                  Không tìm thấy sản phẩm có sẵn trong kho tương ứng với các lớp nhãn AI vừa nhận diện.
                </div>
              )}
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

