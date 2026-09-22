"use client";

import * as React from "react";
import Image from "next/image";
import { ShoppingCart, Check, AlertCircle, Sparkles } from "lucide-react";
import { Product } from "@/types";
import { formatVND } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useCartStore } from "@/hooks/use-cart";
import { useAuthStore } from "@/hooks/use-auth";
import { toast } from "sonner";

interface ProductCardProps {
  product: Product;
  highlightMatch?: boolean;
}

export function ProductCard({ product, highlightMatch }: ProductCardProps) {
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
      await addToCart(product.id, 1);
      setIsAdded(true);
      setTimeout(() => setIsAdded(false), 1500);
    } catch {
      // Error handled by store toast
    } finally {
      setIsAdding(false);
    }
  };

  // Image fallback for local or placeholder images
  const imgSrc =
    product.image_url && product.image_url.startsWith("http")
      ? product.image_url
      : "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=600&auto=format&fit=crop&q=80";

  return (
    <div
      className={`group relative flex flex-col rounded-2xl border bg-card p-4 transition-all duration-300 hover:shadow-lg hover:-translate-y-1 ${
        highlightMatch
          ? "border-primary ring-2 ring-primary/30 shadow-md shadow-primary/10"
          : "border-border/60"
      }`}
    >
      {/* Visual match badge */}
      {highlightMatch && (
        <div className="absolute top-3 left-3 z-10">
          <Badge className="gap-1 bg-primary text-primary-foreground shadow-sm">
            <Sparkles className="h-3 w-3" />
            Khớp ảnh AI
          </Badge>
        </div>
      )}

      {/* Stock badge */}
      {isOutOfStock && (
        <div className="absolute top-3 right-3 z-10">
          <Badge variant="destructive" className="gap-1">
            <AlertCircle className="h-3 w-3" />
            Hết hàng
          </Badge>
        </div>
      )}

      {/* Image Thumbnail Container */}
      <div className="relative aspect-square w-full overflow-hidden rounded-xl bg-muted/50 mb-3">
        <Image
          src={imgSrc}
          alt={product.name}
          fill
          sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
          className="object-cover transition-transform duration-500 group-hover:scale-105"
        />
      </div>

      {/* Product Information */}
      <div className="flex flex-1 flex-col justify-between space-y-2">
        <div>
          <div className="flex items-center justify-between gap-2">
            {product.class_name && (
              <span className="text-[11px] font-semibold text-primary uppercase tracking-wide">
                {product.class_name}
              </span>
            )}
            <span className="text-xs text-muted-foreground ml-auto">
              Kho: {product.stock_quantity}
            </span>
          </div>

          <h3 className="font-semibold text-base text-foreground line-clamp-1 group-hover:text-primary transition-colors">
            {product.name}
          </h3>

          {product.description && (
            <p className="text-xs text-muted-foreground line-clamp-2 mt-1">
              {product.description}
            </p>
          )}
        </div>

        {/* Price & Add to Cart */}
        <div className="pt-2 flex items-center justify-between border-t border-border/40">
          <div className="flex flex-col">
            <span className="text-xs text-muted-foreground">Giá bán</span>
            <span className="text-lg font-bold text-primary">
              {formatVND(product.price)}
            </span>
          </div>

          <Button
            size="sm"
            disabled={isOutOfStock || isAdding}
            onClick={handleAddToCart}
            className={`gap-1.5 transition-all duration-200 ${
              isAdded
                ? "bg-emerald-600 hover:bg-emerald-600 text-white"
                : "bg-primary hover:bg-primary/90 text-primary-foreground"
            }`}
          >
            {isAdded ? (
              <>
                <Check className="h-4 w-4" />
                <span>Đã thêm</span>
              </>
            ) : (
              <>
                <ShoppingCart className="h-4 w-4" />
                <span>Thêm</span>
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}

