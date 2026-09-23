import * as React from "react";
import { ShopNavbar } from "@/components/layout/shop/shop-navbar";
import { ShopFooter } from "@/components/layout/shop/shop-footer";

interface ShopLayoutProps {
  children: React.ReactNode;
}

export default function ShopLayout({ children }: ShopLayoutProps) {
  return (
    <div className="relative flex min-h-screen flex-col bg-background text-foreground">
      <ShopNavbar />
      <main className="flex-1 flex flex-col">{children}</main>
      <ShopFooter />
    </div>
  );
}

