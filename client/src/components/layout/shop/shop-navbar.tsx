"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Camera,
  ShoppingBag,
  LogIn,
  Sparkles,
  Search,
} from "lucide-react";
import { useAuthStore } from "@/stores/auth-store";
import { useCartStore } from "@/stores/cart-store";
import { useVisualSearchStore } from "@/stores/visual-search-store";
import { Button } from "@/components/ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { ThemeToggle } from "@/components/layout/theme-toggle";
import { ShopUserMenu } from "./shop-user-menu";
import { ShopMobileMenu } from "./shop-mobile-menu";

export function ShopNavbar() {
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const isAdmin = useAuthStore((s) => s.isAdmin);
  const logout = useAuthStore((s) => s.logout);

  const totalItems = useCartStore((s) => s.totalItems);
  const openCart = useCartStore((s) => s.openCart);

  const openVisualSearch = useVisualSearchStore((s) => s.openModal);
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false);

  const handleLogout = async () => {
    await logout();
    router.push("/login");
  };

  const handleQuickSearchClick = () => {
    const el = document.getElementById("catalog-search-input");
    if (el) {
      el.focus();
      el.scrollIntoView({ behavior: "smooth", block: "center" });
    } else {
      const section = document.getElementById("catalog-section");
      if (section) section.scrollIntoView({ behavior: "smooth" });
    }
  };

  return (
    <header className="sticky top-0 z-40 w-full border-b border-border bg-background/80 backdrop-blur-xl transition-colors">
      <div className="container mx-auto flex h-16 items-center justify-between px-4 sm:px-8">
        {/* Left: Brand Logo */}
        <Link href="/" className="flex items-center gap-3 group">
          <div className="relative flex h-10 w-10 items-center justify-center rounded-xl bg-linear-to-br from-blue-500 via-indigo-600 to-violet-600 text-white font-bold shadow-lg shadow-blue-500/25 transition-transform group-hover:scale-105">
            <Camera className="h-5 w-5" />
            <span className="absolute -top-1 -right-1 flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-cyan-500"></span>
            </span>
          </div>
          <div className="flex flex-col">
            <div className="flex items-center gap-1.5">
              <span className="text-base sm:text-lg font-extrabold tracking-tight bg-linear-to-r from-slate-900 via-indigo-950 to-blue-600 dark:from-white dark:via-slate-200 dark:to-blue-300 bg-clip-text text-transparent">
                Visual AI Store
              </span>
              <span className="hidden md:inline-flex text-[10px] font-bold px-1.5 py-0.5 rounded bg-blue-500/10 dark:bg-blue-500/20 text-blue-600 dark:text-blue-400 border border-blue-500/20 dark:border-blue-500/30">
                v2.0
              </span>
            </div>
            <span className="text-[10px] font-medium text-muted-foreground uppercase tracking-widest hidden sm:inline">
              YOLO11 • Camera-to-Shop
            </span>
          </div>
        </Link>

        {/* Center: Navigation Links (Desktop Anchor Scroll) */}
        <nav className="hidden lg:flex items-center gap-1 rounded-full border border-border bg-muted/40 px-4 py-1.5 backdrop-blur-md">
          <Link
            href="/#hero"
            className="px-3 py-1 text-xs font-medium text-muted-foreground hover:text-foreground transition-colors"
          >
            Khám phá
          </Link>
          <Link
            href="/#features"
            className="px-3 py-1 text-xs font-medium text-muted-foreground hover:text-foreground transition-colors"
          >
            Cách hoạt động
          </Link>
          <Link
            href="/#catalog-section"
            className="px-3 py-1 text-xs font-medium text-muted-foreground hover:text-foreground transition-colors"
          >
            Kho sản phẩm
          </Link>
          <Link
            href="/#tech-pipeline"
            className="px-3 py-1 text-xs font-medium text-muted-foreground hover:text-foreground transition-colors"
          >
            Kiến trúc AI
          </Link>
        </nav>

        {/* Right: Actions */}
        <div className="flex items-center gap-2 sm:gap-3">
          {/* Quick Search Pill (Desktop) */}
          <button
            type="button"
            onClick={handleQuickSearchClick}
            className="hidden md:flex items-center gap-2 rounded-full border border-border bg-muted/40 px-3.5 py-1.5 text-xs text-muted-foreground hover:border-primary/40 hover:text-foreground transition-all cursor-pointer"
          >
            <Search className="h-3.5 w-3.5 text-muted-foreground" />
            <span>Tìm kiếm...</span>
            <kbd className="pointer-events-none inline-flex h-4 select-none items-center gap-0.5 rounded border border-border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground">
              ⌘K
            </kbd>
          </button>

          {/* Glowing Neon CTA: Quét AI */}
          <Button
            onClick={openVisualSearch}
            className="relative gap-2 rounded-full px-4 sm:px-5 py-2 text-xs sm:text-sm font-semibold text-white bg-linear-to-r from-blue-600 via-indigo-600 to-violet-600 hover:from-blue-500 hover:to-violet-500 shadow-md shadow-indigo-500/25 border border-cyan-400/40 ring-2 ring-cyan-500/20 hover:ring-cyan-400/50 transition-all cursor-pointer"
          >
            <Sparkles className="h-4 w-4 text-cyan-300 animate-pulse" />
            <span className="font-semibold">Quét AI</span>
          </Button>

          {/* Theme Toggle */}
          <ThemeToggle />

          {/* Cart Trigger */}
          {isAuthenticated ? (
            <Button
              variant="outline"
              size="icon"
              className="relative rounded-full h-9 w-9 sm:h-10 sm:w-10 border-border bg-muted/40 hover:bg-muted text-foreground cursor-pointer"
              onClick={openCart}
            >
              <ShoppingBag className="h-4 w-4 sm:h-5 sm:w-5" />
              {totalItems > 0 && (
                <span className="absolute -top-1.5 -right-1.5 flex h-5 w-5 items-center justify-center rounded-full bg-linear-to-r from-blue-500 to-violet-600 text-[11px] font-bold text-white shadow-sm ring-2 ring-background">
                  {totalItems > 99 ? "99+" : totalItems}
                </span>
              )}
            </Button>
          ) : (
            <Popover>
              <PopoverTrigger asChild>
                <Button
                  variant="outline"
                  size="icon"
                  className="relative rounded-full h-9 w-9 sm:h-10 sm:w-10 border-border bg-muted/40 hover:bg-muted text-muted-foreground"
                >
                  <ShoppingBag className="h-4 w-4 sm:h-5 sm:w-5" />
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-64 p-4 text-center space-y-3 z-50 rounded-xl border border-border bg-popover text-popover-foreground shadow-2xl backdrop-blur-xl">
                <p className="text-xs text-muted-foreground">
                  Vui lòng đăng nhập để lưu trữ và quản lý giỏ hàng của bạn.
                </p>
                <Button
                  size="sm"
                  className="w-full rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs"
                  asChild
                >
                  <Link href="/login">Đăng nhập ngay</Link>
                </Button>
              </PopoverContent>
            </Popover>
          )}

          {/* User Auth Section */}
          {isAuthenticated && user ? (
            <ShopUserMenu
              user={user}
              isAdmin={isAdmin}
              onLogout={handleLogout}
            />
          ) : (
            <Button
              size="sm"
              asChild
              className="gap-1.5 rounded-full text-xs font-semibold bg-muted hover:bg-muted/80 text-foreground border border-border"
            >
              <Link href="/login">
                <LogIn className="h-3.5 w-3.5" />
                <span className="hidden sm:inline">Đăng nhập</span>
              </Link>
            </Button>
          )}

          {/* Mobile Sheet Trigger & Menu */}
          <ShopMobileMenu
            open={mobileMenuOpen}
            onOpenChange={setMobileMenuOpen}
            isAuthenticated={isAuthenticated}
            onOpenVisualSearch={openVisualSearch}
          />
        </div>
      </div>
    </header>
  );
}
