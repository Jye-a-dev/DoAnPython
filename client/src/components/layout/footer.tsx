import * as React from "react";
import Link from "next/link";
import { Camera, Globe, ShieldCheck, Cpu, Radio, Sparkles } from "lucide-react";

function GithubIcon(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg
      viewBox="0 0 24 24"
      width="16"
      height="16"
      stroke="currentColor"
      strokeWidth="2"
      fill="none"
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      <path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4" />
      <path d="M9 18c-4.51 2-5-2-7-2" />
    </svg>
  );
}

export function Footer() {
  return (
    <footer className="w-full border-t border-border bg-muted/30 text-muted-foreground">
      <div className="container mx-auto px-4 sm:px-8 py-16 space-y-12">
        {/* 4-Column Layout */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-10">
          {/* Column 1: Brand & Identity */}
          <div className="space-y-4">
            <Link href="/" className="flex items-center gap-2.5">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-linear-to-br from-blue-500 to-indigo-600 text-white font-bold shadow-md shadow-blue-500/20">
                <Camera className="h-5 w-5" />
              </div>
              <span className="font-extrabold text-lg tracking-tight text-foreground">
                Visual AI Store
              </span>
            </Link>
            <p className="text-xs text-muted-foreground leading-relaxed">
              Nền tảng thương mại điện tử công nghệ cao kết hợp mô hình thị giác máy tính YOLO11, tổng hợp giọng nói Neural TTS và luồng đối chiếu kho tức thì.
            </p>
            <div className="flex items-center gap-2 text-[11px] text-cyan-600 dark:text-cyan-400 font-mono">
              <ShieldCheck className="h-4 w-4" />
              <span>Camera-to-Shop Protocol v2.0</span>
            </div>
          </div>

          {/* Column 2: Khám Phá & Tiện Ích */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-foreground">
              Khám Phá & Tiện Ích
            </h4>
            <ul className="space-y-2 text-xs text-muted-foreground">
              <li>
                <Link href="#hero" className="hover:text-primary transition-colors">
                  Quét Ảnh AI (Live Scanner)
                </Link>
              </li>
              <li>
                <Link href="#features" className="hover:text-primary transition-colors">
                  Cách Hoạt Động (Bento Grid)
                </Link>
              </li>
              <li>
                <Link href="#catalog-section" className="hover:text-primary transition-colors">
                  Kho Hàng Thông Minh
                </Link>
              </li>
              <li>
                <Link href="#tech-pipeline" className="hover:text-primary transition-colors">
                  Kiến Trúc Microservice
                </Link>
              </li>
              <li>
                <Link href="/login" className="hover:text-primary transition-colors">
                  Tài Khoản & Quản Lý Giỏ Hàng
                </Link>
              </li>
            </ul>
          </div>

          {/* Column 3: Công Nghệ & Pipeline */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-foreground">
              Công Nghệ & Pipeline
            </h4>
            <ul className="space-y-2 text-xs text-muted-foreground font-mono">
              <li className="flex items-center gap-1.5">
                <Cpu className="h-3 w-3 text-blue-500" />
                <span>YOLO11x Detection Engine</span>
              </li>
              <li className="flex items-center gap-1.5">
                <Radio className="h-3 w-3 text-indigo-500" />
                <span>Edge Neural TTS (vi-VN)</span>
              </li>
              <li className="flex items-center gap-1.5">
                <Sparkles className="h-3 w-3 text-cyan-500" />
                <span>SQLite BLOB Media Stream</span>
              </li>
              <li className="flex items-center gap-1.5">
                <Globe className="h-3 w-3 text-violet-500" />
                <span>FastAPI Gateway & Next.js 15</span>
              </li>
            </ul>
          </div>

          {/* Column 4: Trạng Thái Hệ Thống & Hỗ Trợ */}
          <div className="space-y-4">
            <h4 className="text-xs font-bold uppercase tracking-wider text-foreground">
              Trạng Thái Hệ Thống
            </h4>

            {/* Pulsing Beacon Operational Badge */}
            <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/10 p-3.5 space-y-1.5 backdrop-blur-md">
              <div className="flex items-center gap-2">
                <span className="relative flex h-2.5 w-2.5">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                  <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500" />
                </span>
                <span className="text-xs font-bold text-emerald-600 dark:text-emerald-300">
                  Pipeline & Gateway Operational
                </span>
              </div>
              <p className="text-[11px] text-muted-foreground">
                Uptime: 99.98% • Latency Gateway: ~38ms
              </p>
            </div>

            <div className="flex items-center gap-3 text-xs text-muted-foreground">
              <Link
                href="https://github.com/Jye-a-dev/template_next_client"
                target="_blank"
                className="hover:text-foreground flex items-center gap-1.5 transition-colors"
              >
                <GithubIcon className="h-4 w-4" />
                <span>Mã Nguồn Mở</span>
              </Link>
            </div>
          </div>
        </div>

        {/* Bottom Bar: Copyright & Compliance */}
        <div className="pt-8 border-t border-border flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-muted-foreground">
          <p>
            © {new Date().getFullYear()} Visual AI Store. Bản quyền thuộc về kiến trúc sư giải pháp.
          </p>
          <div className="flex items-center gap-6">
            <span className="hover:text-foreground cursor-pointer transition-colors">Chính Sách Bảo Mật</span>
            <span className="hover:text-foreground cursor-pointer transition-colors">Điều Khoản Dịch Vụ</span>
            <span className="hover:text-foreground cursor-pointer transition-colors">Tài Liệu API</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
