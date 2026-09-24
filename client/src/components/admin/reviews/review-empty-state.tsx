"use client";

import * as React from "react";
import { CheckCircle2, Sparkles } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export function ReviewEmptyState() {
  return (
    <Card className="border-border bg-card/60 backdrop-blur-sm">
      <CardHeader>
        <CardTitle className="text-base font-semibold flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-cyan-500" />
          Hàng đợi kiểm duyệt nhãn AI
        </CardTitle>
        <CardDescription className="text-xs">
          Các phát hiện có độ tin cậy thấp hoặc ở trạng thái chờ duyệt
        </CardDescription>
      </CardHeader>
      <CardContent className="py-12 flex flex-col items-center justify-center text-center space-y-3">
        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-500">
          <CheckCircle2 className="h-6 w-6" />
        </div>
        <h3 className="font-semibold text-sm text-foreground">Hàng đợi đang trống</h3>
        <p className="text-xs text-muted-foreground max-w-sm">
          Mọi kết quả nhận diện camera gần đây đều đã được duyệt hoặc đạt độ tin cậy cao. Không có nhãn nào cần can thiệp.
        </p>
      </CardContent>
    </Card>
  );
}

