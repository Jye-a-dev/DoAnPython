"use client";

import * as React from "react";
import Image from "next/image";
import {
  FileSearch,
  RefreshCw,
  Eye,
  Download,
  Filter,
  Layers,
  Sparkles,
} from "lucide-react";
import { toast } from "sonner";
import { adminService } from "@/services/admin.service";
import { resolveMediaUrl } from "@/lib/api-client";
import type { DetectionRecord, ErrorClusterItem } from "@/types";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";

export default function AdminRecordsPage() {
  const [records, setRecords] = React.useState<DetectionRecord[]>([]);
  const [clusters, setClusters] = React.useState<ErrorClusterItem[]>([]);
  const [activeCluster, setActiveCluster] = React.useState<string>("all");
  const [isLoading, setIsLoading] = React.useState(true);
  const [isExporting, setIsExporting] = React.useState(false);

  // Detail Modal State
  const [selectedRecord, setSelectedRecord] = React.useState<DetectionRecord | null>(null);

  const loadData = React.useCallback(async () => {
    setIsLoading(true);
    try {
      const [recRes, clusterRes] = await Promise.all([
        adminService.getDetectionHistory({ limit: 50, skip: 0 }),
        adminService.getErrorClusters().catch(() => null),
      ]);

      const raw = Array.isArray(recRes.data) ? recRes.data : [];
      setRecords(raw);

      if (clusterRes?.data?.clusters) {
        setClusters(clusterRes.data.clusters);
      }
    } catch {
      toast.error("Không thể tải nhật ký nhận diện.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  React.useEffect(() => {
    loadData();
  }, [loadData]);

  const handleExportDataset = async () => {
    setIsExporting(true);
    try {
      const res = await adminService.exportRetrainDataset(
        activeCluster === "all" ? undefined : activeCluster
      );
      const blob = new Blob([res.data], { type: "application/json" });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `yolo11_retrain_dataset_${activeCluster}.json`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      toast.success("Đã xuất dataset huấn luyện thành công!");
    } catch {
      toast.error("Xuất dataset huấn luyện thất bại.");
    } finally {
      setIsExporting(false);
    }
  };

  // Filter records based on selected cluster IDs
  const filteredRecords = React.useMemo(() => {
    if (activeCluster === "all") return records;
    const targetCluster = clusters.find((c) => c.cluster_id === activeCluster);
    if (!targetCluster) return records;
    const idSet = new Set(targetCluster.record_ids);
    return records.filter((r) => idSet.has(r.id));
  }, [records, clusters, activeCluster]);

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
              Nhật Ký & Gom Nhóm Lỗi Nhận Diện
            </h1>
          </div>
          <p className="text-xs sm:text-sm text-muted-foreground mt-1">
            Phân loại cụm lỗi (thiếu sáng, bị che khuất, chồng chéo) và xuất dataset huấn luyện cho model YOLO11.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            onClick={loadData}
            variant="outline"
            size="sm"
            disabled={isLoading}
            className="gap-1.5 cursor-pointer text-xs"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isLoading ? "animate-spin" : ""}`} />
            <span>Làm mới</span>
          </Button>

          <Button
            onClick={handleExportDataset}
            disabled={isExporting}
            size="sm"
            className="gap-1.5 text-xs bg-indigo-600 hover:bg-indigo-500 text-white cursor-pointer"
          >
            <Download className="h-3.5 w-3.5" />
            <span>Xuất Dataset (YOLO Format)</span>
          </Button>
        </div>
      </div>

      {/* Error Clustering Tabs Bar */}
      <div className="space-y-2">
        <div className="flex items-center gap-2 text-xs font-semibold text-muted-foreground">
          <Layers className="h-3.5 w-3.5 text-indigo-500" />
          <span>Gom nhóm lỗi nhận diện AI (Error Clusters):</span>
        </div>

        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => setActiveCluster("all")}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all cursor-pointer flex items-center gap-1.5 ${
              activeCluster === "all"
                ? "bg-primary text-primary-foreground shadow-sm"
                : "bg-card border border-border text-muted-foreground hover:bg-muted/50"
            }`}
          >
            <Filter className="h-3 w-3" />
            <span>Tất cả ({records.length})</span>
          </button>

          {clusters.map((cluster) => {
            const isActive = activeCluster === cluster.cluster_id;
            return (
              <button
                key={cluster.cluster_id}
                onClick={() => setActiveCluster(cluster.cluster_id)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all cursor-pointer flex items-center gap-1.5 ${
                  isActive
                    ? "bg-indigo-600 text-white shadow-sm"
                    : "bg-card border border-border text-muted-foreground hover:bg-muted/50"
                }`}
              >
                <span>{cluster.cluster_name}</span>
                <Badge
                  variant="secondary"
                  className={`text-[10px] px-1 py-0 font-mono ${
                    isActive ? "bg-white/20 text-white" : ""
                  }`}
                >
                  {cluster.count}
                </Badge>
              </button>
            );
          })}
        </div>
      </div>

      {/* Records Table Card */}
      <Card className="border-border bg-card/60 backdrop-blur-sm">
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left border-collapse">
              <thead>
                <tr className="border-b border-border bg-muted/30 text-muted-foreground font-semibold">
                  <th className="p-3 pl-4">Record ID</th>
                  <th className="p-3">Thời Điểm Quét</th>
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
                      Đang phân loại và gom cụm dữ liệu...
                    </td>
                  </tr>
                ) : filteredRecords.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="p-8 text-center text-muted-foreground">
                      Không có bản ghi nào trong cụm lỗi đã chọn.
                    </td>
                  </tr>
                ) : (
                  filteredRecords.map((rec) => (
                    <tr key={rec.id} className="hover:bg-muted/30 transition-colors">
                      <td className="p-3 pl-4 font-mono text-muted-foreground truncate max-w-36">
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
                        {rec.summary || rec.raw_detected_text || "Nhận diện vật thể thông minh"}
                      </td>
                      <td className="p-3">
                        <Badge
                          variant="outline"
                          className={`text-[10px] font-mono ${
                            rec.status === "approved"
                              ? "text-emerald-500 border-emerald-500/30"
                              : rec.status === "rejected"
                              ? "text-red-500 border-red-500/30"
                              : "text-amber-500 border-amber-500/30"
                          }`}
                        >
                          {rec.status?.toUpperCase() || "PENDING"}
                        </Badge>
                      </td>
                      <td className="p-3 pr-4 text-right">
                        <Button
                          onClick={() => setSelectedRecord(rec)}
                          variant="ghost"
                          size="icon"
                          className="h-7 w-7 text-muted-foreground hover:text-foreground cursor-pointer"
                        >
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

      {/* Record Detail Modal */}
      {selectedRecord && (
        <Dialog open={!!selectedRecord} onOpenChange={(open) => !open && setSelectedRecord(null)}>
          <DialogContent className="sm:max-w-xl max-h-[85vh] overflow-y-auto border-border bg-card p-5 space-y-4">
            <DialogHeader className="pb-3 border-b border-border">
              <div className="flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-indigo-500" />
                <DialogTitle className="text-sm font-semibold">
                  Chi Tiết Bản Ghi: {selectedRecord.id}
                </DialogTitle>
              </div>
              <DialogDescription className="text-xs text-muted-foreground">
                Quét lúc {new Date(selectedRecord.created_at).toLocaleString("vi-VN")}
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-3 text-xs">
              <div className="relative aspect-video rounded-xl overflow-hidden border border-border bg-black/40">
                {selectedRecord.image_url ? (
                  <Image
                    src={resolveMediaUrl(selectedRecord.image_url)}
                    alt="Scan Image"
                    fill
                    className="object-contain"
                  />
                ) : (
                  <div className="h-full w-full flex items-center justify-center text-muted-foreground">
                    Không có ảnh
                  </div>
                )}
              </div>

              <div className="space-y-1">
                <span className="font-semibold text-foreground">Nội dung tóm tắt nhận diện:</span>
                <p className="p-2.5 rounded-lg bg-muted/40 border border-border text-muted-foreground">
                  {selectedRecord.summary || selectedRecord.raw_detected_text}
                </p>
              </div>

              <div className="space-y-1">
                <span className="font-semibold text-foreground">
                  Vật thể bóc tách ({selectedRecord.objects?.length || 0}):
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {selectedRecord.objects?.map((obj, oIdx) => (
                    <Badge key={oIdx} variant="secondary" className="gap-1 font-mono text-[11px]">
                      <span>{obj.label_vi || obj.name}</span>
                      <span className="text-primary font-bold">
                        {Math.round((obj.confidence || 0.8) * 100)}%
                      </span>
                    </Badge>
                  ))}
                </div>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}
