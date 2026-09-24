"use client";

import * as React from "react";
import Image from "next/image";
import { UploadCloud, Sparkles, Loader2, Plus, Tag } from "lucide-react";
import { toast } from "sonner";
import { adminService } from "@/services/admin.service";
import { productService } from "@/services/product.service";
import { apiClient } from "@/lib/api-client";
import type { Category, AutoTagResponse } from "@/types";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

interface ProductCreateModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export function ProductCreateModal({ isOpen, onClose, onSuccess }: ProductCreateModalProps) {
  const [categories, setCategories] = React.useState<Category[]>([]);
  const [selectedFile, setSelectedFile] = React.useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = React.useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = React.useState(false);
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const [aiTagResult, setAiTagResult] = React.useState<AutoTagResponse | null>(null);

  // Form State
  const [name, setName] = React.useState("");
  const [sku, setSku] = React.useState("");
  const [className, setClassName] = React.useState("");
  const [categoryId, setCategoryId] = React.useState("");
  const [price, setPrice] = React.useState("");
  const [stockQuantity, setStockQuantity] = React.useState("10");
  const [description, setDescription] = React.useState("");

  React.useEffect(() => {
    if (isOpen) {
      productService
        .getCategories()
        .then((res) => setCategories(res.data || []))
        .catch(() => {});
    }
  }, [isOpen]);

  const handleFileChange = async (file: File) => {
    setSelectedFile(file);
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);

    // Trigger Zero-Shot Auto-Classification
    setIsAnalyzing(true);
    try {
      const res = await adminService.autoTagProduct(file);
      const data = res.data;
      setAiTagResult(data);
      setClassName(data.tag || `#${data.class_name}`);
      if (data.suggested_category_id) {
        setCategoryId(data.suggested_category_id);
      }
      if (!name) {
        setName(`Sản phẩm ${data.label_vi} cao cấp`);
      }
      if (!sku) {
        setSku(`SKU-${data.class_name.toUpperCase()}-${Math.floor(1000 + Math.random() * 9000)}`);
      }
      toast.success(`AI nhận diện: ${data.label_vi} (${Math.round(data.confidence * 100)}%)`);
    } catch {
      toast.error("Không thể tự động phân tích ảnh.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !price) {
      toast.error("Vui lòng điền tên và giá sản phẩm.");
      return;
    }

    setIsSubmitting(true);
    try {
      await apiClient.post("/products", {
        name: name.trim(),
        sku: sku.trim() || undefined,
        class_name: className.trim().replace(/^#/, "").toLowerCase() || undefined,
        category_id: categoryId || undefined,
        price: parseFloat(price) || 0,
        stock_quantity: parseInt(stockQuantity, 10) || 0,
        image_url: previewUrl || undefined,
        description: description.trim() || undefined,
        is_available: true,
      });

      toast.success("Tạo sản phẩm và liên kết nhãn thị giác thành công!");
      onSuccess();
      onClose();
      // Reset form
      setSelectedFile(null);
      setPreviewUrl(null);
      setAiTagResult(null);
      setName("");
      setSku("");
      setClassName("");
      setCategoryId("");
      setPrice("");
      setStockQuantity("10");
      setDescription("");
    } catch (err: unknown) {
      const msg =
        err && typeof err === "object" && "response" in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : "Không thể lưu sản phẩm.";
      toast.error(String(msg));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-xl max-h-[90vh] flex flex-col p-0 overflow-hidden border-border bg-card">
        <DialogHeader className="p-5 pb-3 border-b border-border">
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-blue-500/10 text-blue-500">
              <Plus className="h-4 w-4" />
            </div>
            <DialogTitle className="text-base font-semibold">
              Tạo SKU Mới & Liên Kết Nhãn Thị Giác
            </DialogTitle>
          </div>
          <DialogDescription className="text-xs text-muted-foreground">
            Tải ảnh sản phẩm để AI tự động phân loại 80 lớp COCO chuẩn hoá Tiếng Việt và gợi ý danh mục.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-5 space-y-4 text-xs">
          {/* Visual Dropzone & AI Tagging Banner */}
          <div className="space-y-2">
            <label className="font-semibold text-foreground flex items-center justify-between">
              <span>Ảnh Sản Phẩm & Phân Tích Thị Giác</span>
              {isAnalyzing && (
                <span className="text-[11px] text-blue-500 flex items-center gap-1 font-mono">
                  <Loader2 className="h-3 w-3 animate-spin" />
                  Đang phân loại YOLO11...
                </span>
              )}
            </label>

            <div className="relative border-2 border-dashed border-border rounded-xl p-4 flex flex-col items-center justify-center bg-muted/20 hover:bg-muted/30 transition-colors">
              {previewUrl ? (
                <div className="flex items-center gap-4 w-full">
                  <div className="relative h-20 w-20 rounded-lg overflow-hidden border border-border shrink-0">
                    <Image src={previewUrl} alt="Preview" fill className="object-cover" />
                  </div>
                  <div className="flex-1 min-w-0 space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-foreground truncate max-w-40">
                        {selectedFile?.name}
                      </span>
                      {aiTagResult && (
                        <Badge className="bg-emerald-500/15 text-emerald-500 border border-emerald-500/30 gap-1 text-[10px]">
                          <Sparkles className="h-3 w-3" />
                          {aiTagResult.tag}
                        </Badge>
                      )}
                    </div>
                    <p className="text-[11px] text-muted-foreground">
                      {aiTagResult?.summary || "Đã tải ảnh lên thành công."}
                    </p>
                    <label className="inline-block text-[11px] text-primary hover:underline cursor-pointer">
                      Thay đổi ảnh khác
                      <input
                        type="file"
                        accept="image/*"
                        className="hidden"
                        onChange={(e) => e.target.files?.[0] && handleFileChange(e.target.files[0])}
                      />
                    </label>
                  </div>
                </div>
              ) : (
                <label className="flex flex-col items-center justify-center cursor-pointer py-4 w-full">
                  <UploadCloud className="h-8 w-8 text-muted-foreground mb-2" />
                  <span className="font-medium text-foreground">Kéo thả hoặc bấm để chọn ảnh SKU</span>
                  <span className="text-[11px] text-muted-foreground mt-0.5">
                    Hỗ trợ JPG, PNG, WEBP (Zero-Shot Auto-Classification)
                  </span>
                  <input
                    type="file"
                    accept="image/*"
                    className="hidden"
                    onChange={(e) => e.target.files?.[0] && handleFileChange(e.target.files[0])}
                  />
                </label>
              )}
            </div>
          </div>

          {/* Form Fields Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="space-y-1 sm:col-span-2">
              <label className="font-medium text-foreground">Tên sản phẩm *</label>
              <input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="VD: Laptop Gaming Asus ROG Strix"
                className="h-8 w-full rounded-md border border-border bg-background px-2.5 text-xs focus:outline-none focus:ring-1 focus:ring-primary"
              />
            </div>

            <div className="space-y-1">
              <label className="font-medium text-foreground flex items-center gap-1">
                <Tag className="h-3 w-3 text-blue-500" />
                <span>Mã nhãn AI (class_name)</span>
              </label>
              <input
                type="text"
                value={className}
                onChange={(e) => setClassName(e.target.value)}
                placeholder="VD: #laptop hoặc #bottle"
                className="h-8 w-full rounded-md border border-border bg-background px-2.5 font-mono text-xs focus:outline-none focus:ring-1 focus:ring-primary text-blue-500"
              />
            </div>

            <div className="space-y-1">
              <label className="font-medium text-foreground">Mã SKU</label>
              <input
                type="text"
                value={sku}
                onChange={(e) => setSku(e.target.value)}
                placeholder="VD: SKU-LAPTOP-001"
                className="h-8 w-full rounded-md border border-border bg-background px-2.5 font-mono text-xs focus:outline-none focus:ring-1 focus:ring-primary"
              />
            </div>

            <div className="space-y-1">
              <label className="font-medium text-foreground">Danh mục gợi ý</label>
              <select
                value={categoryId}
                onChange={(e) => setCategoryId(e.target.value)}
                className="h-8 w-full rounded-md border border-border bg-background px-2.5 text-xs focus:outline-none focus:ring-1 focus:ring-primary"
              >
                <option value="">-- Chưa chọn danh mục --</option>
                {categories.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-1">
              <label className="font-medium text-foreground">Đơn giá (VND) *</label>
              <input
                type="number"
                required
                min="0"
                step="1000"
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                placeholder="VD: 25000000"
                className="h-8 w-full rounded-md border border-border bg-background px-2.5 font-mono text-xs focus:outline-none focus:ring-1 focus:ring-primary"
              />
            </div>

            <div className="space-y-1">
              <label className="font-medium text-foreground">Lượng tồn kho</label>
              <input
                type="number"
                min="0"
                value={stockQuantity}
                onChange={(e) => setStockQuantity(e.target.value)}
                placeholder="VD: 15"
                className="h-8 w-full rounded-md border border-border bg-background px-2.5 font-mono text-xs focus:outline-none focus:ring-1 focus:ring-primary"
              />
            </div>

            <div className="space-y-1 sm:col-span-2">
              <label className="font-medium text-foreground">Mô tả sản phẩm</label>
              <textarea
                rows={2}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Mô tả tóm tắt thông số và công dụng sản phẩm..."
                className="w-full rounded-md border border-border bg-background p-2.5 text-xs focus:outline-none focus:ring-1 focus:ring-primary resize-none"
              />
            </div>
          </div>

          <DialogFooter className="pt-2 border-t border-border">
            <Button type="button" variant="outline" size="sm" onClick={onClose} disabled={isSubmitting}>
              Hủy
            </Button>
            <Button
              type="submit"
              size="sm"
              disabled={isSubmitting || isAnalyzing}
              className="bg-blue-600 hover:bg-blue-500 text-white gap-1.5"
            >
              {isSubmitting ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Plus className="h-3.5 w-3.5" />}
              <span>Lưu & Đồng Bộ AI</span>
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

