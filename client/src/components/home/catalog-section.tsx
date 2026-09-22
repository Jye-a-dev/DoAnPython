"use client";

import * as React from "react";
import { Search, Sparkles, SlidersHorizontal, PackageX } from "lucide-react";
import { ProductCard } from "@/components/product/product-card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { productService } from "@/services";
import { Product, Category } from "@/types";

export function CatalogSection() {
  const [products, setProducts] = React.useState<Product[]>([]);
  const [categories, setCategories] = React.useState<Category[]>([]);
  const [selectedCategory, setSelectedCategory] = React.useState<string | null>(null);

  // Local responsive input state with native typing response
  const [searchInput, setSearchInput] = React.useState("");
  const deferredSearch = React.useDeferredValue(searchInput);
  const [, startTransition] = React.useTransition();
  const [activeSearch, setActiveSearch] = React.useState("");
  const [isLoading, setIsLoading] = React.useState(true);

  // Low-priority transition debounce for catalog filtering
  React.useEffect(() => {
    const handler = setTimeout(() => {
      startTransition(() => {
        setActiveSearch(deferredSearch.trim());
      });
    }, 250);
    return () => clearTimeout(handler);
  }, [deferredSearch]);

  // Fetch product categories once
  React.useEffect(() => {
    async function loadCategories() {
      try {
        const response = await productService.getCategories();
        setCategories(response.data || []);
      } catch {
        // Fallback gracefully
      }
    }
    loadCategories();
  }, []);

  // Fetch products upon search or category filter change
  React.useEffect(() => {
    let isCancelled = false;

    async function loadProducts() {
      setIsLoading(true);
      try {
        const params: { limit?: number; skip?: number; search?: string; category_id?: string } = { limit: 50, skip: 0 };
        if (activeSearch) {
          params.search = activeSearch;
        }
        if (selectedCategory) {
          params.category_id = selectedCategory;
        }

        const response = await productService.getAll(params);
        if (!isCancelled) {
          setProducts(response.data || []);
        }
      } catch {
        if (!isCancelled) {
          setProducts([]);
        }
      } finally {
        if (!isCancelled) {
          setIsLoading(false);
        }
      }
    }

    loadProducts();

    return () => {
      isCancelled = true;
    };
  }, [activeSearch, selectedCategory]);

  return (
    <section id="catalog-section" className="container mx-auto px-4 sm:px-8 py-16 flex-1 space-y-8">
      {/* Header & Search Bar */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6 border-b border-border pb-6">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-foreground">
              Kho Sản Phẩm Thông Minh
            </h2>
            <Sparkles className="h-5 w-5 text-cyan-500 dark:text-cyan-400" />
          </div>
          <p className="text-xs sm:text-sm text-muted-foreground">
            Tìm kiếm nhanh theo tên, mã SKU hoặc phân loại nhãn nhận diện AI
          </p>
        </div>

        {/* Search Input with Local Sync State */}
        <div className="relative w-full md:w-80">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
          <Input
            id="catalog-search-input"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Tìm kiếm sản phẩm, SKU, nhãn AI..."
            className="pl-10 pr-4 py-2 text-xs sm:text-sm rounded-2xl border-border bg-muted/60 text-foreground placeholder:text-muted-foreground focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/50"
          />
        </div>
      </div>

      {/* Category Filter Pills */}
      <div className="flex items-center gap-2.5 overflow-x-auto pb-2 scrollbar-none">
        <div className="flex items-center gap-1.5 text-xs text-muted-foreground mr-2 shrink-0">
          <SlidersHorizontal className="h-3.5 w-3.5 text-muted-foreground" />
          <span className="hidden sm:inline">Phân loại:</span>
        </div>

        <Button
          variant={selectedCategory === null ? "default" : "outline"}
          size="sm"
          onClick={() => setSelectedCategory(null)}
          className={`rounded-full text-xs font-semibold px-4.5 transition-colors cursor-pointer ${
            selectedCategory === null
              ? "bg-linear-to-r from-blue-600 to-indigo-600 text-white shadow-md shadow-blue-600/20"
              : "border-border bg-muted/40 text-muted-foreground hover:text-foreground hover:bg-muted"
          }`}
        >
          Tất cả
        </Button>

        {categories.map((cat) => (
          <Button
            key={cat.id}
            variant={selectedCategory === cat.id ? "default" : "outline"}
            size="sm"
            onClick={() => setSelectedCategory(cat.id)}
          className={`rounded-full text-xs font-semibold px-4.5 whitespace-nowrap transition-colors cursor-pointer ${
              selectedCategory === cat.id
                ? "bg-linear-to-r from-blue-600 to-indigo-600 text-white shadow-md shadow-blue-600/20"
                : "border-border bg-muted/40 text-muted-foreground hover:text-foreground hover:bg-muted"
            }`}
          >
            {cat.name}
          </Button>
        ))}
      </div>

      {/* Total Products Counter & Filter Status */}
      <div className="flex items-center justify-between text-xs text-muted-foreground px-1">
        <span>
          Hiển thị <strong className="text-foreground">{products.length}</strong> sản phẩm có sẵn
        </span>
        {activeSearch && (
          <Badge variant="outline" className="border-cyan-500/30 text-cyan-600 dark:text-cyan-300 text-[11px]">
            Từ khóa: &ldquo;{activeSearch}&rdquo;
          </Badge>
        )}
      </div>

      {/* Products Grid with content-visibility isolation */}
      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
          {Array.from({ length: 8 }).map((_, index) => (
            <div
              key={index}
              className="space-y-3 rounded-3xl border border-border bg-card/80 p-4 shadow-sm"
            >
              <Skeleton className="aspect-4/3 w-full rounded-2xl bg-muted" />
              <Skeleton className="h-4 w-1/3 bg-muted" />
              <Skeleton className="h-5 w-3/4 bg-muted" />
              <div className="flex justify-between pt-2 border-t border-border/50">
                <Skeleton className="h-6 w-20 bg-muted" />
                <Skeleton className="h-8 w-20 rounded-xl bg-muted" />
              </div>
            </div>
          ))}
        </div>
      ) : products.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
          {products.map((product, index) => (
            <div key={product.id} className="content-visibility-card">
              <ProductCard product={product} priority={index < 4} />
            </div>
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center rounded-3xl border border-dashed border-border bg-card/30 py-16 text-center space-y-4">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-muted text-muted-foreground">
            <PackageX className="h-8 w-8" />
          </div>
          <div className="space-y-1">
            <h3 className="font-bold text-lg text-foreground">Không tìm thấy sản phẩm nào</h3>
            <p className="text-xs text-muted-foreground max-w-sm">
              Không có sản phẩm nào phù hợp với bộ lọc hoặc từ khóa &ldquo;{activeSearch}&rdquo;. Thử tìm kiếm với từ khóa khác hoặc quét ảnh AI.
            </p>
          </div>
          {activeSearch && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => setSearchInput("")}
              className="rounded-full border-border bg-muted/50 text-xs text-foreground hover:bg-muted"
            >
              Xóa bộ lọc tìm kiếm
            </Button>
          )}
        </div>
      )}
    </section>
  );
}