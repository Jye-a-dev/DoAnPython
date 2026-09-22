"use client";

import * as React from "react";
import { AlertCircle, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  React.useEffect(() => {
    // Log error to telemetry service (e.g. Sentry)
    console.error("Application runtime error:", error);
  }, [error]);

  return (
    <div className="flex flex-1 flex-col items-center justify-center p-6 text-center">
      <div className="flex size-14 items-center justify-center rounded-full bg-destructive/10 text-destructive mb-4">
        <AlertCircle className="size-8" />
      </div>
      <h2 className="text-2xl font-bold tracking-tight">Đã xảy ra sự cố không mong muốn</h2>
      <p className="mt-2 text-sm text-muted-foreground max-w-md">
        {error.message || "Hệ thống gặp lỗi trong quá trình xử lý yêu cầu của bạn. Vui lòng thử tải lại trang."}
      </p>
      {error.digest && (
        <p className="mt-1 font-mono text-xs text-muted-foreground/60">
          Mã lỗi: {error.digest}
        </p>
      )}
      <div className="mt-6 flex items-center gap-3">
        <Button onClick={() => reset()} className="gap-2">
          <RotateCcw className="size-4" />
          <span>Thử lại</span>
        </Button>
        <Button variant="outline" onClick={() => (window.location.href = "/")}>
          Về trang chủ
        </Button>
      </div>
    </div>
  );
}

