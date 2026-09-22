"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Camera, ShoppingBag, ShieldAlert, LogOut, LogIn, Sparkles } from "lucide-react";
import { useAuthStore } from "@/hooks/use-auth";
import { useCartStore } from "@/hooks/use-cart";
import { useVisualSearchStore } from "@/hooks/use-visual-search";
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
import { ThemeToggle } from "@/components/shared/theme-toggle";

export function Navbar() {
  const router = useRouter();
  const { user, isAuthenticated, isAdmin, logout } = useAuthStore();
  const { totalItems, openCart } = useCartStore();
  const { openModal: openVisualSearch } = useVisualSearchStore();

  const handleLogout = async () => {
    await logout();
    router.push("/login");
  };

  return (
    <header className="sticky top-0 z-40 w-full border-b border-border/40 bg-background/80 backdrop-blur-md">
      <div className="container mx-auto flex h-16 items-center justify-between px-4 sm:px-8">
        {/* Brand Logo */}
        <Link href="/" className="flex items-center gap-2 group">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary text-primary-foreground font-bold shadow-md shadow-primary/20 transition-transform group-hover:scale-105">
            <Camera className="h-5 w-5" />
          </div>
          <div className="flex flex-col">
            <span className="text-lg font-bold tracking-tight bg-gradient-to-r from-primary to-blue-600 bg-clip-text text-transparent">
              Visual AI Store
            </span>
            <span className="text-[10px] font-medium text-muted-foreground uppercase tracking-widest">
              Camera-to-Shop
            </span>
          </div>
        </Link>

        {/* Center / Actions */}
        <div className="flex items-center gap-3">
          {/* Visual AI Scan Trigger Button */}
          <Button
            onClick={openVisualSearch}
            className="relative gap-2 bg-gradient-to-r from-blue-600 via-indigo-600 to-primary text-white shadow-md hover:shadow-indigo-500/25 ring-2 ring-primary/40 animate-pulse transition-all"
          >
            <Sparkles className="h-4 w-4" />
            <span className="hidden sm:inline font-semibold">Quét AI</span>
          </Button>

          {/* Theme Toggle */}
          <ThemeToggle />

          {/* Cart Trigger */}
          {isAuthenticated ? (
            <Button
              variant="outline"
              size="icon"
              className="relative rounded-full h-10 w-10 border-border"
              onClick={openCart}
            >
              <ShoppingBag className="h-5 w-5 text-foreground" />
              {totalItems > 0 && (
                <span className="absolute -top-1.5 -right-1.5 flex h-5 w-5 items-center justify-center rounded-full bg-primary text-[11px] font-bold text-primary-foreground shadow-sm">
                  {totalItems > 99 ? "99+" : totalItems}
                </span>
              )}
            </Button>
          ) : (
            <Popover>
              <PopoverTrigger asChild>
                <Button variant="outline" size="icon" className="relative rounded-full h-10 w-10">
                  <ShoppingBag className="h-5 w-5 text-muted-foreground" />
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-64 p-4 text-center space-y-3 z-50 bg-popover text-popover-foreground shadow-lg border">
                <p className="text-sm text-muted-foreground">
                  Vui lòng đăng nhập để lưu trữ và quản lý giỏ hàng của bạn.
                </p>
                <Button size="sm" className="w-full" asChild>
                  <Link href="/login">Đăng nhập ngay</Link>
                </Button>
              </PopoverContent>
            </Popover>
          )}

          {/* User Auth Section */}
          {isAuthenticated && user ? (
            <div className="flex items-center gap-2">
              {/* Admin Panel Badge */}
              {isAdmin && (
                <Link href="/admin">
                  <Badge variant="destructive" className="hidden md:inline-flex items-center gap-1 cursor-pointer hover:bg-destructive/90">
                    <ShieldAlert className="h-3 w-3" />
                    ADMIN PANEL
                  </Badge>
                </Link>
              )}

              {/* Profile Dropdown */}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" className="relative h-10 w-10 rounded-full p-0">
                    <Avatar className="h-9 w-9 border border-border">
                      <AvatarImage src={user.avatar_url || ""} alt={user.full_name || user.email} />
                      <AvatarFallback className="bg-primary/10 text-primary font-semibold">
                        {(user.full_name || user.email).charAt(0).toUpperCase()}
                      </AvatarFallback>
                    </Avatar>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent className="w-56 mt-2 z-50 rounded-lg border bg-popover p-2 text-popover-foreground shadow-md" align="end">
                  <DropdownMenuLabel className="px-2 py-1.5 text-sm font-semibold">
                    <p className="truncate font-medium">{user.full_name || "Người dùng"}</p>
                    <p className="truncate text-xs text-muted-foreground">{user.email}</p>
                  </DropdownMenuLabel>
                  <DropdownMenuSeparator className="my-1 h-px bg-muted" />
                  {isAdmin && (
                    <DropdownMenuItem className="flex items-center gap-2 rounded-md px-2 py-1.5 text-sm cursor-pointer hover:bg-muted" asChild>
                      <Link href="/admin">
                        <ShieldAlert className="h-4 w-4 text-destructive" />
                        Trang Quản trị
                      </Link>
                    </DropdownMenuItem>
                  )}
                  <DropdownMenuItem
                    onClick={handleLogout}
                    className="flex items-center gap-2 rounded-md px-2 py-1.5 text-sm text-destructive cursor-pointer hover:bg-destructive/10"
                  >
                    <LogOut className="h-4 w-4" />
                    Đăng xuất
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          ) : (
            <Button size="sm" asChild className="gap-2">
              <Link href="/login">
                <LogIn className="h-4 w-4" />
                <span>Đăng nhập</span>
              </Link>
            </Button>
          )}
        </div>
      </div>
    </header>
  );
}
