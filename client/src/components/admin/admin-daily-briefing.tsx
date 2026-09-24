"use client";

import * as React from "react";
import Link from "next/link";
import { Sparkles, ArrowRight, ShieldCheck, AlertTriangle, RefreshCw } from "lucide-react";
import { adminService } from "@/services/admin.service";
import type { ExecutiveDailyBriefingResponse } from "@/types";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

export function AdminDailyBriefing() {
  const [briefing, setBriefing] = React.useState<ExecutiveDailyBriefingResponse | null>(null);
  const [isLoading, setIsLoading] = React.useState(true);

  const loadBriefing = React.useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await adminService.getDailyBriefing();
      setBriefing(res.data);
    } catch {
      // Graceful fallback
    } finally {
      setIsLoading(false);
    }
  }, []);

  React.useEffect(() => {
    loadBriefing();
  }, [loadBriefing]);

  if (!briefing && !isLoading) return null;

  return (
    <Card className="relative overflow-hidden border border-indigo-500/20 bg-linear-to-r from-indigo-950/20 via-background to-purple-950/20 backdrop-blur-md">
      <div className="absolute top-0 right-0 h-32 w-32 bg-indigo-500/10 blur-3xl pointer-events-none" />
      <CardContent className="p-4 sm:p-5 space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <Badge className="gap-1.5 px-2.5 py-0.5 bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-[11px]">
              <Sparkles className="h-3 w-3 animate-pulse" />
              EXECUTIVE DAILY BRIEFING
            </Badge>
            <span className="text-[11px] text-muted-foreground font-mono">
              {briefing?.generated_at
                ? `Cập nhật: ${new Date(briefing.generated_at).toLocaleTimeString("vi-VN")}`
                : "Đang phân tích..."}
            </span>
          </div>

          <Button
            onClick={loadBriefing}
            variant="ghost"
            size="sm"
            disabled={isLoading}
            className="h-7 text-xs gap-1 text-muted-foreground hover:text-foreground self-start sm:self-auto cursor-pointer"
          >
            <RefreshCw className={`h-3 w-3 ${isLoading ? "animate-spin" : ""}`} />
            <span>Tái tổng hợp</span>
          </Button>
        </div>

        {/* Executive Summary */}
        <div className="space-y-1">
          <p className="text-sm sm:text-base font-medium text-foreground tracking-tight">
            {isLoading ? (
              <span className="inline-block h-5 w-3/4 rounded bg-muted animate-pulse" />
            ) : (
              briefing?.summary || "Hệ thống đang hoạt động ổn định và sẵn sàng xử lý yêu cầu."
            )}
          </p>
        </div>

        {/* Metric Badges & Action Shortcuts */}
        {!isLoading && briefing && (
          <div className="flex flex-wrap items-center gap-2 pt-1">
            {briefing.metrics.pending_reviews_count > 0 && (
              <Button
                asChild
                variant="outline"
                size="sm"
                className="h-7 text-xs gap-1.5 border-amber-500/30 text-amber-500 bg-amber-500/10 hover:bg-amber-500/20"
              >
                <Link href="/admin/reviews">
                  <ShieldCheck className="h-3.5 w-3.5" />
                  <span>Duyệt {briefing.metrics.pending_reviews_count} bản ghi AI</span>
                  <ArrowRight className="h-3 w-3" />
                </Link>
              </Button>
            )}

            {briefing.metrics.low_stock_count > 0 && (
              <Button
                asChild
                variant="outline"
                size="sm"
                className="h-7 text-xs gap-1.5 border-red-500/30 text-red-500 bg-red-500/10 hover:bg-red-500/20"
              >
                <Link href="/admin/products">
                  <AlertTriangle className="h-3.5 w-3.5" />
                  <span>Xử lý {briefing.metrics.low_stock_count} SKU tồn kho thấp</span>
                  <ArrowRight className="h-3 w-3" />
                </Link>
              </Button>
            )}

            <div className="hidden md:flex items-center gap-2 pl-2 border-l border-border text-xs text-muted-foreground font-mono">
              <span>Hôm nay: {briefing.metrics.scans_today} scans</span>
              <span>•</span>
              <span>
                Doanh thu:{" "}
                {new Intl.NumberFormat("vi-VN", { style: "currency", currency: "VND" }).format(
                  briefing.metrics.revenue_today
                )}
              </span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

