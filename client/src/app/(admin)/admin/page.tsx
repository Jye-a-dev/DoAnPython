"use client";

import * as React from "react";
import { useAuthStore } from "@/stores/auth-store";
import { adminService } from "@/services";
import { ProductStats, OrderStats, DetectionRecord } from "@/types";
import { AdminHeader } from "@/components/admin/admin-header";
import { AdminMetricsCards } from "@/components/admin/admin-metrics-cards";
import { AdminAuditLog } from "@/components/admin/admin-audit-log";

export default function AdminDashboardPage() {
  const { isAuthenticated, isAdmin } = useAuthStore();

  const [productStats, setProductStats] = React.useState<ProductStats | null>(null);
  const [orderStats, setOrderStats] = React.useState<OrderStats | null>(null);
  const [historyRecords, setHistoryRecords] = React.useState<DetectionRecord[]>([]);
  const [isLoading, setIsLoading] = React.useState(true);

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

  return (
    <div className="space-y-8">
      {/* 1. Header Toolbar (Banner + Refresh Button) */}
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

