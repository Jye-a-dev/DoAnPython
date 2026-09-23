"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  User as UserIcon,
  Mail,
  Shield,
  Calendar,
  Package,
  LogOut,
  Camera,
} from "lucide-react";
import { useAuthStore } from "@/stores/auth-store";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";

export default function UserProfilePage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading, logout } = useAuthStore();

  React.useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/login?redirect=/profile");
    }
  }, [isLoading, isAuthenticated, router]);

  if (isLoading || !user) {
    return (
      <div className="container mx-auto px-4 py-16 flex justify-center items-center flex-1">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      </div>
    );
  }

  const handleLogout = async () => {
    await logout();
    router.push("/login");
  };

  return (
    <div className="container mx-auto px-4 sm:px-8 py-10 space-y-8 max-w-4xl flex-1">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
            Tài Khoản Của Tôi
          </h1>
          <p className="text-xs sm:text-sm text-muted-foreground mt-1">
            Quản lý thông tin định danh và cài đặt tài khoản người dùng Visual AI Store.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" asChild className="text-xs gap-1.5">
            <Link href="/orders">
              <Package className="h-3.5 w-3.5 text-indigo-500" />
              <span>Đơn hàng của tôi</span>
            </Link>
          </Button>

          <Button
            variant="ghost"
            size="sm"
            onClick={handleLogout}
            className="text-xs gap-1.5 text-destructive hover:bg-destructive/10 cursor-pointer"
          >
            <LogOut className="h-3.5 w-3.5" />
            <span>Đăng xuất</span>
          </Button>
        </div>
      </div>

      {/* Profile Overview Card */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="md:col-span-1 border-border bg-card/60 backdrop-blur-sm">
          <CardContent className="pt-6 flex flex-col items-center text-center space-y-4">
            <Avatar className="h-20 w-20 ring-4 ring-primary/10">
              <AvatarImage src={user.avatar_url || ""} />
              <AvatarFallback className="bg-primary/10 text-primary text-xl font-bold">
                {(user.full_name || user.email).charAt(0).toUpperCase()}
              </AvatarFallback>
            </Avatar>

            <div className="space-y-1">
              <h3 className="font-bold text-base text-foreground">
                {user.full_name || "Người dùng"}
              </h3>
              <p className="text-xs text-muted-foreground break-all">{user.email}</p>
            </div>

            <Badge
              variant={user.role_id === 1 ? "destructive" : "secondary"}
              className="text-xs px-2.5 py-0.5"
            >
              {user.role_id === 1 ? "🔴 Quản trị viên (Admin)" : "Khách hàng thân thiết"}
            </Badge>

            {user.role_id === 1 && (
              <Button size="sm" variant="default" asChild className="w-full text-xs mt-2">
                <Link href="/admin">Truy cập Trang Quản Trị</Link>
              </Button>
            )}
          </CardContent>
        </Card>

        {/* Detailed Info Card */}
        <Card className="md:col-span-2 border-border bg-card/60 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="text-base font-semibold">Thông tin chi tiết</CardTitle>
            <CardDescription className="text-xs">
              Các thông số kỹ thuật và định danh gắn liền với tài khoản
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 text-xs">
            <div className="flex items-center justify-between py-2 border-b border-border/60">
              <span className="flex items-center gap-2 text-muted-foreground">
                <UserIcon className="h-4 w-4 text-blue-500" />
                Định danh (UUID v4)
              </span>
              <span className="font-mono text-[11px] text-foreground bg-muted/60 px-2 py-0.5 rounded">
                {user.id}
              </span>
            </div>

            <div className="flex items-center justify-between py-2 border-b border-border/60">
              <span className="flex items-center gap-2 text-muted-foreground">
                <Mail className="h-4 w-4 text-indigo-500" />
                Địa chỉ Email
              </span>
              <span className="font-medium text-foreground">{user.email}</span>
            </div>

            <div className="flex items-center justify-between py-2 border-b border-border/60">
              <span className="flex items-center gap-2 text-muted-foreground">
                <Shield className="h-4 w-4 text-cyan-500" />
                Mã quyền hạn (Role ID)
              </span>
              <span className="font-mono text-foreground font-semibold">
                {user.role_id} ({user.role_id === 1 ? "Admin" : "User"})
              </span>
            </div>

            <div className="flex items-center justify-between py-2 border-b border-border/60">
              <span className="flex items-center gap-2 text-muted-foreground">
                <Calendar className="h-4 w-4 text-violet-500" />
                Ngày tham gia
              </span>
              <span className="text-foreground">
                {user.created_at ? new Date(user.created_at).toLocaleDateString("vi-VN") : "Hôm nay"}
              </span>
            </div>

            <div className="flex items-center justify-between py-2">
              <span className="flex items-center gap-2 text-muted-foreground">
                <Camera className="h-4 w-4 text-emerald-500" />
                Tính năng Quét AI
              </span>
              <Badge variant="outline" className="text-[11px] text-emerald-600 border-emerald-500/30">
                Đã kích hoạt YOLO11
              </Badge>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

