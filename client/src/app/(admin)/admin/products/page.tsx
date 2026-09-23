"use client";

import * as React from "react";
import { Boxes, Plus, Search, RefreshCw } from "lucide-react";
import { productService } from "@/services/product.service";
import { Product } from "@/types";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";

export default function AdminProductsPage() {
  const [products, setProducts] = React.useState<Product[]>([]);
  const [isLoading, setIsLoading] = React.useState(true);
  const [search, setSearch] = React.useState("");

  const loadProducts = React.useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await productService.getAll({ limit: 50 });
      setProducts(res.data || []);
    } catch {
      // Fallback empty
    } finally {
      setIsLoading(false);
    }
  }, []);

  React.useEffect(() => {
    loadProducts();
  }, [loadProducts]);

  const filteredProducts = products.filter(
    (p) =>
      p.name.toLowerCase().includes(search.toLowerCase()) ||
      p.sku?.toLowerCase().includes(search.toLowerCase()) ||
      p.class_name?.toLowerCase().includes(search.toLowerCase())
  );

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
            Điều chỉnh danh mục hàng hóa, đối chiếu class nhãn YOLO11 và theo dõi tồn kho.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            onClick={loadProducts}
            variant="outline"
            size="sm"
            className="gap-1.5 cursor-pointer text-xs"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isLoading ? "animate-spin" : ""}`} />
            <span>Làm mới</span>
          </Button>

          <Button size="sm" className="gap-1.5 text-xs bg-blue-600 hover:bg-blue-500 text-white">
            <Plus className="h-3.5 w-3.5" />
            <span>Thêm sản phẩm</span>
          </Button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex items-center justify-between gap-4">
        <div className="relative w-full max-w-sm">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Tìm theo tên, SKU, class nhãn..."
            className="h-9 w-full rounded-lg border border-border bg-card pl-8 pr-3 text-xs placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
          />
        </div>
        <span className="text-xs text-muted-foreground font-mono">
          Tổng cộng: {filteredProducts.length} SKU
        </span>
      </div>

      {/* Products Table Card */}
      <Card className="border-border bg-card/60 backdrop-blur-sm">
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left border-collapse">
              <thead>
                <tr className="border-b border-border bg-muted/30 text-muted-foreground font-semibold">
                  <th className="p-3 pl-4">Sản Phẩm</th>
                  <th className="p-3">SKU</th>
                  <th className="p-3">Class AI (YOLO)</th>
                  <th className="p-3">Đơn Giá</th>
                  <th className="p-3">Tồn Kho</th>
                  <th className="p-3 pr-4 text-right">Trạng Thái</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/60">
                {isLoading ? (
                  <tr>
                    <td colSpan={6} className="p-8 text-center text-muted-foreground">
                      <RefreshCw className="h-5 w-5 animate-spin mx-auto text-primary mb-2" />
                      Đang tải danh sách SKU...
                    </td>
                  </tr>
                ) : filteredProducts.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="p-8 text-center text-muted-foreground">
                      Không tìm thấy SKU nào phù hợp với từ khóa.
                    </td>
                  </tr>
                ) : (
                  filteredProducts.map((product) => (
                    <tr key={product.id} className="hover:bg-muted/30 transition-colors">
                      <td className="p-3 pl-4 font-medium text-foreground">
                        <div className="flex flex-col">
                          <span>{product.name}</span>
                          <span className="text-[10px] font-mono text-muted-foreground truncate max-w-50">
                            {product.id}
                          </span>
                        </div>
                      </td>
                      <td className="p-3 font-mono text-muted-foreground">{product.sku || "N/A"}</td>
                      <td className="p-3">
                        <Badge variant="secondary" className="font-mono text-[10px] px-1.5 py-0">
                          {product.class_name || "general"}
                        </Badge>
                      </td>
                      <td className="p-3 font-semibold text-foreground">
                        {new Intl.NumberFormat("vi-VN", { style: "currency", currency: "VND" }).format(product.price)}
                      </td>
                      <td className="p-3 font-mono">
                        <span className={(product.stock_quantity ?? 0) < 10 ? "text-amber-500 font-bold" : "text-emerald-500"}>
                          {product.stock_quantity ?? 0}
                        </span>
                      </td>
                      <td className="p-3 pr-4 text-right">
                        <Badge variant="outline" className="text-[10px] text-emerald-600 border-emerald-500/30">
                          Sẵn sàng
                        </Badge>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

