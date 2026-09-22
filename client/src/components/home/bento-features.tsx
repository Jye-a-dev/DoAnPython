"use client";

import * as React from "react";
import {
  Volume2,
  Boxes,
  Mic,
  Zap,
  CheckCircle2,
  ScanLine,
  ArrowRight,
  Sparkles,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useVisualSearchStore } from "@/stores/visual-search-store";

function BentoFeaturesComponent() {
  const { openModal } = useVisualSearchStore();

  return (
    <section id="features" className="py-20 border-b border-border bg-background relative">
      {/* Background glow effects (Isolated in GPU sub-layer) */}
      <div className="ambient-glow-layer absolute inset-0 overflow-hidden">
        <div className="absolute top-1/2 left-1/4 -translate-y-1/2 w-96 h-96 bg-blue-600/10 rounded-full blur-[120px]" />
        <div className="absolute bottom-10 right-1/4 w-96 h-96 bg-violet-600/10 rounded-full blur-[120px]" />
      </div>

      <div className="container mx-auto px-4 sm:px-8 relative z-10 space-y-12">
        {/* Section Header */}
        <div className="text-center max-w-2xl mx-auto space-y-3">
          <Badge className="bg-indigo-500/10 text-indigo-500 dark:text-indigo-400 border border-indigo-500/20 px-3 py-1 text-xs">
            Kiến Trúc AI Toàn Diện
          </Badge>
          <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-foreground">
            Bộ Động Cơ Thị Giác & Giọng Nói{" "}
            <span className="bg-linear-to-r from-blue-500 via-indigo-600 to-violet-600 dark:from-blue-400 dark:via-indigo-400 dark:to-violet-400 bg-clip-text text-transparent">
              Thế Hệ Mới
            </span>
          </h2>
          <p className="text-sm sm:text-base text-muted-foreground">
            Hợp nhất mô hình phát hiện vật thể YOLO11, tổng hợp giọng nói Neural TTS và định tuyến kho hàng thông minh trong một nền tảng duy nhất.
          </p>
        </div>

        {/* Bento Grid 4 Blocks */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* BLOCK 1 (Large - Col Span 2): YOLO Vision Siêu Tốc */}
          <div className="md:col-span-2 rounded-3xl faux-glass-card p-6 sm:p-8 hover:border-blue-500/40 transition-[border-color,background-color] duration-200 relative overflow-hidden group shadow-sm">
            <div className="ambient-glow-layer absolute -right-20 -bottom-20 w-80 h-80 bg-blue-500/10 rounded-full blur-3xl group-hover:bg-blue-500/15" />

            <div className="flex flex-col h-full justify-between space-y-6">
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-blue-500/10 text-blue-500 dark:text-blue-400 border border-blue-500/20">
                    <ScanLine className="h-6 w-6" />
                  </div>
                  <div>
                    <span className="text-[11px] font-mono text-cyan-600 dark:text-cyan-400 uppercase tracking-wider">Vision Engine</span>
                    <h3 className="text-xl sm:text-2xl font-bold text-foreground">Thị giác máy tính YOLO Siêu tốc</h3>
                  </div>
                </div>
                <p className="text-sm text-muted-foreground max-w-xl leading-relaxed">
                  Trực tiếp phân tích và định vị đa vật thể với độ trễ dưới 0.3s. Khả năng nhận diện 80+ phân lớp chuẩn COCO và tự động gắn tọa độ Bounding Box chính xác từng pixel.
                </p>
              </div>

              {/* Multi Bounding Box Simulated Canvas */}
              <div className="relative rounded-2xl border border-border bg-muted/50 p-5 overflow-hidden">
                <div className="flex flex-wrap items-center justify-between gap-2 pb-4 border-b border-border text-xs text-muted-foreground font-mono">
                  <span className="flex items-center gap-2 text-cyan-600 dark:text-cyan-300">
                    <Zap className="h-3.5 w-3.5 text-cyan-500 dark:text-cyan-400" />
                    Inference: 42ms • FPS: 60 • NMS IoU: 0.45
                  </span>
                  <span className="text-muted-foreground/70">YOLO11x_Weights_FP16</span>
                </div>

                {/* Simulated Visual Bounding Boxes Showcase */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-4">
                  <div className="rounded-xl border border-cyan-500/40 bg-cyan-500/5 p-3 relative">
                    <div className="flex items-center justify-between text-[11px] font-bold text-cyan-600 dark:text-cyan-400">
                      <span>#laptop</span>
                      <span>98.6%</span>
                    </div>
                    <div className="mt-2 text-[10px] text-muted-foreground font-mono">
                      Box: [45, 80, 520, 390]
                    </div>
                    <span className="inline-block mt-2 text-[10px] font-semibold text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded">
                      ✓ Đã khớp kho
                    </span>
                  </div>

                  <div className="rounded-xl border border-indigo-500/40 bg-indigo-500/5 p-3 relative">
                    <div className="flex items-center justify-between text-[11px] font-bold text-indigo-600 dark:text-indigo-400">
                      <span>#cell phone</span>
                      <span>99.1%</span>
                    </div>
                    <div className="mt-2 text-[10px] text-muted-foreground font-mono">
                      Box: [540, 110, 680, 320]
                    </div>
                    <span className="inline-block mt-2 text-[10px] font-semibold text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded">
                      ✓ Đã khớp kho
                    </span>
                  </div>

                  <div className="rounded-xl border border-violet-500/40 bg-violet-500/5 p-3 relative">
                    <div className="flex items-center justify-between text-[11px] font-bold text-violet-600 dark:text-violet-400">
                      <span>#backpack</span>
                      <span>94.8%</span>
                    </div>
                    <div className="mt-2 text-[10px] text-muted-foreground font-mono">
                      Box: [120, 200, 340, 480]
                    </div>
                    <span className="inline-block mt-2 text-[10px] font-semibold text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded">
                      ✓ Đã khớp kho
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* BLOCK 2 (Medium): Thuyết minh Giọng nói Tự nhiên */}
          <div className="rounded-3xl faux-glass-card p-6 sm:p-8 hover:border-indigo-500/40 transition-[border-color,background-color] duration-200 relative overflow-hidden flex flex-col justify-between space-y-6 shadow-sm">
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-indigo-500/10 text-indigo-500 dark:text-indigo-400 border border-indigo-500/20">
                  <Volume2 className="h-6 w-6" />
                </div>
                <div>
                  <span className="text-[11px] font-mono text-indigo-500 dark:text-indigo-400 uppercase tracking-wider">Voice Synthesis</span>
                  <h3 className="text-xl font-bold text-foreground">Thuyết minh Giọng nói</h3>
                </div>
              </div>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Tự động diễn giải tóm tắt danh sách sản phẩm nhận diện bằng giọng đọc tiếng Việt mượt mà với âm sắc tự nhiên.
              </p>
            </div>

            {/* Neural TTS Interactive Visualizer Card */}
            <div className="rounded-2xl border border-border bg-muted/50 p-4 space-y-3">
              <div className="flex items-center justify-between text-xs">
                <span className="text-foreground font-medium">TTS Neural Voice vi-VN</span>
                <span className="text-cyan-600 dark:text-cyan-400 font-mono text-[11px]">Auto Play</span>
              </div>
              <div className="flex items-center justify-center gap-1.5 h-10 px-4 bg-indigo-500/10 rounded-xl border border-indigo-500/20">
                <span className="w-1 h-3 bg-cyan-500 rounded-full animate-sound-wave" style={{ animationDelay: "0ms" }} />
                <span className="w-1 h-6 bg-indigo-500 rounded-full animate-sound-wave" style={{ animationDelay: "100ms" }} />
                <span className="w-1 h-8 bg-violet-500 rounded-full animate-sound-wave" style={{ animationDelay: "200ms" }} />
                <span className="w-1 h-5 bg-cyan-500 rounded-full animate-sound-wave" style={{ animationDelay: "300ms" }} />
                <span className="w-1 h-7 bg-indigo-500 rounded-full animate-sound-wave" style={{ animationDelay: "400ms" }} />
                <span className="w-1 h-4 bg-violet-500 rounded-full animate-sound-wave" style={{ animationDelay: "500ms" }} />
                <span className="w-1 h-8 bg-cyan-500 rounded-full animate-sound-wave" style={{ animationDelay: "600ms" }} />
                <span className="w-1 h-5 bg-indigo-500 rounded-full animate-sound-wave" style={{ animationDelay: "700ms" }} />
              </div>
              <p className="text-[11px] text-muted-foreground italic">
                &ldquo;Hệ thống đã nhận diện được 1 laptop và 1 điện thoại với độ tin cậy cao.&rdquo;
              </p>
            </div>
          </div>

          {/* BLOCK 3 (Medium): Đối chiếu kho tức thì (Match-From-Scan) */}
          <div className="rounded-3xl faux-glass-card p-6 sm:p-8 hover:border-violet-500/40 transition-[border-color,background-color] duration-200 relative overflow-hidden flex flex-col justify-between space-y-6 shadow-sm">
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-violet-500/10 text-violet-500 dark:text-violet-400 border border-violet-500/20">
                  <Boxes className="h-6 w-6" />
                </div>
                <div>
                  <span className="text-[11px] font-mono text-violet-500 dark:text-violet-400 uppercase tracking-wider">Inventory Mapping</span>
                  <h3 className="text-xl font-bold text-foreground">Đối chiếu kho tức thì</h3>
                </div>
              </div>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Tự động ánh xạ kết quả thị giác sang mã SKU và số lượng tồn kho theo thời gian thực từ cơ sở dữ liệu.
              </p>
            </div>

            {/* Pipeline Visual Representation */}
            <div className="rounded-2xl border border-border bg-muted/50 p-4 space-y-2.5">
              <div className="flex items-center justify-between text-xs py-1 px-2 rounded-lg bg-background/90 border border-border/50">
                <span className="text-muted-foreground">Ảnh quét camera</span>
                <span className="text-foreground font-mono font-semibold">raw_image.jpg</span>
              </div>
              <div className="flex justify-center text-muted-foreground">
                <ArrowRight className="h-4 w-4 rotate-90" />
              </div>
              <div className="flex items-center justify-between text-xs py-1 px-2 rounded-lg bg-indigo-500/10 text-indigo-600 dark:text-indigo-300 border border-indigo-500/20">
                <span>Lớp nhãn YOLO</span>
                <span className="font-mono font-bold">#laptop (0.98)</span>
              </div>
              <div className="flex justify-center text-muted-foreground">
                <ArrowRight className="h-4 w-4 rotate-90" />
              </div>
              <div className="flex items-center justify-between text-xs py-1 px-2 rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-300 border border-emerald-500/20">
                <span>SKU & Tồn kho thực</span>
                <span className="font-mono font-bold">MB-14-M3 • Còn 12</span>
              </div>
            </div>
          </div>

          {/* BLOCK 4 (Long Bottom - Col Span 2): Chốt đơn không chạm */}
          <div className="md:col-span-2 lg:col-span-2 rounded-3xl faux-glass-card p-6 sm:p-8 hover:border-emerald-500/40 transition-[border-color,background-color] duration-200 relative overflow-hidden flex flex-col justify-between space-y-6 shadow-sm">
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-emerald-500/10 text-emerald-500 dark:text-emerald-400 border border-emerald-500/20">
                  <Mic className="h-6 w-6" />
                </div>
                <div>
                  <span className="text-[11px] font-mono text-emerald-500 dark:text-emerald-400 uppercase tracking-wider">Touchless Flow</span>
                  <h3 className="text-xl font-bold text-foreground">Chốt đơn không chạm & Xác nhận giọng nói</h3>
                </div>
              </div>
              <p className="text-sm text-muted-foreground leading-relaxed max-w-xl">
                Trải nghiệm mua sắm rảnh tay hoàn chỉnh. Chỉ cần 1-chạm xác nhận đơn hàng, hệ thống phát audio tóm tắt thanh toán và cập nhật giỏ hàng ngay lập tức.
              </p>
            </div>

            <div className="flex flex-wrap items-center justify-between gap-4 pt-2 border-t border-border">
              <div className="flex items-center gap-2 text-xs text-emerald-600 dark:text-emerald-300">
                <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                <span>Bảo mật JWT 2-Factor • Xác thực đơn hàng tự động</span>
              </div>
              <Button
                onClick={openModal}
                size="sm"
                className="gap-2 rounded-xl bg-linear-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-xs font-semibold cursor-pointer"
              >
                <Sparkles className="h-3.5 w-3.5" />
                <span>Trải nghiệm ngay</span>
              </Button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

export const BentoFeatures = React.memo(BentoFeaturesComponent);
