"use client";

import * as React from "react";
import { Boxes, Plus, Search, RefreshCw, Flame, Clock } from "lucide-react";
import { productService } from "@/services/product.service";
import { adminService } from "@/services/admin.service";
import type { Product, InventoryForecastItem } from "@/types";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { ProductCreateModal } from "@/components/admin/product-create-modal";

export default function AdminProductsPage() {
  const [products, setProducts] = React.useState<Product[]>([]);
  const [forecastMap, setForecastMap] = React.useState<Record<string, InventoryForecastItem>>({});
  const [highDemandCount, setHighDemandCount] = React.useState(0);
  const [isLoading, setIsLoading] = React.useState(true);
  const [search, setSearch] = React.useState("");
  const [isCreateModalOpen, setIsCreateModalOpen] = React.useState(false);
  const [showHighDemandOnly, setShowHighDemandOnly] = React.useState(false);

  const loadData = React.useCallback(async () => {
    setIsLoading(true);
    try {
      const [prodRes, forecastRes] = await Promise.all([
        productService.getAll({ limit: 100 }).catch(() => null),
        adminService.getInventoryForecast().catch(() => null),
      ]);

      if (prodRes?.data) {
        setProducts(prodRes.data);
      }

      if (forecastRes?.data) {
        const map: Record<string, InventoryForecastItem> = {};
        for (const item of forecastRes.data.items) {
          map[item.product_id] = item;
        }
        setForecastMap(map);
        setHighDemandCount(forecastRes.data.high_demand_count || 0);
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  React.useEffect(() => {
    loadData();
  }, [loadData]);

  const filteredProducts = products.filter((p) => {
    const matchesSearch =
      p.name.toLowerCase().includes(search.toLowerCase()) ||
      p.sku?.toLowerCase().includes(search.toLowerCase()) ||
      p.class_name?.toLowerCase().includes(search.toLowerCase());

    if (!matchesSearch) return false;

    if (showHighDemandOnly) {
      const fc = forecastMap[p.id];
      return fc && (fc.urgency === "CRITICAL" || fc.urgency === "HIGH");
    }

    return true;
  });

  return (
    <div className="space-y-6">
      {/* Header Toolbar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-6">
        <div>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="gap-1 px-2.5 py-0.5 text-blue-500 border-blue-500/30">
              <Boxes className="h-3.5 w-3.5" />
              SKU & INVENTORY
            </Badge>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">
              Quản Lý Kho Hàng & SKU
            </h1>
          </div>
          <p className="text-xs sm:text-sm text-muted-foreground mt-1">
            Zero-Shot Auto-Classification, dự báo nhập hàng thông minh (Stockout ETA) và đối soát class nhãn YOLO11.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            onClick={loadData}
            variant="outline"
            size="sm"
            disabled={isLoading}
            className="gap-1.5 cursor-pointer text-xs"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isLoading ? "animate-spin" : ""}`} />
            <span>Làm mới</span>
          </Button>

          <Button
            onClick={() => setIsCreateModalOpen(true)}
            size="sm"
            className="gap-1.5 text-xs bg-blue-600 hover:bg-blue-500 text-white cursor-pointer"
          >
            <Plus className="h-3.5 w-3.5" />
            <span>Thêm sản phẩm (Auto-Tag)</span>
          </Button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3 w-full max-w-md">
          <div className="relative w-full">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Tìm theo tên, SKU, class nhãn..."
              className="h-9 w-full rounded-lg border border-border bg-card pl-8 pr-3 text-xs placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>

          <Button
            onClick={() => setShowHighDemandOnly(!showHighDemandOnly)}
            variant={showHighDemandOnly ? "default" : "outline"}
            size="sm"
            className={`h-9 text-xs gap-1.5 shrink-0 cursor-pointer ${
              showHighDemandOnly
                ? "bg-amber-600 hover:bg-amber-500 text-white"
                : "border-amber-500/30 text-amber-500 hover:bg-amber-500/10"
            }`}
          >
            <Flame className="h-3.5 w-3.5" />
            <span>Nhu cầu cao ({highDemandCount})</span>
          </Button>
        </div>

        <span className="text-xs text-muted-foreground font-mono">
          Hiển thị: {filteredProducts.length} / {products.length} SKU
        </span>
      </div>

      {/* Products Table Card */}
      <Card className="border-border bg-card/60 backdrop-blur-sm">
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left border-collapse">
              <thead>
                <tr className="border-b border-border bg-muted/30 text-muted-foreground font-semibold">
                  <th className="p-3 pl-4">Sản Phẩm & Cảnh Báo AI</th>
                  <th className="p-3">Mã SKU</th>
                  <th className="p-3">Class AI (YOLO)</th>
                  <th className="p-3">Đơn Giá</th>
                  <th className="p-3">Tồn Kho</th>
                  <th className="p-3">Quét Tuần Này</th>
                  <th className="p-3">Stockout ETA</th>
                  <th className="p-3 pr-4 text-right">Trạng Thái</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/60">
                {isLoading ? (
                  <tr>
                    <td colSpan={8} className="p-8 text-center text-muted-foreground">
                      <RefreshCw className="h-5 w-5 animate-spin mx-auto text-primary mb-2" />
                      Đang phân tích tồn kho và đối soát dữ liệu quét...
                    </td>
                  </tr>
                ) : filteredProducts.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="p-8 text-center text-muted-foreground">
                      Không tìm thấy SKU nào phù hợp với bộ lọc.
                    </td>
                  </tr>
                ) : (
                  filteredProducts.map((product) => {
                    const fc = forecastMap[product.id];
                    const isHighDemand = fc && (fc.urgency === "CRITICAL" || fc.urgency === "HIGH");
                    const etaText =
                      fc?.stockout_eta_days !== null && fc?.stockout_eta_days !== undefined
                        ? `~${fc.stockout_eta_days} ngày`
                        : "Ổn định";

                    return (
                      <tr key={product.id} className="hover:bg-muted/30 transition-colors">
                        <td className="p-3 pl-4 font-medium text-foreground">
                          <div className="flex flex-col space-y-1">
                            <span>{product.name}</span>
                            {fc?.warning_badge && (
                              <div className="flex items-center gap-1 text-[11px] text-amber-500 font-medium">
                                <Flame className="h-3 w-3 shrink-0" />
                                <span>{fc.warning_badge}</span>
                              </div>
                            )}
                          </div>
                        </td>

                        <td className="p-3 font-mono text-muted-foreground">
                          {product.sku || "N/A"}
                        </td>

                        <td className="p-3">
                          <Badge variant="secondary" className="font-mono text-[10px] px-1.5 py-0 text-blue-500 bg-blue-500/10 border-blue-500/20">
                            {product.class_name?.startsWith("#") ? product.class_name : `#${product.class_name || "general"}`}
                          </Badge>
                        </td>

                        <td className="p-3 font-semibold text-foreground font-mono">
                          {new Intl.NumberFormat("vi-VN", { style: "currency", currency: "VND" }).format(product.price)}
                        </td>

                        <td className="p-3 font-mono">
                          <span
                            className={
                              (product.stock_quantity ?? 0) <= 5
                                ? "text-red-500 font-bold"
                                : (product.stock_quantity ?? 0) <= 10
                                ? "text-amber-500 font-semibold"
                                : "text-emerald-500"
                            }
                          >
                            {product.stock_quantity ?? 0}
                          </span>
                        </td>

                        <td className="p-3 font-mono text-muted-foreground">
                          {fc?.scan_count_7d || 0} scans
                        </td>

                        <td className="p-3">
                          <div className="flex items-center gap-1 text-[11px] font-mono">
                            <Clock className={`h-3 w-3 ${isHighDemand ? "text-red-500 animate-pulse" : "text-muted-foreground"}`} />
                            <span className={isHighDemand ? "text-red-500 font-bold" : "text-muted-foreground"}>
                              {etaText}
                            </span>
                          </div>
                        </td>

                        <td className="p-3 pr-4 text-right">
                          <Badge
                            variant="outline"
                            className={`text-[10px] ${
                              product.is_available
                                ? "text-emerald-600 border-emerald-500/30"
                                : "text-muted-foreground border-border"
                            }`}
                          >
                            {product.is_available ? "Sẵn sàng" : "Tạm ẩn"}
                          </Badge>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Product Creation Modal with Zero-Shot Auto-Classification */}
      <ProductCreateModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onSuccess={loadData}
      />
    </div>
  );
}
