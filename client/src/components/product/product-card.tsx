"use client";

import * as React from "react";
import Image from "next/image";
import { Check, AlertCircle, Sparkles, Plus } from "lucide-react";
import { Product } from "@/types";
import { formatVND } from "@/lib/utils";
import { resolveMediaUrl } from "@/lib/api-client";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useCartStore } from "@/stores/cart-store";
import { useAuthStore } from "@/stores/auth-store";
import { toast } from "sonner";

interface ProductCardProps {
  product: Product;
  highlightMatch?: boolean;
  priority?: boolean;
}

function ProductCardComponent({ product, highlightMatch, priority = false }: ProductCardProps) {
  const { isAuthenticated } = useAuthStore();
  const { addToCart } = useCartStore();
  const [isAdding, setIsAdding] = React.useState(false);
  const [isAdded, setIsAdded] = React.useState(false);

  const isOutOfStock = !product.is_available || product.stock_quantity <= 0;

  const handleAddToCart = async () => {
    if (!isAuthenticated) {
      toast.error("Vui lòng đăng nhập để thêm hàng vào giỏ!");
      return;
    }

    setIsAdding(true);
    try {
      // Contract: product.id is UUID v4 string
      await addToCart(product.id, 1);
      setIsAdded(true);
      setTimeout(() => setIsAdded(false), 1500);
    } catch {
      // Error handled by store toast
    } finally {
      setIsAdding(false);
    }
  };

  // Pure memoized media resolution to prevent GC churn during scroll frames
  const imgSrc = React.useMemo(() => {
    return (
      resolveMediaUrl(product.image_url) ||
      "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=600&auto=format&fit=crop&q=80"
    );
  }, [product.image_url]);

  return (
    <div
      className={`group relative flex flex-col rounded-3xl p-4 transition-[transform,border-color,background-color] duration-200 transform-gpu ${
        highlightMatch
          ? "border border-cyan-400/80 bg-cyan-500/10 dark:bg-cyan-950/30 ring-2 ring-cyan-400/30 shadow-xl shadow-cyan-500/10 -translate-y-1"
          : "faux-glass-card hover:border-primary/40 hover:-translate-y-1 shadow-md"
      }`}
    >
      {/* Visual match badge */}
      {highlightMatch && (
        <div className="absolute top-5 left-5 z-20">
          <Badge className="gap-1 bg-linear-to-r from-cyan-500 to-blue-600 text-white font-bold shadow-md shadow-cyan-500/20 text-[11px] border-none">
            <Sparkles className="h-3 w-3" />
            Khớp ảnh AI
          </Badge>
        </div>
      )}

      {/* 4:3 Image Container with Floating AI Tag */}
      <div className="relative aspect-4/3 w-full overflow-hidden rounded-2xl bg-muted border border-border mb-3.5">
        <Image
          src={imgSrc}
          alt={product.name}
          fill
          priority={priority}
          loading={priority ? undefined : "lazy"}
          decoding="async"
          sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, (max-width: 1280px) 33vw, 25vw"
          className="object-cover transition-transform duration-300 ease-out group-hover:scale-105 transform-gpu"
        />

        {/* Floating AI Class Tag */}
        {product.class_name && (
          <div className="absolute bottom-2 left-2 z-10 flex items-center gap-1 rounded-md bg-background/95 px-2 py-0.5 text-[10px] font-mono font-semibold text-cyan-600 dark:text-cyan-300 border border-cyan-500/30 shadow-xs">
            <span>#{product.class_name}</span>
          </div>
        )}

        {/* Stock Status Badge Overlay */}
        <div className="absolute top-2.5 right-2.5 z-10">
          {isOutOfStock ? (
            <span className="inline-flex items-center gap-1 rounded-md bg-destructive px-2 py-0.5 text-[10px] font-semibold text-destructive-foreground shadow-sm">
              <AlertCircle className="h-3 w-3" />
              Hết hàng
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 rounded-md bg-background/95 px-2 py-0.5 text-[10px] font-semibold text-emerald-600 dark:text-emerald-400 border border-emerald-500/30 shadow-xs">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
              Còn hàng ({product.stock_quantity})
            </span>
          )}
        </div>
      </div>

      {/* Product Information */}
      <div className="flex flex-1 flex-col justify-between space-y-3">
        <div className="space-y-1">
          {product.sku && (
            <span className="text-[10px] font-mono text-muted-foreground tracking-wider">
              SKU: {product.sku}
            </span>
          )}

          <h3 className="font-semibold text-sm sm:text-base text-foreground line-clamp-1 group-hover:text-primary transition-colors">
            {product.name}
          </h3>

          {product.description && (
            <p className="text-xs text-muted-foreground line-clamp-2 leading-relaxed">
              {product.description}
            </p>
          )}
        </div>

        {/* Price & Hover Quick Add Action */}
        <div className="pt-2 flex items-center justify-between border-t border-border">
          <div className="flex flex-col">
            <span className="text-[10px] uppercase tracking-wider text-muted-foreground">Giá niêm yết</span>
            <span className="text-base sm:text-lg font-black text-cyan-600 dark:text-cyan-400">
              {formatVND(product.price)}
            </span>
          </div>

          <Button
            size="sm"
            disabled={isOutOfStock || isAdding}
            onClick={handleAddToCart}
            className={`gap-1.5 h-8 px-3 rounded-xl text-xs font-semibold transition-[background-color,transform] duration-150 cursor-pointer ${
              isAdded
                ? "bg-emerald-600 hover:bg-emerald-600 text-white"
                : "bg-linear-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white shadow-md shadow-blue-600/20"
            }`}
          >
            {isAdded ? (
              <>
                <Check className="h-3.5 w-3.5" />
                <span>Đã thêm</span>
              </>
            ) : (
              <>
                <Plus className="h-3.5 w-3.5" />
                <span>Thêm nhanh</span>
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}

export const ProductCard = React.memo(ProductCardComponent);
