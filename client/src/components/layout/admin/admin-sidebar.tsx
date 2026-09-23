"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Boxes,
  FileSearch,
  CheckCircle2,
  Users,
  Settings,
  ChevronLeft,
  ChevronRight,
  ShieldCheck,
  Store,
  LogOut,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useAuthStore } from "@/stores/auth-store";

const adminNavItems = [
  { title: "Dashboard", href: "/admin", icon: LayoutDashboard },
  { title: "Kho hàng & SKU", href: "/admin/products", icon: Boxes },
  { title: "Nhật ký nhận diện", href: "/admin/records", icon: FileSearch },
  { title: "Kiểm duyệt AI & OCR", href: "/admin/reviews", icon: CheckCircle2 },
  { title: "Người dùng", href: "/admin/users", icon: Users },
  { title: "Cấu hình Gateway", href: "/admin/settings", icon: Settings },
];

export function AdminSidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = React.useState(false);
  const logout = useAuthStore((s) => s.logout);

  return (
    <aside
      className={cn(
        "relative flex flex-col border-r border-border bg-card transition-all duration-300 z-30 select-none",
        collapsed ? "w-18" : "w-64"
      )}
    >
      {/* Brand Header */}
      <div className="flex h-16 items-center justify-between px-4 border-b border-border">
        <Link href="/admin" className="flex items-center gap-3 overflow-hidden">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-linear-to-br from-red-600 via-rose-600 to-amber-600 text-white shadow-md shadow-red-500/20">
            <ShieldCheck className="h-5 w-5" />
          </div>
          {!collapsed && (
            <div className="flex flex-col truncate">
              <span className="font-bold text-sm tracking-tight text-foreground truncate">
                Admin Control
              </span>
              <Badge variant="destructive" className="w-fit text-[9px] px-1.5 py-0 uppercase font-mono">
                Admin Core
              </Badge>
            </div>
          )}
        </Link>
      </div>

      {/* Navigation List */}
      <nav className="flex-1 space-y-1.5 p-3 overflow-y-auto">
        {adminNavItems.map((item) => {
          const isActive =
            item.href === "/admin"
              ? pathname === "/admin"
              : pathname.startsWith(item.href);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              title={collapsed ? item.title : undefined}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-xs font-medium transition-all group",
                isActive
                  ? "bg-primary text-primary-foreground shadow-sm shadow-primary/25 font-semibold"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              )}
            >
              <Icon
                className={cn(
                  "h-4 w-4 shrink-0 transition-transform group-hover:scale-110",
                  isActive && "text-primary-foreground"
                )}
              />
              {!collapsed && <span className="truncate">{item.title}</span>}
            </Link>
          );
        })}
      </nav>

      {/* Bottom Actions */}
      <div className="p-3 border-t border-border space-y-2">
        <Button
          variant="outline"
          size="sm"
          asChild
          className={cn(
            "w-full justify-start gap-2 text-xs",
            collapsed && "justify-center px-0"
          )}
        >
          <Link href="/">
            <Store className="h-4 w-4 shrink-0 text-blue-500" />
            {!collapsed && <span>Về Giao Diện Shop</span>}
          </Link>
        </Button>

        <Button
          variant="ghost"
          size="sm"
          onClick={() => logout()}
          className={cn(
            "w-full justify-start gap-2 text-xs text-destructive hover:bg-destructive/10",
            collapsed && "justify-center px-0"
          )}
        >
          <LogOut className="h-4 w-4 shrink-0" />
          {!collapsed && <span>Đăng xuất</span>}
        </Button>

        {/* Collapse Toggle Trigger */}
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setCollapsed(!collapsed)}
          className="w-full h-8 text-muted-foreground hover:text-foreground cursor-pointer"
        >
          {collapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <ChevronLeft className="h-4 w-4" />
          )}
        </Button>
      </div>
    </aside>
  );
}

