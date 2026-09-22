"use client";

import { Camera, Sparkles, Volume2, ShoppingBag, ArrowDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useVisualSearchStore } from "@/hooks/use-visual-search";

export function HeroSection() {
  const { openModal } = useVisualSearchStore();

  const scrollToProducts = () => {
    const el = document.getElementById("catalog-section");
    if (el) {
      el.scrollIntoView({ behavior: "smooth" });
    }
  };

  return (
    <section className="relative overflow-hidden py-16 sm:py-24 border-b border-border/40 bg-gradient-to-b from-primary/5 via-background to-background">
      <div className="container mx-auto px-4 sm:px-8 text-center max-w-4xl space-y-6">
        {/* Sub-badge */}
        <div className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/10 px-4 py-1.5 text-xs font-semibold text-primary">
          <Sparkles className="h-3.5 w-3.5" />
          <span>Công Nghệ AI Visual Search & Text-To-Speech Mới Nhất</span>
        </div>

        {/* Main Headline */}
        <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-foreground leading-[1.15]">
          Mua Sắm Thông Minh Cùng{" "}
          <span className="bg-gradient-to-r from-blue-600 via-indigo-600 to-primary bg-clip-text text-transparent">
            Thị Giác AI
          </span>
        </h1>

        {/* Description */}
        <p className="text-base sm:text-lg text-muted-foreground max-w-2xl mx-auto leading-relaxed">
          Chụp ảnh hoặc kéo thả bất kỳ vật thể nào xung quanh bạn. Hệ thống YOLO AI sẽ phân tích bounding box tức thì,
          phát giọng đọc tóm tắt thông minh và gợi ý chính xác sản phẩm có sẵn trong kho hàng.
        </p>

        {/* CTA Buttons */}
        <div className="flex flex-wrap items-center justify-center gap-4 pt-2">
          <Button
            size="lg"
            onClick={openModal}
            className="gap-2.5 rounded-full px-8 text-base shadow-lg shadow-primary/25 bg-gradient-to-r from-primary to-blue-600 hover:opacity-95"
          >
            <Camera className="h-5 w-5" />
            <span>Quét Ảnh Nhận Diện Ngay</span>
          </Button>

          <Button
            variant="outline"
            size="lg"
            onClick={scrollToProducts}
            className="gap-2 rounded-full px-6 text-base"
          >
            <span>Khám Phá Cửa Hàng</span>
            <ArrowDown className="h-4 w-4" />
          </Button>
        </div>

        {/* Highlight Stats / Badges */}
        <div className="pt-8 grid grid-cols-1 sm:grid-cols-3 gap-4 max-w-2xl mx-auto">
          <div className="flex items-center gap-3 p-3 rounded-xl border border-border/50 bg-card/60 backdrop-blur-xs text-left">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-blue-500/10 text-blue-500">
              <Camera className="h-5 w-5" />
            </div>
            <div>
              <p className="text-xs font-semibold">YOLO Detection</p>
              <p className="text-[11px] text-muted-foreground">Nhận diện vật thể 80+ lớp</p>
            </div>
          </div>

          <div className="flex items-center gap-3 p-3 rounded-xl border border-border/50 bg-card/60 backdrop-blur-xs text-left">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-indigo-500/10 text-indigo-500">
              <Volume2 className="h-5 w-5" />
            </div>
            <div>
              <p className="text-xs font-semibold">Giọng Đọc AI TTS</p>
              <p className="text-[11px] text-muted-foreground">Thuyết minh tiếng Việt mượt mà</p>
            </div>
          </div>

          <div className="flex items-center gap-3 p-3 rounded-xl border border-border/50 bg-card/60 backdrop-blur-xs text-left">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-500">
              <ShoppingBag className="h-5 w-5" />
            </div>
            <div>
              <p className="text-xs font-semibold">Match-From-Scan</p>
              <p className="text-[11px] text-muted-foreground">Khớp kho hàng chuẩn xác</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

