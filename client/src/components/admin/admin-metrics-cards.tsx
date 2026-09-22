import * as React from "react";
import { DollarSign, ShoppingBag, Package, TrendingUp } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ProductStats, OrderStats } from "@/types";
import { formatVND } from "@/lib/utils";

interface AdminMetricsCardsProps {
  isLoading: boolean;
  productStats: ProductStats | null;
  orderStats: OrderStats | null;
}

export function AdminMetricsCards({
  isLoading,
  productStats,
  orderStats,
}: AdminMetricsCardsProps) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
      {/* 1. Doanh thu */}
      <Card className="border-border/60">
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-xs font-semibold text-muted-foreground">
            Tổng Doanh Thu
          </CardTitle>
          <DollarSign className="h-4 w-4 text-emerald-500" />
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <Skeleton className="h-8 w-28" />
          ) : (
            <div className="text-2xl font-bold text-foreground">
              {formatVND(orderStats?.total_revenue || 0)}
            </div>
          )}
          <p className="text-[11px] text-muted-foreground mt-1">
            Đơn hàng hoàn tất và thanh toán
          </p>
        </CardContent>
      </Card>

      {/* 2. Tổng đơn hàng */}
      <Card className="border-border/60">
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-xs font-semibold text-muted-foreground">
            Tổng Đơn Hàng
          </CardTitle>
          <ShoppingBag className="h-4 w-4 text-primary" />
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <Skeleton className="h-8 w-16" />
          ) : (
            <div className="text-2xl font-bold text-foreground">
              {orderStats?.total_orders || 0}
            </div>
          )}
          <p className="text-[11px] text-muted-foreground mt-1">
            Chờ xử lý: {orderStats?.pending_orders || 0} | Đã gửi: {orderStats?.shipped_orders || 0}
          </p>
        </CardContent>
      </Card>

      {/* 3. Sản phẩm trong kho */}
      <Card className="border-border/60">
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-xs font-semibold text-muted-foreground">
            Kho Hàng Sản Phẩm
          </CardTitle>
          <Package className="h-4 w-4 text-blue-500" />
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <Skeleton className="h-8 w-20" />
          ) : (
            <div className="text-2xl font-bold text-foreground">
              {productStats?.total_products || 0} SKU
            </div>
          )}
          <p className="text-[11px] text-muted-foreground mt-1">
            Còn hàng: {productStats?.available_products || 0} | Hết hàng: {productStats?.out_of_stock_products || 0}
          </p>
        </CardContent>
      </Card>

      {/* 4. Giá trị tồn kho */}
      <Card className="border-border/60">
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-xs font-semibold text-muted-foreground">
            Tổng Giá Trị Tồn Kho
          </CardTitle>
          <TrendingUp className="h-4 w-4 text-indigo-500" />
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <Skeleton className="h-8 w-28" />
          ) : (
            <div className="text-2xl font-bold text-foreground">
              {formatVND(productStats?.total_inventory_value || 0)}
            </div>
          )}
          <p className="text-[11px] text-muted-foreground mt-1">
            Tổng số lượng: {productStats?.total_stock_units || 0} đơn vị
          </p>
        </CardContent>
      </Card>
    </div>
  );
}

