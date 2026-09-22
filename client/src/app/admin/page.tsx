"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import {
  ShieldAlert,
  Package,
  ShoppingBag,
  DollarSign,
  TrendingUp,
  Camera,
  RefreshCw,
  Eye,
} from "lucide-react";
import { useAuthStore } from "@/hooks/use-auth";
import { apiClient, resolveMediaUrl } from "@/lib/api-client";
import { ProductStats, OrderStats, DetectionRecord } from "@/types";
import { formatVND } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";

export default function AdminDashboardPage() {
  const router = useRouter();
  const { isAuthenticated, isAdmin, isLoading: authLoading } = useAuthStore();

  const [productStats, setProductStats] = React.useState<ProductStats | null>(null);
  const [orderStats, setOrderStats] = React.useState<OrderStats | null>(null);
  const [historyRecords, setHistoryRecords] = React.useState<DetectionRecord[]>([]);
  const [isLoading, setIsLoading] = React.useState(true);

  React.useEffect(() => {
    if (!authLoading && (!isAuthenticated || !isAdmin)) {
      router.push("/login");
    }
  }, [authLoading, isAuthenticated, isAdmin, router]);

  const loadDashboardData = React.useCallback(async () => {
    setIsLoading(true);
    try {
      const [pStatsRes, oStatsRes, histRes] = await Promise.all([
        apiClient.get<ProductStats>("/products/stats").catch(() => null),
        apiClient.get<OrderStats>("/orders/stats").catch(() => null),
        apiClient.get<{ records: DetectionRecord[] }>("/history", { params: { limit: 6, skip: 0 } }).catch(() => null),
      ]);

      if (pStatsRes) setProductStats(pStatsRes.data);
      if (oStatsRes) setOrderStats(oStatsRes.data);
      if (histRes) setHistoryRecords(histRes.data?.records || []);
    } finally {
      setIsLoading(false);
    }
  }, []);

  React.useEffect(() => {
    if (isAuthenticated && isAdmin) {
      loadDashboardData();
    }
  }, [isAuthenticated, isAdmin, loadDashboardData]);

  if (authLoading || (!isAdmin && isAuthenticated)) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <RefreshCw className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 sm:px-8 py-10 space-y-8">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b pb-6">
        <div>
          <div className="flex items-center gap-2">
            <Badge variant="destructive" className="gap-1 px-2.5 py-0.5">
              <ShieldAlert className="h-3.5 w-3.5" />
              QUẢN TRỊ VIÊN
            </Badge>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">Hệ Thống Quản Trị Trung Tâm</h1>
          </div>
          <p className="text-xs sm:text-sm text-muted-foreground mt-1">
            Theo dõi chỉ số kho hàng, doanh thu đơn hàng và giám sát nhật ký nhận diện AI.
          </p>
        </div>

        <Button onClick={loadDashboardData} variant="outline" size="sm" className="gap-1.5 self-start sm:self-auto">
          <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
          <span>Làm mới dữ liệu</span>
        </Button>
      </div>

      {/* KPI Metrics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {/* Doanh thu */}
        <Card className="border-border/60">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-xs font-semibold text-muted-foreground">Tổng Doanh Thu</CardTitle>
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
            <p className="text-[11px] text-muted-foreground mt-1">Đơn hàng hoàn tất và thanh toán</p>
          </CardContent>
        </Card>

        {/* Tổng đơn hàng */}
        <Card className="border-border/60">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-xs font-semibold text-muted-foreground">Tổng Đơn Hàng</CardTitle>
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

        {/* Sản phẩm trong kho */}
        <Card className="border-border/60">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-xs font-semibold text-muted-foreground">Kho Hàng Sản Phẩm</CardTitle>
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

        {/* Giá trị tồn kho */}
        <Card className="border-border/60">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-xs font-semibold text-muted-foreground">Tổng Giá Trị Tồn Kho</CardTitle>
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

      {/* Detection Audit Log Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Camera className="h-5 w-5 text-primary" />
            <h2 className="text-lg font-bold text-foreground">Nhật Ký Quét Ảnh Camera & YOLO Mới Nhất</h2>
          </div>
          <span className="text-xs text-muted-foreground">Bản ghi gần nhất</span>
        </div>

        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <Skeleton className="h-40 rounded-xl" />
            <Skeleton className="h-40 rounded-xl" />
            <Skeleton className="h-40 rounded-xl" />
          </div>
        ) : historyRecords.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {historyRecords.map((record) => (
              <div
                key={record.id}
                className="flex flex-col rounded-xl border bg-card p-4 space-y-3 shadow-xs hover:border-primary/50 transition-colors"
              >
                <div className="flex items-start gap-3">
                  <div className="relative h-16 w-16 shrink-0 overflow-hidden rounded-lg border bg-black/5">
                    <Image
                      src={resolveMediaUrl(record.image_url)}
                      alt="Detection"
                      fill
                      sizes="64px"
                      className="object-cover"
                    />
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] font-mono text-muted-foreground truncate">
                        ID: {record.id.slice(0, 8)}...
                      </span>
                      <Badge variant="outline" className="text-[10px]">
                        {record.status}
                      </Badge>
                    </div>

                    <p className="text-xs text-foreground font-medium line-clamp-2 mt-1">
                      {record.summary || record.raw_detected_text || "Không có tóm tắt"}
                    </p>
                  </div>
                </div>

                {/* Detected Badges */}
                <div className="flex flex-wrap gap-1">
                  {Array.isArray(record.objects) &&
                    record.objects.slice(0, 3).map((obj, i) => (
                      <Badge key={i} variant="secondary" className="text-[10px] py-0 px-1.5">
                        {obj.label_vi || obj.name}
                      </Badge>
                    ))}
                  {Array.isArray(record.objects) && record.objects.length > 3 && (
                    <Badge variant="outline" className="text-[10px] py-0 px-1.5">
                      +{record.objects.length - 3}
                    </Badge>
                  )}
                </div>

                <div className="pt-2 border-t flex items-center justify-between text-[11px] text-muted-foreground">
                  <span>{record.created_at ? new Date(record.created_at).toLocaleString("vi-VN") : "Gần đây"}</span>
                  <a
                    href={resolveMediaUrl(record.image_url)}
                    target="_blank"
                    rel="noreferrer"
                    className="flex items-center gap-1 text-primary hover:underline"
                  >
                    <Eye className="h-3 w-3" />
                    Xem ảnh
                  </a>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="rounded-xl border border-dashed p-8 text-center text-muted-foreground text-sm">
            Chưa có lịch sử nhận diện nào được ghi nhận trên hệ thống.
          </div>
        )}
      </div>
    </div>
  );
}
