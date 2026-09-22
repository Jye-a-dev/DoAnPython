"use client";

import * as React from "react";
import Image from "next/image";
import {
  Camera,
  Sparkles,
  ArrowDown,
  Volume2,
  Zap,
  Star,
  ShoppingBag,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { useVisualSearchStore } from "@/stores/visual-search-store";
import { resolveMediaUrl } from "@/lib/api-client";

function HeroSectionComponent() {
  const { openModal } = useVisualSearchStore();

  const scrollToProducts = () => {
    const el = document.getElementById("catalog-section");
    if (el) {
      el.scrollIntoView({ behavior: "smooth" });
    }
  };

  // Sample mockup image resolved through API client or high-res tech fallback
  const sampleMockupImage = React.useMemo(() => {
    return resolveMediaUrl(
      "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=800&auto=format&fit=crop&q=85"
    );
  }, []);

  return (
    <section
      id="hero"
      className="relative overflow-hidden pt-12 pb-20 lg:pt-20 lg:pb-28 border-b border-border bg-background"
    >
      {/* 1. Atmospheric Ambient Spotlight Glow (Isolated in GPU sub-layer) */}
      <div className="ambient-glow-layer absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 left-1/2 -translate-x-1/2 h-200 w-200 max-w-full rounded-full bg-linear-to-tr from-indigo-600/20 via-blue-500/15 to-violet-600/20 blur-[130px] opacity-30 dark:opacity-70" />
        <div className="absolute top-1/3 -right-20 h-72 w-72 rounded-full bg-cyan-500/10 blur-[100px]" />
        <div className="absolute bottom-0 -left-20 h-72 w-72 rounded-full bg-indigo-500/10 blur-[100px]" />
      </div>

      <div className="container mx-auto px-4 sm:px-8 relative z-10">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-8 items-center">
          {/* LEFT COLUMN: Headline, Badges, CTAs, Social Proof (7 Cols) */}
          <div className="lg:col-span-7 flex flex-col items-start text-left space-y-6">
            {/* Glowing Pill Badge */}
            <div className="inline-flex items-center gap-2 rounded-full border border-cyan-500/30 bg-cyan-500/10 px-3.5 py-1.5 text-xs font-semibold text-cyan-600 dark:text-cyan-300 shadow-xs">
              <Zap className="h-3.5 w-3.5 text-cyan-500 dark:text-cyan-400 animate-pulse" />
              <span>⚡ YOLO11 Vision & Neural Voice Engine v2.0</span>
            </div>

            {/* Main Headline H1 */}
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black tracking-tight text-foreground leading-[1.12]">
              Mua Sắm Thông Minh Cùng{" "}
              <span className="bg-linear-to-r from-blue-500 via-indigo-600 to-violet-600 dark:from-blue-400 dark:via-indigo-400 dark:to-violet-400 bg-clip-text text-transparent">
                Thị Giác AI
              </span>
            </h1>

            {/* Subtitle */}
            <p className="text-base sm:text-lg text-muted-foreground max-w-xl leading-relaxed font-normal">
              Chụp ảnh hoặc tải lên bất kỳ vật phẩm nào xung quanh bạn. Mô hình YOLO AI sẽ phân tích bounding box tức thì dưới 0.3s, tự động thuyết minh bằng giọng nói AI và đối chiếu kho hàng chính xác.
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-wrap items-center gap-4 pt-2">
              <Button
                size="lg"
                onClick={openModal}
                className="relative group overflow-hidden gap-2.5 rounded-full px-7 py-6 text-sm sm:text-base font-semibold text-white bg-linear-to-r from-blue-600 via-indigo-600 to-violet-600 hover:from-blue-500 hover:to-violet-500 shadow-xl shadow-indigo-600/30 ring-2 ring-cyan-400/40 hover:ring-cyan-300/80 transition-all cursor-pointer"
              >
                <span className="absolute -inset-x-20 top-0 h-full w-20 bg-white/20 skew-x-12 -translate-x-full group-hover:translate-x-100 transition-transform duration-1000" />
                <Camera className="h-5 w-5 text-cyan-300" />
                <span>Quét Ảnh Nhận Diện Ngay</span>
              </Button>

              <Button
                variant="outline"
                size="lg"
                onClick={scrollToProducts}
                className="gap-2 rounded-full px-6 py-6 text-sm sm:text-base font-medium border-border bg-card/90 text-foreground hover:bg-muted transition-colors cursor-pointer"
              >
                <span>Xem Catalog Sản Phẩm</span>
                <ArrowDown className="h-4 w-4 text-muted-foreground group-hover:translate-y-0.5 transition-transform" />
              </Button>
            </div>

            {/* Social Proof Strip */}
            <div className="pt-4 flex flex-wrap items-center gap-4 text-xs text-muted-foreground border-t border-border w-full">
              <div className="flex -space-x-2">
                <div className="relative h-8 w-8 rounded-full border-2 border-background overflow-hidden bg-muted">
                  <Image src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100&auto=format&fit=crop&q=80" alt="Avatar 1" fill className="object-cover" />
                </div>
                <div className="relative h-8 w-8 rounded-full border-2 border-background overflow-hidden bg-muted">
                  <Image src="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&auto=format&fit=crop&q=80" alt="Avatar 2" fill className="object-cover" />
                </div>
                <div className="relative h-8 w-8 rounded-full border-2 border-background overflow-hidden bg-muted">
                  <Image src="https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=100&auto=format&fit=crop&q=80" alt="Avatar 3" fill className="object-cover" />
                </div>
                <div className="relative h-8 w-8 rounded-full border-2 border-background overflow-hidden bg-linear-to-r from-blue-600 to-indigo-600 flex items-center justify-center text-[10px] font-bold text-white">
                  +5k
                </div>
              </div>

              <div className="flex items-center gap-1.5">
                <div className="flex text-amber-400">
                  <Star className="h-3.5 w-3.5 fill-current" />
                  <Star className="h-3.5 w-3.5 fill-current" />
                  <Star className="h-3.5 w-3.5 fill-current" />
                  <Star className="h-3.5 w-3.5 fill-current" />
                  <Star className="h-3.5 w-3.5 fill-current" />
                </div>
                <span className="font-semibold text-foreground">4.9/5</span>
                <span>• Đã nhận diện hơn <strong className="text-cyan-600 dark:text-cyan-300">50,000+</strong> vật thể hôm nay</span>
              </div>
            </div>
          </div>

          {/* RIGHT COLUMN: Interactive Mockup Showcase (5 Cols) */}
          <div className="lg:col-span-5 relative flex items-center justify-center">
            {/* Glowing Backdrop for Mockup */}
            <div className="ambient-glow-layer absolute inset-0 bg-linear-to-r from-blue-500/20 to-violet-500/20 rounded-3xl blur-2xl -z-10" />

            {/* Floating Camera Scan Glass Card */}
            <div className="relative w-full max-w-md rounded-3xl border border-border bg-card/95 p-4 shadow-2xl ring-1 ring-border/50 text-card-foreground">
              {/* Header Bar of Mockup */}
              <div className="flex items-center justify-between pb-3 px-1 border-b border-border text-xs">
                <div className="flex items-center gap-2">
                  <span className="h-2.5 w-2.5 rounded-full bg-red-500/80 inline-block" />
                  <span className="h-2.5 w-2.5 rounded-full bg-amber-500/80 inline-block" />
                  <span className="h-2.5 w-2.5 rounded-full bg-emerald-500/80 inline-block" />
                  <span className="font-mono text-[11px] text-muted-foreground ml-1">AI_CAMERA_STREAM_LIVE</span>
                </div>
                <span className="inline-flex items-center gap-1 font-mono text-[10px] text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-ping" />
                  REC 60FPS
                </span>
              </div>

              {/* Viewport with Sample Image & Bounding Box */}
              <div className="relative aspect-4/3 w-full mt-3 overflow-hidden rounded-2xl border border-border bg-muted">
                <Image
                  src={sampleMockupImage}
                  alt="AI Scan Object Preview"
                  fill
                  sizes="(max-width: 768px) 100vw, 400px"
                  className="object-cover opacity-90"
                  priority
                />

                {/* Laser Scan Beam (Vertical Sweep with GPU Transform) */}
                <div className="pointer-events-none absolute inset-x-0 top-0 h-1 bg-linear-to-r from-transparent via-cyan-400 to-transparent shadow-[0_0_15px_#22d3ee] animate-scan-beam z-20" />

                {/* Simulated Neon Cyan Bounding Box with Corner Reticles */}
                <div className="absolute top-[18%] left-[14%] w-[72%] h-[68%] rounded border-2 border-cyan-400/90 shadow-[0_0_20px_rgba(34,211,238,0.35)] z-10 pointer-events-none">
                  {/* 4 Corner Reticle Accents */}
                  <span className="absolute -top-1 -left-1 w-3 h-3 border-t-2 border-l-2 border-white" />
                  <span className="absolute -top-1 -right-1 w-3 h-3 border-t-2 border-r-2 border-white" />
                  <span className="absolute -bottom-1 -left-1 w-3 h-3 border-b-2 border-l-2 border-white" />
                  <span className="absolute -bottom-1 -right-1 w-3 h-3 border-b-2 border-r-2 border-white" />

                  {/* Anchored AI Tag */}
                  <div className="absolute -top-7 left-0 flex items-center gap-1.5 rounded-md bg-cyan-500/95 px-2 py-0.5 text-[11px] font-bold text-white shadow-md">
                    <Sparkles className="h-3 w-3" />
                    <span>#laptop [98.6%]</span>
                  </div>

                  {/* Secondary Detected Tag */}
                  <div className="absolute -bottom-6 right-0 flex items-center gap-1 rounded bg-indigo-600/95 px-1.5 py-0.5 text-[10px] font-semibold text-white shadow-xs">
                    <span>SKU: MB-PRO-14</span>
                  </div>
                </div>

                {/* Top-Right Telemetry Chip */}
                <div className="absolute top-2.5 right-2.5 z-20 flex flex-col gap-1 items-end">
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-background/95 text-cyan-600 dark:text-cyan-300 border border-cyan-500/30">
                    ⚡ Latency: 42ms
                  </span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-background/95 text-indigo-600 dark:text-indigo-300 border border-indigo-500/30">
                    🎯 YOLO11x: Active
                  </span>
                </div>
              </div>

              {/* Bottom Mini Widget: Audio Waveform & Instant Match Action */}
              <div className="mt-3 rounded-2xl border border-border bg-muted/50 p-3 space-y-2.5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-500/10 text-indigo-600 dark:text-indigo-400">
                      <Volume2 className="h-4 w-4" />
                    </div>
                    <div>
                      <p className="text-[11px] font-semibold text-foreground">Neural TTS Thuyết Minh</p>
                      <p className="text-[10px] text-muted-foreground">Giọng đọc tiếng Việt tự nhiên</p>
                    </div>
                  </div>

                  {/* Waveform Bars Animation */}
                  <div className="flex items-center gap-1 h-5 px-2">
                    <span className="w-1 h-3 bg-cyan-500 rounded-full animate-sound-wave" style={{ animationDelay: "0ms" }} />
                    <span className="w-1 h-5 bg-indigo-500 rounded-full animate-sound-wave" style={{ animationDelay: "150ms" }} />
                    <span className="w-1 h-2 bg-violet-500 rounded-full animate-sound-wave" style={{ animationDelay: "300ms" }} />
                    <span className="w-1 h-4 bg-cyan-500 rounded-full animate-sound-wave" style={{ animationDelay: "450ms" }} />
                    <span className="w-1 h-3 bg-indigo-500 rounded-full animate-sound-wave" style={{ animationDelay: "600ms" }} />
                  </div>
                </div>

                {/* Product Match Info & Add Action */}
                <div className="flex items-center justify-between pt-1 border-t border-border/50">
                  <div>
                    <span className="text-[10px] text-muted-foreground block">Sản phẩm khớp kho</span>
                    <span className="text-xs font-bold text-foreground">Apple MacBook Pro 14 M3</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-extrabold text-cyan-600 dark:text-cyan-400">29.990.000 đ</span>
                    <Button
                      size="sm"
                      onClick={openModal}
                      className="h-7 px-2.5 rounded-lg text-[11px] font-medium bg-blue-600 hover:bg-blue-500 text-white gap-1 cursor-pointer"
                    >
                      <ShoppingBag className="h-3 w-3" />
                      Quét thử
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

export const HeroSection = React.memo(HeroSectionComponent);
