"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import axios from "axios";
import { toast } from "sonner";
import { useAuthStore } from "@/stores/auth-store";
import { AuthBackground } from "@/components/auth/auth-background";
import { LoginBrandHeader } from "@/components/auth/login-brand-header";
import { LoginForm } from "@/components/auth/login-form";
import { LoginFooter } from "@/components/auth/login-footer";

export default function LoginPage() {
  const router = useRouter();
  const { login, loginWithGoogle, isAuthenticated, isAdmin } = useAuthStore();

  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const [isGoogleSubmitting, setIsGoogleSubmitting] = React.useState(false);
  const [errorMessage, setErrorMessage] = React.useState<string | null>(null);

  // Auto-redirect if already authenticated
  React.useEffect(() => {
    if (isAuthenticated) {
      if (isAdmin) {
        router.push("/admin");
      } else {
        router.push("/");
      }
    }
  }, [isAuthenticated, isAdmin, router]);

  const handleLogin = async (cleanEmail: string, password: string) => {
    setIsSubmitting(true);
    setErrorMessage(null);
    try {
      const user = await login(cleanEmail, password);
      toast.success(`Đăng nhập thành công! Chào mừng ${user.full_name || user.email}`);

      // Role-based routing: 1 -> Admin dashboard, 2 -> Client storefront
      if (user.role_id === 1) {
        router.push("/admin");
      } else {
        router.push("/");
      }
    } catch (error: unknown) {
      let msg = "Tài khoản hoặc mật khẩu không chính xác.";
      if (axios.isAxiosError(error) && error.response?.data?.detail) {
        msg = String(error.response.data.detail);
      } else if (axios.isAxiosError(error) && error.response?.data?.message) {
        msg = String(error.response.data.message);
      }
      setErrorMessage(msg);
      toast.error(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleGoogleLogin = async () => {
    setIsGoogleSubmitting(true);
    setErrorMessage(null);
    try {
      const googleMockIdToken =
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6Imdvb2dsZS51c2VyQGdtYWlsLmNvbSIsIm5hbWUiOiJHb29nbGUgQ3VzdG9tZXIiLCJzdWIiOiJnb29nbGUtdXNlci0xIn0.URGUIH31mBw0ITw4SEtTuwjxbpMAKdXKXxortwPe8NQ";

      const user = await loginWithGoogle(googleMockIdToken);
      toast.success(`Đăng nhập Google thành công! Chào mừng ${user.full_name || user.email}`);

      if (user.role_id === 1) {
        router.push("/admin");
      } else {
        router.push("/");
      }
    } catch (error: unknown) {
      let msg = "Xác thực Google thất bại. Vui lòng kiểm tra lại kết nối mạng.";
      if (axios.isAxiosError(error) && error.response?.data?.detail) {
        msg = String(error.response.data.detail);
      }
      setErrorMessage(msg);
      toast.error(msg);
    } finally {
      setIsGoogleSubmitting(false);
    }
  };

  return (
    <div className="relative min-h-[calc(100vh-4rem)] w-full flex items-center justify-center p-4 py-12 overflow-hidden bg-[#090A0F]">
      {/* 1. Ambient Lighting & Spotlights */}
      <AuthBackground />

      {/* 2. Glassmorphic Card Container */}
      <div
        className="relative z-10 w-full max-w-md rounded-2xl shadow-2xl p-6 sm:p-8 space-y-6"
        style={{
          background: "rgba(15, 23, 42, 0.85)",
          border: "1px solid rgba(255, 255, 255, 0.08)",
          backdropFilter: "blur(24px)",
          WebkitBackdropFilter: "blur(24px)",
        }}
      >
        {/* Brand Header */}
        <LoginBrandHeader />

        {/* Form & Dual-Auth Flow */}
        <LoginForm
          onLogin={handleLogin}
          onGoogleLogin={handleGoogleLogin}
          isSubmitting={isSubmitting}
          isGoogleSubmitting={isGoogleSubmitting}
          errorMessage={errorMessage}
          setErrorMessage={setErrorMessage}
        />

        {/* Enterprise Privacy & Terms Footer */}
        <LoginFooter />
      </div>
    </div>
  );
}

