"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Package,
  ShoppingBag,
  ChevronRight,
  ArrowLeft,
} from "lucide-react";
import { useAuthStore } from "@/stores/auth-store";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

export default function UserOrdersPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading } = useAuthStore();

  React.useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/login?redirect=/orders");
    }
  }, [isLoading, isAuthenticated, router]);

  if (isLoading || !user) {
    return (
      <div className="container mx-auto px-4 py-16 flex justify-center items-center flex-1">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 sm:px-8 py-10 space-y-8 max-w-4xl flex-1">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-6">
        <div>
          <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1">
            <Link href="/profile" className="hover:text-foreground">
              Tài khoản
            </Link>
            <ChevronRight className="h-3.5 w-3.5" />
            <span className="text-foreground">Đơn hàng</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
            Đơn Hàng Của Tôi
          </h1>
          <p className="text-xs sm:text-sm text-muted-foreground mt-1">
            Xem lại lịch sử đặt hàng, hóa đơn điện tử và trạng thái vận chuyển AI.
          </p>
        </div>

        <Button variant="outline" size="sm" asChild className="text-xs gap-1.5 self-start sm:self-auto">
          <Link href="/profile">
            <ArrowLeft className="h-3.5 w-3.5" />
            <span>Về hồ sơ cá nhân</span>
          </Link>
        </Button>
      </div>

      {/* Orders List / Empty State */}
      <Card className="border-border bg-card/60 backdrop-blur-sm">
        <CardContent className="py-16 flex flex-col items-center justify-center text-center space-y-4">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-muted/60 text-muted-foreground">
            <Package className="h-8 w-8 text-indigo-500" />
          </div>
          <div className="space-y-1">
            <h3 className="font-bold text-base text-foreground">
              Chưa có đơn hàng nào
            </h3>
            <p className="text-xs text-muted-foreground max-w-sm">
              Bạn chưa thực hiện đơn đặt hàng nào gần đây. Hãy trải nghiệm tính năng Quét AI bằng camera để thêm sản phẩm vào giỏ hàng ngay!
            </p>
          </div>

          <Button asChild size="sm" className="rounded-full gap-2 text-xs">
            <Link href="/#catalog-section">
              <ShoppingBag className="h-4 w-4" />
              <span>Khám phá sản phẩm</span>
            </Link>
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}

