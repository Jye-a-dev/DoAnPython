"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import axios from "axios";
import { Camera, LogIn, ShieldAlert, User as UserIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { useAuthStore } from "@/hooks/use-auth";
import { toast } from "sonner";

export default function LoginPage() {
  const router = useRouter();
  const { login, isAuthenticated, isAdmin } = useAuthStore();

  const [email, setEmail] = React.useState("admin@system.local");
  const [roleId, setRoleId] = React.useState<number>(1);
  const [fullName, setFullName] = React.useState("System Administrator");
  const [isSubmitting, setIsSubmitting] = React.useState(false);

  React.useEffect(() => {
    if (isAuthenticated) {
      if (isAdmin) {
        router.push("/admin");
      } else {
        router.push("/");
      }
    }
  }, [isAuthenticated, isAdmin, router]);

  const handleDevLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) {
      toast.error("Vui lòng nhập địa chỉ email.");
      return;
    }

    setIsSubmitting(true);
    try {
      await login(email.trim(), roleId, fullName.trim());
      toast.success("Đăng nhập thành công!");
      if (roleId === 1) {
        router.push("/admin");
      } else {
        router.push("/");
      }
    } catch (error: unknown) {
      let msg = "Đăng nhập thất bại. Vui lòng thử lại.";
      if (axios.isAxiosError(error) && error.response?.data?.detail) {
        msg = String(error.response.data.detail);
      }
      toast.error(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleGoogleSimulateLogin = async () => {
    setIsSubmitting(true);
    try {
      await login("google.user@gmail.com", 2, "Google Customer");
      toast.success("Đăng nhập bằng tài khoản Google thành công!");
      router.push("/");
    } catch (error: unknown) {
      let msg = "Đăng nhập Google thất bại.";
      if (axios.isAxiosError(error) && error.response?.data?.detail) {
        msg = String(error.response.data.detail);
      }
      toast.error(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex-1 flex items-center justify-center p-4 py-16 bg-linear-to-b from-primary/5 via-background to-background">
      <Card className="w-full max-w-md shadow-xl border-border/80">
        <CardHeader className="text-center space-y-2">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-primary text-primary-foreground shadow-lg shadow-primary/20">
            <Camera className="h-6 w-6" />
          </div>
          <CardTitle className="text-2xl font-bold">Đăng Nhập Hệ Thống</CardTitle>
          <CardDescription className="text-xs">
            Visual AI E-Commerce & YOLO Smart Object Detection Gateway
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* 1. Google OAuth2 Quick Action */}
          <Button
            variant="outline"
            onClick={handleGoogleSimulateLogin}
            disabled={isSubmitting}
            className="w-full gap-2 border-border font-medium py-5"
          >
            <svg className="h-4 w-4" viewBox="0 0 24 24">
              <path
                fill="#4285F4"
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
              />
              <path
                fill="#34A853"
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
              />
              <path
                fill="#FBBC05"
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
              />
              <path
                fill="#EA4335"
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
              />
            </svg>
            <span>Tiếp tục với Google OAuth2</span>
          </Button>

          <div className="relative flex items-center justify-center">
            <div className="w-full border-t border-border" />
            <span className="absolute bg-card px-2 text-[11px] text-muted-foreground uppercase font-semibold">
              Hoặc đăng nhập trực tiếp (Dev Login)
            </span>
          </div>

          {/* 2. Direct Dev Login Form */}
          <form onSubmit={handleDevLogin} className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-foreground">Email tài khoản</label>
              <Input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="admin@system.local hoặc user@mail.com"
                className="text-sm"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-foreground">Họ tên hiển thị</label>
              <Input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Tên người dùng"
                className="text-sm"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-foreground">Vai trò đăng nhập (Role)</label>
              <div className="grid grid-cols-2 gap-2">
                <Button
                  type="button"
                  variant={roleId === 1 ? "default" : "outline"}
                  onClick={() => {
                    setRoleId(1);
                    setEmail("admin@system.local");
                    setFullName("Quản Trị Viên");
                  }}
                  className="gap-1.5 text-xs py-2"
                >
                  <ShieldAlert className="h-3.5 w-3.5" />
                  <span>Admin (Role 1)</span>
                </Button>

                <Button
                  type="button"
                  variant={roleId === 2 ? "default" : "outline"}
                  onClick={() => {
                    setRoleId(2);
                    setEmail("customer@shop.vn");
                    setFullName("Khách Mua Hàng");
                  }}
                  className="gap-1.5 text-xs py-2"
                >
                  <UserIcon className="h-3.5 w-3.5" />
                  <span>User (Role 2)</span>
                </Button>
              </div>
            </div>

            <Button
              type="submit"
              disabled={isSubmitting}
              className="w-full font-bold shadow-md bg-linear-to-r from-primary to-blue-600 gap-2"
            >
              <LogIn className="h-4 w-4" />
              <span>{isSubmitting ? "Đang kết nối..." : "Đăng Nhập Vào Hệ Thống"}</span>
            </Button>
          </form>
        </CardContent>

        <CardFooter className="flex justify-center border-t pt-4">
          <p className="text-[11px] text-muted-foreground text-center">
            Flask RESTX Gateway tự động phát hành Access JWT Token và Cookie Session.
          </p>
        </CardFooter>
      </Card>
    </div>
  );
}
