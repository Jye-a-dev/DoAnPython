"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Camera,
  ShoppingBag,
  ShieldAlert,
  LogOut,
  LogIn,
  Sparkles,
  Search,
  Menu,
  ChevronRight,
  Layers,
  Cpu,
  Store,
} from "lucide-react";
import { useAuthStore } from "@/stores/auth-store";
import { useCartStore } from "@/stores/cart-store";
import { useVisualSearchStore } from "@/stores/visual-search-store";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@radix-ui/react-dropdown-menu";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
  SheetClose,
} from "@/components/ui/sheet";
import { ThemeToggle } from "@/components/layout/theme-toggle";

export function Navbar() {
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

        {/* Center: Navigation Links (Desktop) */}
        <nav className="hidden lg:flex items-center gap-1 rounded-full border border-border bg-muted/40 px-4 py-1.5 backdrop-blur-md">
          <Link
            href="#hero"
            className="px-3 py-1 text-xs font-medium text-muted-foreground hover:text-foreground transition-colors"
          >
            Khám phá
          </Link>
          <Link
            href="#features"
            className="px-3 py-1 text-xs font-medium text-muted-foreground hover:text-foreground transition-colors"
          >
            Cách hoạt động
          </Link>
          <Link
            href="#catalog-section"
            className="px-3 py-1 text-xs font-medium text-muted-foreground hover:text-foreground transition-colors"
          >
            Kho sản phẩm
          </Link>
          <Link
            href="#tech-pipeline"
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

          {/* Glowing Neon CTA: Bắt đầu Quét AI */}
          <Button
            onClick={openVisualSearch}
            className="relative gap-2 rounded-full px-4 sm:px-5 py-2 text-xs sm:text-sm font-semibold text-white bg-linear-to-r from-blue-600 via-indigo-600 to-violet-600 hover:from-blue-500 hover:to-violet-500 shadow-md shadow-indigo-500/25 border border-cyan-400/40 ring-2 ring-cyan-500/20 hover:ring-cyan-400/50 transition-all cursor-pointer"
          >
            <Sparkles className="h-4 w-4 text-cyan-300 animate-pulse" />
            <span className="font-semibold">Quét AI</span>
          </Button>

          {/* Theme Toggle */}
          <ThemeToggle />

          {/* Cart Trigger Button */}
          {isAuthenticated ? (
            <Button
              variant="outline"
              size="icon"
              className="relative rounded-full h-9 w-9 sm:h-10 sm:w-10 border-border bg-muted/40 hover:bg-muted text-foreground"
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
                <Button size="sm" className="w-full rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs" asChild>
                  <Link href="/login">Đăng nhập ngay</Link>
                </Button>
              </PopoverContent>
            </Popover>
          )}

          {/* User Auth Section */}
          {isAuthenticated && user ? (
            <div className="flex items-center gap-2">
              {isAdmin && (
                <Link href="/admin">
                  <Badge
                    variant="destructive"
                    className="hidden xl:inline-flex items-center gap-1 cursor-pointer bg-red-500/20 text-red-500 dark:text-red-400 border border-red-500/30 hover:bg-red-500/30 text-[10px]"
                  >
                    <ShieldAlert className="h-3 w-3" />
                    ADMIN
                  </Badge>
                </Link>
              )}

              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" className="relative h-9 w-9 sm:h-10 sm:w-10 rounded-full p-0 ring-1 ring-border">
                    <Avatar className="h-8 w-8 sm:h-9 sm:w-9">
                      <AvatarImage src={user.avatar_url || ""} alt={user.full_name || user.email} />
                      <AvatarFallback className="bg-primary/10 text-primary font-semibold text-xs">
                        {(user.full_name || user.email).charAt(0).toUpperCase()}
                      </AvatarFallback>
                    </Avatar>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent
                  className="w-56 mt-2 z-50 rounded-xl border border-border bg-popover p-2 text-popover-foreground shadow-2xl backdrop-blur-xl"
                  align="end"
                >
                  <DropdownMenuLabel className="px-2 py-1.5 text-xs">
                    <p className="font-semibold text-foreground truncate">{user.full_name || "Người dùng"}</p>
                    <p className="text-[11px] text-muted-foreground truncate">{user.email}</p>
                  </DropdownMenuLabel>
                  <DropdownMenuSeparator className="my-1 h-px bg-border" />
                  {isAdmin && (
                    <DropdownMenuItem
                      className="flex items-center gap-2 rounded-lg px-2 py-1.5 text-xs text-red-500 hover:bg-muted cursor-pointer"
                      asChild
                    >
                      <Link href="/admin">
                        <ShieldAlert className="h-3.5 w-3.5" />
                        Trang Quản trị Admin
                      </Link>
                    </DropdownMenuItem>
                  )}
                  <DropdownMenuItem
                    onClick={handleLogout}
                    className="flex items-center gap-2 rounded-lg px-2 py-1.5 text-xs text-muted-foreground hover:bg-destructive/10 hover:text-destructive cursor-pointer"
                  >
                    <LogOut className="h-3.5 w-3.5" />
                    Đăng xuất
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
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

          {/* Mobile Sheet Trigger */}
          <Sheet open={mobileMenuOpen} onOpenChange={setMobileMenuOpen}>
            <SheetTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="lg:hidden h-9 w-9 rounded-xl border border-border text-foreground hover:bg-muted"
              >
                <Menu className="h-5 w-5" />
              </Button>
            </SheetTrigger>
            <SheetContent
              side="right"
              className="w-72 bg-background/95 border-l border-border p-6 text-foreground backdrop-blur-2xl"
            >
              <SheetHeader className="text-left border-b border-border pb-4">
                <SheetTitle className="text-base font-bold text-foreground flex items-center gap-2">
                  <Camera className="h-5 w-5 text-blue-500" />
                  Visual AI Store
                </SheetTitle>
              </SheetHeader>
              <div className="flex flex-col gap-3 pt-6">
                <SheetClose asChild>
                  <Link
                    href="#hero"
                    className="flex items-center justify-between rounded-lg px-3 py-2 text-sm text-muted-foreground hover:text-foreground hover:bg-muted/50"
                  >
                    <span className="flex items-center gap-2.5">
                      <Layers className="h-4 w-4 text-blue-500" />
                      Khám phá
                    </span>
                    <ChevronRight className="h-4 w-4 text-muted-foreground" />
                  </Link>
                </SheetClose>
                <SheetClose asChild>
                  <Link
                    href="#features"
                    className="flex items-center justify-between rounded-lg px-3 py-2 text-sm text-muted-foreground hover:text-foreground hover:bg-muted/50"
                  >
                    <span className="flex items-center gap-2.5">
                      <Cpu className="h-4 w-4 text-indigo-500" />
                      Cách hoạt động
                    </span>
                    <ChevronRight className="h-4 w-4 text-muted-foreground" />
                  </Link>
                </SheetClose>
                <SheetClose asChild>
                  <Link
                    href="#catalog-section"
                    className="flex items-center justify-between rounded-lg px-3 py-2 text-sm text-muted-foreground hover:text-foreground hover:bg-muted/50"
                  >
                    <span className="flex items-center gap-2.5">
                      <Store className="h-4 w-4 text-violet-500" />
                      Kho sản phẩm
                    </span>
                    <ChevronRight className="h-4 w-4 text-muted-foreground" />
                  </Link>
                </SheetClose>
                <SheetClose asChild>
                  <Link
                    href="#tech-pipeline"
                    className="flex items-center justify-between rounded-lg px-3 py-2 text-sm text-muted-foreground hover:text-foreground hover:bg-muted/50"
                  >
                    <span className="flex items-center gap-2.5">
                      <Sparkles className="h-4 w-4 text-cyan-500" />
                      Kiến trúc AI
                    </span>
                    <ChevronRight className="h-4 w-4 text-muted-foreground" />
                  </Link>
                </SheetClose>

                <div className="pt-4 border-t border-border">
                  <Button
                    onClick={() => {
                      setMobileMenuOpen(false);
                      openVisualSearch();
                    }}
                    className="w-full gap-2 rounded-xl bg-linear-to-r from-blue-600 to-indigo-600 text-white text-sm"
                  >
                    <Camera className="h-4 w-4" />
                    Quét Ảnh Nhận Diện Ngay
                  </Button>
                </div>
              </div>
            </SheetContent>
          </Sheet>
        </div>
      </div>
    </header>
  );
}
