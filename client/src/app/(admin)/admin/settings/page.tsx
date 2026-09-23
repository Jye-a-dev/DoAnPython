"use client";

import * as React from "react";
import { Settings, Cpu, Radio, Save } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";

export default function AdminSettingsPage() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-6">
        <div>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="gap-1 px-2.5 py-0.5 text-amber-500 border-amber-500/30">
              <Settings className="h-3.5 w-3.5" />
              SYSTEM CONFIG
            </Badge>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">
              Cấu Hình Hệ Thống & Gateway
            </h1>
          </div>
          <p className="text-xs sm:text-sm text-muted-foreground mt-1">
            Điều chỉnh tham số pipeline nhận diện YOLO, ngưỡng tự tin và dịch vụ giọng nói Neural TTS.
          </p>
        </div>

        <Button size="sm" className="gap-1.5 text-xs bg-blue-600 hover:bg-blue-500 text-white">
          <Save className="h-3.5 w-3.5" />
          <span>Lưu thay đổi</span>
        </Button>
      </div>

      {/* Settings Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="border-border bg-card/60 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="text-sm font-semibold flex items-center gap-2">
              <Cpu className="h-4 w-4 text-blue-500" />
              YOLO11 Detection Engine
            </CardTitle>
            <CardDescription className="text-xs">
              Tham số mô hình thị giác máy tính và phân loại sản phẩm
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 text-xs">
            <div className="flex items-center justify-between py-2 border-b border-border/60">
              <span className="text-muted-foreground">Confidence Threshold</span>
              <span className="font-mono font-semibold">0.45 (45%)</span>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-border/60">
              <span className="text-muted-foreground">IoU NMS Threshold</span>
              <span className="font-mono font-semibold">0.50</span>
            </div>
            <div className="flex items-center justify-between py-2">
              <span className="text-muted-foreground">Model Weight</span>
              <span className="font-mono text-cyan-500">yolo11x-seg.pt</span>
            </div>
          </CardContent>
        </Card>

        <Card className="border-border bg-card/60 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="text-sm font-semibold flex items-center gap-2">
              <Radio className="h-4 w-4 text-indigo-500" />
              Edge Neural TTS Voice Engine
            </CardTitle>
            <CardDescription className="text-xs">
              Thiết lập giọng đọc mô tả sản phẩm và xác nhận giỏ hàng bằng giọng nói
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 text-xs">
            <div className="flex items-center justify-between py-2 border-b border-border/60">
              <span className="text-muted-foreground">Ngôn ngữ mặc định</span>
              <span className="font-semibold">vi-VN (Tiếng Việt)</span>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-border/60">
              <span className="text-muted-foreground">Voice ID</span>
              <span className="font-mono font-semibold">vi-VN-HoaiMyNeural</span>
            </div>
            <div className="flex items-center justify-between py-2">
              <span className="text-muted-foreground">Độ trễ tổng hợp trung bình</span>
              <span className="font-mono text-emerald-500">~120ms</span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

