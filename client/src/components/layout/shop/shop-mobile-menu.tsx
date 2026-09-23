"use client";

import * as React from "react";
import Link from "next/link";
import {
  Camera,
  Layers,
  Cpu,
  Store,
  Sparkles,
  User,
  Package,
  ChevronRight,
  Menu,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
  SheetClose,
} from "@/components/ui/sheet";

interface ShopMobileMenuProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  isAuthenticated: boolean;
  onOpenVisualSearch: () => void;
}

export function ShopMobileMenu({
  open,
  onOpenChange,
  isAuthenticated,
  onOpenVisualSearch,
}: ShopMobileMenuProps) {
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
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
              href="/#hero"
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
              href="/#features"
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
              href="/#catalog-section"
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
              href="/#tech-pipeline"
              className="flex items-center justify-between rounded-lg px-3 py-2 text-sm text-muted-foreground hover:text-foreground hover:bg-muted/50"
            >
              <span className="flex items-center gap-2.5">
                <Sparkles className="h-4 w-4 text-cyan-500" />
                Kiến trúc AI
              </span>
              <ChevronRight className="h-4 w-4 text-muted-foreground" />
            </Link>
          </SheetClose>

          {isAuthenticated && (
            <>
              <div className="pt-2 border-t border-border" />
              <SheetClose asChild>
                <Link
                  href="/profile"
                  className="flex items-center justify-between rounded-lg px-3 py-2 text-sm text-muted-foreground hover:text-foreground hover:bg-muted/50"
                >
                  <span className="flex items-center gap-2.5">
                    <User className="h-4 w-4 text-blue-500" />
                    Tài khoản của tôi
                  </span>
                  <ChevronRight className="h-4 w-4 text-muted-foreground" />
                </Link>
              </SheetClose>
              <SheetClose asChild>
                <Link
                  href="/orders"
                  className="flex items-center justify-between rounded-lg px-3 py-2 text-sm text-muted-foreground hover:text-foreground hover:bg-muted/50"
                >
                  <span className="flex items-center gap-2.5">
                    <Package className="h-4 w-4 text-indigo-500" />
                    Đơn hàng của tôi
                  </span>
                  <ChevronRight className="h-4 w-4 text-muted-foreground" />
                </Link>
              </SheetClose>
            </>
          )}

          <div className="pt-4 border-t border-border">
            <Button
              onClick={() => {
                onOpenChange(false);
                onOpenVisualSearch();
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
  );
}

