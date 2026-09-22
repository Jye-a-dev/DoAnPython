import * as React from "react";
import { ShieldAlert, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

interface AdminHeaderProps {
  isLoading: boolean;
  onRefresh: () => void;
}

export function AdminHeader({ isLoading, onRefresh }: AdminHeaderProps) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b pb-6">
      <div>
        <div className="flex items-center gap-2">
          <Badge variant="destructive" className="gap-1 px-2.5 py-0.5">
            <ShieldAlert className="h-3.5 w-3.5" />
            QUẢN TRỊ VIÊN
          </Badge>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">
            Hệ Thống Quản Trị Trung Tâm
          </h1>
        </div>
        <p className="text-xs sm:text-sm text-muted-foreground mt-1">
          Theo dõi chỉ số kho hàng, doanh thu đơn hàng và giám sát nhật ký nhận diện AI.
        </p>
      </div>

      <Button
        onClick={onRefresh}
        variant="outline"
        size="sm"
        className="gap-1.5 self-start sm:self-auto cursor-pointer"
      >
        <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
        <span>Làm mới dữ liệu</span>
      </Button>
    </div>
  );
}

