"use client";

import * as React from "react";
import { Users, RefreshCw } from "lucide-react";
import { useAuthStore } from "@/stores/auth-store";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";

export default function AdminUsersPage() {
  const user = useAuthStore((s) => s.user);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-6">
        <div>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="gap-1 px-2.5 py-0.5 text-violet-500 border-violet-500/30">
              <Users className="h-3.5 w-3.5" />
              RBAC & USER DIRECTORY
            </Badge>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">
              Quản Lý Người Dùng & Phân Quyền
            </h1>
          </div>
          <p className="text-xs sm:text-sm text-muted-foreground mt-1">
            Danh bạ tài khoản, phân định vai trò Admin (role_id: 1) và User (role_id: 2).
          </p>
        </div>

        <Button variant="outline" size="sm" className="gap-1.5 cursor-pointer text-xs">
          <RefreshCw className="h-3.5 w-3.5" />
          <span>Làm mới</span>
        </Button>
      </div>

      {/* Current Active Admin Table Card */}
      <Card className="border-border bg-card/60 backdrop-blur-sm">
        <CardContent className="p-0">
          <table className="w-full text-xs text-left border-collapse">
            <thead>
              <tr className="border-b border-border bg-muted/30 text-muted-foreground font-semibold">
                <th className="p-3 pl-4">Họ Và Tên / Email</th>
                <th className="p-3">User ID (UUID v4)</th>
                <th className="p-3">Role ID</th>
                <th className="p-3">Vai Trò Hệ Thống</th>
                <th className="p-3 pr-4 text-right">Trạng Thái</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/60">
              {user && (
                <tr className="hover:bg-muted/30 transition-colors">
                  <td className="p-3 pl-4 font-medium text-foreground">
                    <div className="flex flex-col">
                      <span>{user.full_name || "Quản trị viên chính"}</span>
                      <span className="text-[10px] text-muted-foreground">{user.email}</span>
                    </div>
                  </td>
                  <td className="p-3 font-mono text-muted-foreground">{user.id}</td>
                  <td className="p-3 font-mono font-bold text-red-500">{user.role_id}</td>
                  <td className="p-3">
                    <Badge variant="destructive" className="text-[10px] px-2 py-0.5">
                      SUPER ADMIN
                    </Badge>
                  </td>
                  <td className="p-3 pr-4 text-right">
                    <Badge variant="outline" className="text-[10px] text-emerald-600 border-emerald-500/30">
                      Đang hoạt động
                    </Badge>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}

