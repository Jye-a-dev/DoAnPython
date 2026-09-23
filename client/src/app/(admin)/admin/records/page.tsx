"use client";

import * as React from "react";
import { FileSearch, RefreshCw, Eye } from "lucide-react";
import { adminService } from "@/services/admin.service";
import { DetectionRecord } from "@/types";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";

export default function AdminRecordsPage() {
  const [records, setRecords] = React.useState<DetectionRecord[]>([]);
  const [isLoading, setIsLoading] = React.useState(true);

  const loadRecords = React.useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await adminService.getDetectionHistory({ limit: 20, skip: 0 });
      setRecords(res.data?.records || []);
    } catch {
      // Fallback empty
    } finally {
      setIsLoading(false);
    }
  }, []);

  React.useEffect(() => {
    loadRecords();
  }, [loadRecords]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-6">
        <div>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="gap-1 px-2.5 py-0.5 text-indigo-500 border-indigo-500/30">
              <FileSearch className="h-3.5 w-3.5" />
              VISION AUDIT LOGS
            </Badge>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">
              Nhật Ký Nhận Diện AI
            </h1>
          </div>
          <p className="text-xs sm:text-sm text-muted-foreground mt-1">
            Tra cứu lịch sử quét ảnh YOLO11, bounding boxes và file âm thanh Neural TTS.
          </p>
        </div>

        <Button
          onClick={loadRecords}
          variant="outline"
          size="sm"
          className="gap-1.5 cursor-pointer text-xs"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${isLoading ? "animate-spin" : ""}`} />
          <span>Làm mới dữ liệu</span>
        </Button>
      </div>

      {/* Table Card */}
      <Card className="border-border bg-card/60 backdrop-blur-sm">
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left border-collapse">
              <thead>
                <tr className="border-b border-border bg-muted/30 text-muted-foreground font-semibold">
                  <th className="p-3 pl-4">Record ID (UUID v4)</th>
                  <th className="p-3">Thời Điểm</th>
                  <th className="p-3">Số Vật Thể</th>
                  <th className="p-3">Tóm Tắt Nhận Diện</th>
                  <th className="p-3">Trạng Thái</th>
                  <th className="p-3 pr-4 text-right">Chi Tiết</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/60">
                {isLoading ? (
                  <tr>
                    <td colSpan={6} className="p-8 text-center text-muted-foreground">
                      <RefreshCw className="h-5 w-5 animate-spin mx-auto text-primary mb-2" />
                      Đang tải nhật ký nhận diện...
                    </td>
                  </tr>
                ) : records.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="p-8 text-center text-muted-foreground">
                      Chưa có nhật ký nhận diện nào được ghi nhận.
                    </td>
                  </tr>
                ) : (
                  records.map((rec) => (
                    <tr key={rec.id} className="hover:bg-muted/30 transition-colors">
                      <td className="p-3 pl-4 font-mono text-muted-foreground truncate max-w-37.5">
                        {rec.id}
                      </td>
                      <td className="p-3 text-muted-foreground">
                        {rec.created_at ? new Date(rec.created_at).toLocaleString("vi-VN") : "N/A"}
                      </td>
                      <td className="p-3">
                        <Badge variant="secondary" className="font-mono text-[10px]">
                          {rec.objects?.length || 0} objects
                        </Badge>
                      </td>
                      <td className="p-3 max-w-xs truncate text-foreground font-medium">
                        {rec.summary || "Nhận diện vật thể thông minh"}
                      </td>
                      <td className="p-3">
                        <Badge
                          variant="outline"
                          className="text-[10px] text-emerald-600 border-emerald-500/30 font-mono"
                        >
                          {rec.status || "COMPLETED"}
                        </Badge>
                      </td>
                      <td className="p-3 pr-4 text-right">
                        <Button variant="ghost" size="icon" className="h-7 w-7 text-muted-foreground hover:text-foreground">
                          <Eye className="h-3.5 w-3.5" />
                        </Button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

