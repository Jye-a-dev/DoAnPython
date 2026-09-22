"use client";

import * as React from "react";
import Image from "next/image";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetFooter,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useCartStore } from "@/stores/cart-store";
import { formatVND } from "@/lib/utils";
import { resolveMediaUrl } from "@/lib/api-client";
import { Trash2, Plus, Minus, ShoppingBag, Volume2, CheckCircle2 } from "lucide-react";
import { toast } from "sonner";

export function CartDrawer() {
  const {
    items,
    totalItems,
    totalAmount,
    isOpen,
    closeCart,
    updateQuantity,
    removeItem,
    checkout,
    isCheckingOut,
    confirmationAudioUrl,
  } = useCartStore();

  const [address, setAddress] = React.useState("");
  const [phone, setPhone] = React.useState("");
  const [orderCompleted, setOrderCompleted] = React.useState(false);
  const [lastAudioUrl, setLastAudioUrl] = React.useState<string | null>(null);

  const handleCheckout = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!address.trim() || !phone.trim()) {
      toast.error("Vui lòng điền đầy đủ địa chỉ giao hàng và số điện thoại.");
      return;
    }

    const order = await checkout(address.trim(), phone.trim());
    if (order) {
      setOrderCompleted(true);
      const audioToPlay = resolveMediaUrl(order.audio_confirmation_url || confirmationAudioUrl);
      if (audioToPlay) {
        setLastAudioUrl(audioToPlay);
        try {
          const audio = new Audio(audioToPlay);
          audio.play().catch(() => {});
        } catch {}
      }
    }
  };

  const resetOrderState = () => {
    setOrderCompleted(false);
    setLastAudioUrl(null);
    setAddress("");
    setPhone("");
    closeCart();
  };

  return (
    <Sheet open={isOpen} onOpenChange={(open) => !open && resetOrderState()}>
      <SheetContent side="right" className="flex flex-col w-full sm:max-w-md p-6">
        <SheetHeader className="border-b pb-4">
          <SheetTitle className="flex items-center gap-2 text-lg font-bold">
            <ShoppingBag className="h-5 w-5 text-primary" />
            <span>Giỏ Hàng Của Bạn ({totalItems})</span>
          </SheetTitle>
        </SheetHeader>

        {orderCompleted ? (
          /* Order Confirmation Screen */
          <div className="flex-1 flex flex-col items-center justify-center text-center p-6 space-y-4">
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-emerald-500/10 text-emerald-500">
              <CheckCircle2 className="h-8 w-8" />
            </div>
            <h3 className="text-xl font-bold text-foreground">Đặt Hàng Thành Công!</h3>
            <p className="text-sm text-muted-foreground">
              Đơn hàng đã được xác nhận. Kho vận đang chuẩn bị đóng gói và vận chuyển đến bạn.
            </p>

            {lastAudioUrl && (
              <div className="w-full rounded-xl border border-primary/20 bg-primary/5 p-4 space-y-2">
                <div className="flex items-center justify-center gap-2 text-xs font-semibold text-primary">
                  <Volume2 className="h-4 w-4" />
                  <span>Xác nhận giọng đọc tự động (TTS):</span>
                </div>
                <audio controls autoPlay src={lastAudioUrl} className="w-full h-9" />
              </div>
            )}

            <Button onClick={resetOrderState} className="w-full mt-4">
              Tiếp tục mua sắm
            </Button>
          </div>
        ) : items.length === 0 ? (
          /* Empty Cart State */
          <div className="flex-1 flex flex-col items-center justify-center text-center p-6 space-y-3">
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-muted text-muted-foreground">
              <ShoppingBag className="h-8 w-8" />
            </div>
            <p className="font-semibold text-base">Giỏ hàng của bạn đang trống</p>
            <p className="text-xs text-muted-foreground">
              Hãy chọn những sản phẩm ưng ý hoặc quét ảnh bằng AI để mua sắm ngay.
            </p>
            <Button variant="outline" size="sm" onClick={closeCart} className="mt-2">
              Khám phá sản phẩm
            </Button>
          </div>
        ) : (
          /* Active Cart List & Checkout Form */
          <>
            <div className="flex-1 overflow-y-auto divide-y divide-border/60 pr-1 my-2">
              {items.map((item) => {
                const imgSrc =
                  item.product_image && item.product_image.startsWith("http")
                    ? item.product_image
                    : "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=200&auto=format&fit=crop&q=80";

                return (
                  <div key={item.id} className="py-3 flex items-center gap-3">
                    <div className="relative h-14 w-14 shrink-0 overflow-hidden rounded-lg border bg-muted/30">
                      <Image
                        src={imgSrc}
                        alt={item.product_name}
                        fill
                        sizes="56px"
                        className="object-cover"
                      />
                    </div>

                    <div className="flex-1 min-w-0">
                      <h4 className="text-sm font-semibold text-foreground truncate">
                        {item.product_name}
                      </h4>
                      <p className="text-xs font-bold text-primary">
                        {formatVND(item.product_price)}
                      </p>

                      {/* Quantity Controller */}
                      <div className="flex items-center gap-2 mt-1.5">
                        <Button
                          variant="outline"
                          size="icon"
                          className="h-6 w-6 rounded-md p-0"
                          onClick={() => updateQuantity(item.id, item.quantity - 1)}
                        >
                          <Minus className="h-3 w-3" />
                        </Button>
                        <span className="text-xs font-semibold px-1">{item.quantity}</span>
                        <Button
                          variant="outline"
                          size="icon"
                          className="h-6 w-6 rounded-md p-0"
                          onClick={() => updateQuantity(item.id, item.quantity + 1)}
                        >
                          <Plus className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>

                    <div className="flex flex-col items-end justify-between self-stretch">
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7 text-muted-foreground hover:text-destructive"
                        onClick={() => removeItem(item.id)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                      <span className="text-xs font-semibold text-foreground">
                        {formatVND(item.item_total)}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Subtotal & Checkout Form */}
            <div className="border-t pt-4 space-y-4">
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Tổng thanh toán:</span>
                <span className="text-lg font-extrabold text-primary">
                  {formatVND(totalAmount)}
                </span>
              </div>

              <form onSubmit={handleCheckout} className="space-y-3">
                <div>
                  <label className="text-xs font-semibold text-foreground mb-1 block">
                    Địa chỉ nhận hàng
                  </label>
                  <Input
                    required
                    placeholder="Số nhà, tên đường, phường/xã..."
                    value={address}
                    onChange={(e) => setAddress(e.target.value)}
                    className="text-xs"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-foreground mb-1 block">
                    Số điện thoại liên hệ
                  </label>
                  <Input
                    required
                    placeholder="Ví dụ: 0987654321"
                    type="tel"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    className="text-xs"
                  />
                </div>

                <SheetFooter className="pt-2">
                  <Button
                    type="submit"
                    disabled={isCheckingOut}
                    className="w-full gap-2 font-bold shadow-md bg-gradient-to-r from-primary to-blue-600"
                  >
                    {isCheckingOut ? (
                      <span>Đang xử lý & Tạo giọng đọc...</span>
                    ) : (
                      <>
                        <Volume2 className="h-4 w-4" />
                        <span>Xác Nhận & Đặt Hàng (TTS Voice)</span>
                      </>
                    )}
                  </Button>
                </SheetFooter>
              </form>
            </div>
          </>
        )}
      </SheetContent>
    </Sheet>
  );
}
