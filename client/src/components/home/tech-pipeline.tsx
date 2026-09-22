import * as React from "react";
import { Radio, Cpu, Database, Layers } from "lucide-react";

export function TechPipeline() {
  return (
    <section id="tech-pipeline" className="py-16 border-b border-border bg-muted/30 relative">
      <div className="container mx-auto px-4 sm:px-8 space-y-8">
        <div className="text-center max-w-xl mx-auto space-y-2">
          <span className="text-[11px] font-mono text-cyan-500 dark:text-cyan-400 uppercase tracking-widest">
            Live Pipeline Architecture
          </span>
          <h3 className="text-2xl sm:text-3xl font-extrabold text-foreground">
            Luồng Xử Lý Thị Giác Khép Kín
          </h3>
          <p className="text-xs sm:text-sm text-muted-foreground">
            Kiến trúc microservice xử lý dữ liệu nhị phân BLOB và đồng bộ thời gian thực
          </p>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="rounded-2xl border border-border bg-card/90 p-4 text-center space-y-2 shadow-xs">
            <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-xl bg-blue-500/10 text-blue-500 dark:text-blue-400 border border-blue-500/20">
              <Radio className="h-5 w-5" />
            </div>
            <h4 className="text-xs font-bold text-foreground">1. Edge Capture</h4>
            <p className="text-[11px] text-muted-foreground">Camera 60fps & Web Streaming API</p>
          </div>

          <div className="rounded-2xl border border-border bg-card/90 p-4 text-center space-y-2 shadow-xs">
            <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-500/10 text-cyan-500 dark:text-cyan-400 border border-cyan-500/20">
              <Cpu className="h-5 w-5" />
            </div>
            <h4 className="text-xs font-bold text-foreground">2. YOLO11 Inference</h4>
            <p className="text-[11px] text-muted-foreground">Định vị Bounding Box & 80+ phân lớp</p>
          </div>

          <div className="rounded-2xl border border-border bg-card/90 p-4 text-center space-y-2 shadow-xs">
            <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-500/10 text-indigo-500 dark:text-indigo-400 border border-indigo-500/20">
              <Database className="h-5 w-5" />
            </div>
            <h4 className="text-xs font-bold text-foreground">3. BLOB Storage</h4>
            <p className="text-[11px] text-muted-foreground">Lưu nhị phân SQLite & Endpoint Streaming</p>
          </div>

          <div className="rounded-2xl border border-border bg-card/90 p-4 text-center space-y-2 shadow-xs">
            <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-500 dark:text-emerald-400 border border-emerald-500/20">
              <Layers className="h-5 w-5" />
            </div>
            <h4 className="text-xs font-bold text-foreground">4. Neural Voice & Stock</h4>
            <p className="text-[11px] text-muted-foreground">Edge TTS vi-VN & Khớp tồn kho tức thì</p>
          </div>
        </div>
      </div>
    </section>
  );
}

