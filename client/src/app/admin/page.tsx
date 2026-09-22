"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { RefreshCw } from "lucide-react";
import { useAuthStore } from "@/stores/auth-store";
import { adminService } from "@/services";
import { ProductStats, OrderStats, DetectionRecord } from "@/types";
import { AdminHeader } from "@/components/admin/admin-header";
import { AdminMetricsCards } from "@/components/admin/admin-metrics-cards";
import { AdminAuditLog } from "@/components/admin/admin-audit-log";

export default function AdminDashboardPage() {
  const router = useRouter();
  const { isAuthenticated, isAdmin, isLoading: authLoading } = useAuthStore();

  const [productStats, setProductStats] = React.useState<ProductStats | null>(null);
  const [orderStats, setOrderStats] = React.useState<OrderStats | null>(null);
  const [historyRecords, setHistoryRecords] = React.useState<DetectionRecord[]>([]);
  const [isLoading, setIsLoading] = React.useState(true);

  React.useEffect(() => {
    if (!authLoading && (!isAuthenticated || !isAdmin)) {
      router.push("/login");
    }
  }, [authLoading, isAuthenticated, isAdmin, router]);

  const loadDashboardData = React.useCallback(async () => {
    setIsLoading(true);
    try {
      const [pStatsRes, oStatsRes, histRes] = await Promise.all([
        adminService.getProductStats().catch(() => null),
        adminService.getOrderStats().catch(() => null),
        adminService.getDetectionHistory({ limit: 6, skip: 0 }).catch(() => null),
      ]);

      if (pStatsRes) setProductStats(pStatsRes.data);
      if (oStatsRes) setOrderStats(oStatsRes.data);
      if (histRes) setHistoryRecords(histRes.data?.records || []);
    } finally {
      setIsLoading(false);
    }
  }, []);

  React.useEffect(() => {
    if (isAuthenticated && isAdmin) {
      loadDashboardData();
    }
  }, [isAuthenticated, isAdmin, loadDashboardData]);

  if (authLoading || (!isAdmin && isAuthenticated)) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <RefreshCw className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 sm:px-8 py-10 space-y-8">
      {/* 1. Header Toolbar */}
      <AdminHeader isLoading={isLoading} onRefresh={loadDashboardData} />

      {/* 2. KPI Metrics Cards */}
      <AdminMetricsCards
        isLoading={isLoading}
        productStats={productStats}
        orderStats={orderStats}
      />

      {/* 3. Detection Audit Log Section */}
      <AdminAuditLog isLoading={isLoading} historyRecords={historyRecords} />
    </div>
  );
}