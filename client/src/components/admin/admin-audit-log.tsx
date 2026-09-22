import * as React from "react";
import Image from "next/image";
import { Camera, Eye } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { DetectionRecord } from "@/types";
import { resolveMediaUrl } from "@/lib/api-client";

interface AdminAuditLogProps {
  isLoading: boolean;
  historyRecords: DetectionRecord[];
}

export function AdminAuditLog({ isLoading, historyRecords }: AdminAuditLogProps) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Camera className="h-5 w-5 text-primary" />
          <h2 className="text-lg font-bold text-foreground">
            Nhật Ký Quét Ảnh Camera & YOLO Mới Nhất
          </h2>
        </div>
        <span className="text-xs text-muted-foreground">Bản ghi gần nhất</span>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <Skeleton className="h-40 rounded-xl" />
          <Skeleton className="h-40 rounded-xl" />
          <Skeleton className="h-40 rounded-xl" />
        </div>
      ) : historyRecords.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {historyRecords.map((record) => (
            <div
              key={record.id}
              className="flex flex-col rounded-xl border bg-card p-4 space-y-3 shadow-xs hover:border-primary/50 transition-colors"
            >
              <div className="flex items-start gap-3">
                <div className="relative h-16 w-16 shrink-0 overflow-hidden rounded-lg border bg-black/5">
                  <Image
                    src={resolveMediaUrl(record.image_url)}
                    alt="Detection"
                    fill
                    sizes="64px"
                    className="object-cover"
                  />
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-mono text-muted-foreground truncate">
                      ID: {record.id.slice(0, 8)}...
                    </span>
                    <Badge variant="outline" className="text-[10px]">
                      {record.status}
                    </Badge>
                  </div>

                  <p className="text-xs text-foreground font-medium line-clamp-2 mt-1">
                    {record.summary || record.raw_detected_text || "Không có tóm tắt"}
                  </p>
                </div>
              </div>

              {/* Detected Badges */}
              <div className="flex flex-wrap gap-1">
                {Array.isArray(record.objects) &&
                  record.objects.slice(0, 3).map((obj, i) => (
                    <Badge key={i} variant="secondary" className="text-[10px] py-0 px-1.5">
                      {obj.label_vi || obj.name}
                    </Badge>
                  ))}
                {Array.isArray(record.objects) && record.objects.length > 3 && (
                  <Badge variant="outline" className="text-[10px] py-0 px-1.5">
                    +{record.objects.length - 3}
                  </Badge>
                )}
              </div>

              <div className="pt-2 border-t flex items-center justify-between text-[11px] text-muted-foreground">
                <span>
                  {record.created_at
                    ? new Date(record.created_at).toLocaleString("vi-VN")
                    : "Gần đây"}
                </span>
                <a
                  href={resolveMediaUrl(record.image_url)}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center gap-1 text-primary hover:underline"
                >
                  <Eye className="h-3 w-3" />
                  Xem ảnh
                </a>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="rounded-xl border border-dashed p-8 text-center text-muted-foreground text-sm">
          Chưa có lịch sử nhận diện nào được ghi nhận trên hệ thống.
        </div>
      )}
    </div>
  );
}

