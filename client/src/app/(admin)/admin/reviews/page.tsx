"use client";

import * as React from "react";
import { CheckCircle2, RefreshCw, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";

export default function AdminReviewsPage() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-6">
        <div>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="gap-1 px-2.5 py-0.5 text-cyan-500 border-cyan-500/30">
              <CheckCircle2 className="h-3.5 w-3.5" />
              OCR & LABEL AUDIT
            </Badge>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">
              Kiểm Duyệt AI & OCR
            </h1>
          </div>
          <p className="text-xs sm:text-sm text-muted-foreground mt-1">
            Thẩm định độ tin cậy nhãn nhận diện, hiệu chỉnh văn bản OCR và gắn nhãn huấn luyện lại model.
          </p>
        </div>

        <Button variant="outline" size="sm" className="gap-1.5 cursor-pointer text-xs">
          <RefreshCw className="h-3.5 w-3.5" />
          <span>Làm mới hàng đợi</span>
        </Button>
      </div>

      {/* Queue Status Card */}
      <Card className="border-border bg-card/60 backdrop-blur-sm">
        <CardHeader>
          <CardTitle className="text-base font-semibold flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-cyan-500" />
            Hàng đợi kiểm duyệt nhãn AI
          </CardTitle>
          <CardDescription className="text-xs">
            Các phát hiện có độ tin cậy (confidence) thấp cần quản trị viên đối soát thủ công
          </CardDescription>
        </CardHeader>
        <CardContent className="py-12 flex flex-col items-center justify-center text-center space-y-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-500">
            <CheckCircle2 className="h-6 w-6" />
          </div>
          <h3 className="font-semibold text-sm text-foreground">
            Hàng đợi đang trống
          </h3>
          <p className="text-xs text-muted-foreground max-w-sm">
            Mọi kết quả nhận diện gần đây từ mô hình YOLO11 đều đạt ngưỡng tin cậy trên 85%. Không có nhãn OCR nào cần can thiệp.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}

