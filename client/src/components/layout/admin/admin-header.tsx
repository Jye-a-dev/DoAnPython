"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  ExternalLink,
  ChevronRight,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { ThemeToggle } from "@/components/layout/theme-toggle";
import { useAuthStore } from "@/stores/auth-store";
import { useAdminStore } from "@/stores/admin-store";
import { AdminCopilotModal } from "@/components/admin/admin-copilot-modal";

export function AdminHeader() {
  const pathname = usePathname();
  const user = useAuthStore((s) => s.user);
  const { openCopilot } = useAdminStore();

  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        openCopilot();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [openCopilot]);

  const getBreadcrumbTitle = (path: string) => {
    if (path === "/admin") return "Dashboard Tổng Quan";
    if (path.startsWith("/admin/products")) return "Kho Hàng & SKU";
    if (path.startsWith("/admin/records")) return "Nhật Ký Nhận Diện";
    if (path.startsWith("/admin/reviews")) return "Kiểm Duyệt AI & OCR";
    if (path.startsWith("/admin/users")) return "Quản Lý Người Dùng";
    if (path.startsWith("/admin/settings")) return "Cấu Hình Gateway";
    return "Quản Trị";
  };

  return (
    <>
      <header className="sticky top-0 z-20 flex h-16 w-full items-center justify-between border-b border-border bg-background/85 px-4 sm:px-6 backdrop-blur-md">
        {/* Breadcrumbs */}
        <div className="flex items-center gap-2 text-xs">
          <Link href="/admin" className="text-muted-foreground hover:text-foreground font-medium">
            Admin
          </Link>
          <ChevronRight className="h-3.5 w-3.5 text-muted-foreground" />
          <span className="font-semibold text-foreground">{getBreadcrumbTitle(pathname)}</span>
        </div>

        {/* AI Copilot & Natural Language Command Palette Trigger */}
        <div className="hidden md:flex items-center relative w-72 max-w-sm">
          <button
            onClick={openCopilot}
            className="flex items-center justify-between h-8 w-full rounded-full border border-border bg-muted/40 px-3 text-xs text-muted-foreground hover:text-foreground hover:border-primary/50 transition-colors cursor-pointer"
          >
            <div className="flex items-center gap-2">
              <Sparkles className="h-3.5 w-3.5 text-indigo-500" />
              <span>Hỏi Admin Copilot...</span>
            </div>
            <kbd className="hidden lg:inline-flex items-center gap-0.5 rounded border border-border bg-muted px-1.5 font-mono text-[10px] text-muted-foreground">
              <span>⌘</span>K
            </kbd>
          </button>
        </div>

        {/* Controls & Environment Status */}
        <div className="flex items-center gap-2 sm:gap-3">
          <Button
            onClick={openCopilot}
            variant="outline"
            size="sm"
            className="md:hidden h-8 w-8 p-0 text-indigo-500 cursor-pointer"
          >
            <Sparkles className="h-4 w-4" />
          </Button>

          <Badge
            variant="destructive"
            className="hidden sm:inline-flex items-center gap-1.5 px-2.5 py-1 text-[11px] font-semibold bg-red-500/15 text-red-500 dark:text-red-400 border border-red-500/30"
          >
            <span className="h-1.5 w-1.5 rounded-full bg-red-500 animate-pulse" />
            QUẢN TRỊ VIÊN
          </Badge>

          <Button
            variant="ghost"
            size="sm"
            asChild
            className="h-8 gap-1.5 text-xs text-muted-foreground hover:text-foreground"
          >
            <Link href="/" target="_blank">
              <span className="hidden sm:inline">Về Giao Diện Shop</span>
              <ExternalLink className="h-3.5 w-3.5" />
            </Link>
          </Button>

          <ThemeToggle />

          {user && (
            <div className="flex items-center gap-2 pl-2 border-l border-border">
              <Avatar className="h-8 w-8 ring-1 ring-border">
                <AvatarImage src={user.avatar_url || ""} />
                <AvatarFallback className="bg-primary/10 text-primary text-xs font-bold">
                  {(user.full_name || user.email).charAt(0).toUpperCase()}
                </AvatarFallback>
              </Avatar>
              <div className="hidden xl:flex flex-col text-left">
                <span className="text-xs font-semibold leading-none truncate max-w-30">
                  {user.full_name || "Admin"}
                </span>
                <span className="text-[10px] text-muted-foreground leading-none mt-1 truncate max-w-30">
                  {user.email}
                </span>
              </div>
            </div>
          )}
        </div>
      </header>

      {/* ⌘K AI Copilot Dialog */}
      <AdminCopilotModal />
    </>
  );
}
