"use client";

import * as React from "react";
import { ThemeProvider } from "next-themes";
import { QueryClientProvider } from "@tanstack/react-query";
import { NuqsAdapter } from "nuqs/adapters/next/app";
import { Toaster } from "sonner";
import { getQueryClient } from "@/lib/query-client";
import { useAuthStore } from "@/hooks/use-auth";
import { useCartStore } from "@/hooks/use-cart";
import { CartDrawer } from "@/components/cart/cart-drawer";
import { VisualSearchModal } from "@/components/home/visual-search-modal";

interface ProvidersProps {
  children: React.ReactNode;
}

export function Providers({ children }: ProvidersProps) {
  const queryClient = getQueryClient();
  const initializeAuth = useAuthStore((state) => state.initializeAuth);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const fetchCart = useCartStore((state) => state.fetchCart);

  React.useEffect(() => {
    initializeAuth();
  }, [initializeAuth]);

  React.useEffect(() => {
    if (isAuthenticated) {
      fetchCart();
    }
  }, [isAuthenticated, fetchCart]);

  return (
    <ThemeProvider attribute="class" defaultTheme="system" enableSystem disableTransitionOnChange>
      <QueryClientProvider client={queryClient}>
        <NuqsAdapter>
          {children}
          <CartDrawer />
          <VisualSearchModal />
          <Toaster richColors position="bottom-right" closeButton />
        </NuqsAdapter>
      </QueryClientProvider>
    </ThemeProvider>
  );
}
