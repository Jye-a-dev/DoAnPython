"use client";

import * as React from "react";
import {
  Settings,
  Cpu,
  Radio,
  Save,
  Activity,
  AlertTriangle,
  Download,
  Sparkles,
  RefreshCw,
} from "lucide-react";
import { toast } from "sonner";
import { adminService } from "@/services/admin.service";
import type { ModelDriftResponse } from "@/types";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";

export default function AdminSettingsPage() {
  const [driftData, setDriftData] = React.useState<ModelDriftResponse | null>(null);
  const [isLoadingDrift, setIsLoadingDrift] = React.useState(true);
  const [isExporting, setIsExporting] = React.useState(false);

  const loadDrift = React.useCallback(async () => {
    setIsLoadingDrift(true);
    try {
      const res = await adminService.getModelDrift();
      setDriftData(res.data);
    } catch {
      // Fallback
    } finally {
      setIsLoadingDrift(false);
    }
  }, []);

  React.useEffect(() => {
    loadDrift();
  }, [loadDrift]);

  const handleExportRetrainDataset = async () => {
    setIsExporting(true);
    try {
      const res = await adminService.exportRetrainDataset();
      const blob = new Blob([res.data], { type: "application/json" });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "yolo11_oov_retrain_dataset.json";
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      toast.success("Đã xuất dataset huấn luyện lại thành công!");
    } catch {
      toast.error("Xuất dataset huấn luyện thất bại.");
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-6">
        <div>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="gap-1 px-2.5 py-0.5 text-amber-500 border-amber-500/30">
              <Settings className="h-3.5 w-3.5" />
              SYSTEM CONFIG & MLOPS
            </Badge>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">
              Cấu Hình Hệ Thống & Giám Sát MLOps
            </h1>
          </div>
          <p className="text-xs sm:text-sm text-muted-foreground mt-1">
            Điều chỉnh tham số pipeline nhận diện YOLO, theo dõi độ lệch mô hình (Model Drift) và hàng đợi gắn nhãn từ vựng mới (OOV).
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            onClick={loadDrift}
            variant="outline"
            size="sm"
            disabled={isLoadingDrift}
            className="gap-1.5 cursor-pointer text-xs"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isLoadingDrift ? "animate-spin" : ""}`} />
            <span>Cập nhật telemetry</span>
          </Button>

          <Button size="sm" className="gap-1.5 text-xs bg-blue-600 hover:bg-blue-500 text-white cursor-pointer">
            <Save className="h-3.5 w-3.5" />
            <span>Lưu thay đổi</span>
          </Button>
        </div>
      </div>

      {/* MLOps Model Drift & Telemetry Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Activity className="h-4 w-4 text-purple-500" />
            <h2 className="text-base font-semibold text-foreground">
              MLOps: Cảnh Báo Lệch Mô Hình & Từ Vựng Mới (Model Drift & OOV)
            </h2>
          </div>
          <Button
            onClick={handleExportRetrainDataset}
            disabled={isExporting}
            variant="outline"
            size="sm"
            className="h-7 text-xs gap-1.5 border-purple-500/30 text-purple-500 hover:bg-purple-500/10 cursor-pointer"
          >
            <Download className="h-3.5 w-3.5" />
            <span>Xuất Retrain Dataset</span>
          </Button>
        </div>

        {/* Telemetry KPI Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Card className="border-border bg-card/60 backdrop-blur-sm">
            <CardContent className="p-4 space-y-1">
              <span className="text-xs text-muted-foreground">Chỉ Số Lệch Mô Hình (Drift Rate)</span>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold font-mono text-purple-400">
                  {driftData?.drift_score || 0}%
                </span>
                <span className="text-[11px] text-muted-foreground">
                  ({driftData?.low_confidence_count || 0} ca thấp, {driftData?.corrected_count || 0} ca đã sửa)
                </span>
              </div>
              <p className="text-[10px] text-muted-foreground">
                Tỷ lệ phát hiện có độ tin cậy &lt; 40% hoặc bị admin hiệu chỉnh lại
              </p>
            </CardContent>
          </Card>

          <Card className="border-border bg-card/60 backdrop-blur-sm">
            <CardContent className="p-4 space-y-1">
              <span className="text-xs text-muted-foreground">Từ Vựng Mới Phát Hiện (OOV Terms)</span>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold font-mono text-cyan-400">
                  {driftData?.oov_terms.length || 0}
                </span>
                <span className="text-[11px] text-muted-foreground">nhãn ngoài 80 lớp COCO</span>
              </div>
              <p className="text-[10px] text-muted-foreground">
                Các từ vựng thường xuất hiện trong ghi chú sửa đổi của Admin
              </p>
            </CardContent>
          </Card>

          <Card className="border-border bg-card/60 backdrop-blur-sm">
            <CardContent className="p-4 space-y-1">
              <span className="text-xs text-muted-foreground">Hàng Đợi Huấn Luyện (Retrain Queue)</span>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold font-mono text-amber-400">
                  {driftData?.retrain_queue.length || 0}
                </span>
                <span className="text-[11px] text-muted-foreground">mẫu sẵn sàng fine-tune</span>
              </div>
              <p className="text-[10px] text-muted-foreground">
                Đã gắn nhãn chuẩn xác để nạp vào phiên bản YOLO11 kế tiếp
              </p>
            </CardContent>
          </Card>
        </div>

        {/* OOV Terms & Retrain Queue Table */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <Card className="border-border bg-card/60 backdrop-blur-sm">
            <CardHeader className="p-4 pb-2 border-b border-border/80">
              <CardTitle className="text-xs font-semibold flex items-center gap-1.5">
                <Sparkles className="h-3.5 w-3.5 text-cyan-500" />
                <span>Từ Vựng Ngoài Danh Mục (Out-of-Vocabulary)</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <div className="max-h-56 overflow-y-auto">
                <table className="w-full text-xs text-left border-collapse">
                  <thead>
                    <tr className="border-b border-border bg-muted/30 text-muted-foreground font-semibold">
                      <th className="p-2.5 pl-4">Từ Vựng / Nhãn</th>
                      <th className="p-2.5">Số Lần Xuất Hiện</th>
                      <th className="p-2.5 pr-4 text-right">Danh Mục Đề Xuất</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border/60">
                    {driftData?.oov_terms.length === 0 ? (
                      <tr>
                        <td colSpan={3} className="p-4 text-center text-muted-foreground text-xs">
                          Chưa phát hiện từ vựng mới nào nằm ngoài COCO.
                        </td>
                      </tr>
                    ) : (
                      driftData?.oov_terms.map((item, idx) => (
                        <tr key={idx} className="hover:bg-muted/30 font-mono text-[11px]">
                          <td className="p-2.5 pl-4 font-semibold text-foreground">
                            #{item.term}
                          </td>
                          <td className="p-2.5 text-cyan-500">{item.occurrences} lần</td>
                          <td className="p-2.5 pr-4 text-right text-muted-foreground">
                            {item.suggested_category || "Mở rộng"}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>

          <Card className="border-border bg-card/60 backdrop-blur-sm">
            <CardHeader className="p-4 pb-2 border-b border-border/80">
              <CardTitle className="text-xs font-semibold flex items-center gap-1.5">
                <AlertTriangle className="h-3.5 w-3.5 text-amber-500" />
                <span>Hàng Đợi Huấn Luyện Lại (Retrain Queue)</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <div className="max-h-56 overflow-y-auto">
                <table className="w-full text-xs text-left border-collapse">
                  <thead>
                    <tr className="border-b border-border bg-muted/30 text-muted-foreground font-semibold">
                      <th className="p-2.5 pl-4">ID Bản Ghi</th>
                      <th className="p-2.5">Nhãn Gốc</th>
                      <th className="p-2.5">Nhãn Chuẩn (Ground Truth)</th>
                      <th className="p-2.5 pr-4 text-right">Lý Do</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border/60">
                    {driftData?.retrain_queue.length === 0 ? (
                      <tr>
                        <td colSpan={4} className="p-4 text-center text-muted-foreground text-xs">
                          Hàng đợi huấn luyện lại đang trống.
                        </td>
                      </tr>
                    ) : (
                      driftData?.retrain_queue.map((item, idx) => (
                        <tr key={idx} className="hover:bg-muted/30 text-[11px]">
                          <td className="p-2.5 pl-4 font-mono text-muted-foreground truncate max-w-24">
                            {item.record_id.slice(0, 8)}
                          </td>
                          <td className="p-2.5 truncate max-w-28 text-muted-foreground line-through">
                            {item.raw_detected_text}
                          </td>
                          <td className="p-2.5 truncate max-w-28 font-medium text-emerald-500">
                            {item.corrected_text}
                          </td>
                          <td className="p-2.5 pr-4 text-right text-amber-500 text-[10px]">
                            {item.reason}
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
      </div>

      {/* Engine Parameters Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4 border-t border-border">
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
              <span className="font-mono font-semibold">0.35 (35%)</span>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-border/60">
              <span className="text-muted-foreground">IoU NMS Threshold</span>
              <span className="font-mono font-semibold">0.50</span>
            </div>
            <div className="flex items-center justify-between py-2">
              <span className="text-muted-foreground">Model Weight</span>
              <span className="font-mono text-cyan-500">yolo11m.pt</span>
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
              Chuỗi tổng hợp 3 tầng (edge-tts -&gt; gTTS -&gt; pyttsx3)
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
