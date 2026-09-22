"use client";

import * as React from "react";
import { Search, PackageX, Sparkles } from "lucide-react";
import { HeroSection } from "@/components/home/hero-section";
import { ProductCard } from "@/components/home/product-card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { apiClient } from "@/lib/api-client";
import { Product, Category } from "@/types";

export default function HomePage() {
  const [products, setProducts] = React.useState<Product[]>([]);
  const [categories, setCategories] = React.useState<Category[]>([]);
  const [selectedCategory, setSelectedCategory] = React.useState<string | null>(null);
  const [searchInput, setSearchInput] = React.useState("");
  const [debouncedSearch, setDebouncedSearch] = React.useState("");
  const [isLoading, setIsLoading] = React.useState(true);

  // Client-side debounce typing timer to eliminate input lag
  React.useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedSearch(searchInput.trim());
    }, 300);
    return () => clearTimeout(handler);
  }, [searchInput]);

  // Fetch product categories once
  React.useEffect(() => {
    async function loadCategories() {
      try {
        const response = await apiClient.get<Category[]>("/categories");
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
        const params: Record<string, string | number> = { limit: 50, skip: 0 };
        if (debouncedSearch) {
          params.search = debouncedSearch;
        }
        if (selectedCategory) {
          params.category_id = selectedCategory;
        }

        const response = await apiClient.get<Product[]>("/products", { params });
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
  }, [debouncedSearch, selectedCategory]);

  return (
    <div className="flex flex-col min-h-screen">
      {/* 1. Hero Section */}
      <HeroSection />

      {/* 2. Catalog Section */}
      <section id="catalog-section" className="container mx-auto px-4 sm:px-8 py-12 flex-1 space-y-8">
        {/* Header & Search Bar */}
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border-b pb-6">
          <div>
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-foreground flex items-center gap-2">
              <span>Kho Sản Phẩm Thông Minh</span>
              <Sparkles className="h-5 w-5 text-primary" />
            </h2>
            <p className="text-xs sm:text-sm text-muted-foreground mt-1">
              Tìm kiếm nhanh theo tên, mã SKU hoặc phân loại nhãn nhận diện AI
            </p>
          </div>

          {/* Debounced Search Input */}
          <div className="relative w-full md:w-80">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Tìm kiếm sản phẩm, SKU..."
              className="pl-9 pr-4 py-2 text-sm rounded-xl border-border"
            />
          </div>
        </div>

        {/* Category Filter Pills */}
        <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-none">
          <Button
            variant={selectedCategory === null ? "default" : "outline"}
            size="sm"
            onClick={() => setSelectedCategory(null)}
            className="rounded-full text-xs font-medium px-4"
          >
            Tất cả
          </Button>
          {categories.map((cat) => (
            <Button
              key={cat.id}
              variant={selectedCategory === cat.id ? "default" : "outline"}
              size="sm"
              onClick={() => setSelectedCategory(cat.id)}
              className="rounded-full text-xs font-medium px-4 whitespace-nowrap"
            >
              {cat.name}
            </Button>
          ))}
        </div>

        {/* Products Grid */}
        {isLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {Array.from({ length: 8 }).map((_, index) => (
              <div key={index} className="space-y-3 rounded-2xl border p-4">
                <Skeleton className="aspect-square w-full rounded-xl" />
                <Skeleton className="h-4 w-1/3" />
                <Skeleton className="h-5 w-3/4" />
                <div className="flex justify-between pt-2">
                  <Skeleton className="h-6 w-20" />
                  <Skeleton className="h-8 w-16 rounded-md" />
                </div>
              </div>
            ))}
          </div>
        ) : products.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {products.map((product) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed py-16 text-center space-y-3">
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-muted text-muted-foreground">
              <PackageX className="h-8 w-8" />
            </div>
            <h3 className="font-semibold text-lg">Không tìm thấy sản phẩm nào</h3>
            <p className="text-xs text-muted-foreground max-w-sm">
              Không có sản phẩm nào phù hợp với từ khóa &ldquo;{debouncedSearch}&rdquo;. Thử tìm kiếm với từ khóa khác hoặc quét ảnh AI.
            </p>
            {debouncedSearch && (
              <Button variant="outline" size="sm" onClick={() => setSearchInput("")} className="mt-2">
                Xóa bộ lọc tìm kiếm
              </Button>
            )}
          </div>
        )}
      </section>
    </div>
  );
}
