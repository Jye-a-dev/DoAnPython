"use client";

import * as React from "react";
import Link from "next/link";
import { Mail, Lock, Eye, EyeOff, LogIn, Loader2, AlertCircle } from "lucide-react";
import { toast } from "sonner";
import { DevBypassAccordion } from "@/components/auth/dev-bypass-accordion";

interface LoginFormProps {
  onLogin: (email: string, password: string) => Promise<void>;
  onGoogleLogin: () => Promise<void>;
  isSubmitting: boolean;
  isGoogleSubmitting: boolean;
  errorMessage: string | null;
  setErrorMessage: (msg: string | null) => void;
}

export function LoginForm({
  onLogin,
  onGoogleLogin,
  isSubmitting,
  isGoogleSubmitting,
  errorMessage,
  setErrorMessage,
}: LoginFormProps) {
  const [email, setEmail] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [rememberMe, setRememberMe] = React.useState(true);
  const [showPassword, setShowPassword] = React.useState(false);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setErrorMessage(null);

    const cleanEmail = email.trim();
    if (!cleanEmail) {
      setErrorMessage("Vui lòng nhập địa chỉ email.");
      return;
    }

    if (!cleanEmail.includes("@") || !cleanEmail.includes(".")) {
      setErrorMessage("Định dạng email không hợp lệ.");
      return;
    }

    if (!password) {
      setErrorMessage("Vui lòng nhập mật khẩu tài khoản.");
      return;
    }

    await onLogin(cleanEmail, password);
  };

  const handleApplyPreset = (type: "admin" | "user") => {
    setErrorMessage(null);
    if (type === "admin") {
      setEmail("admin@system.local");
      setPassword("Admin@System2026!");
      toast.info("Đã điền thông tin tài khoản Quản trị viên (Admin)");
    } else {
      setEmail("customer@shop.vn");
      setPassword("Customer@Pass2026!");
      toast.info("Đã điền thông tin tài khoản Khách hàng (User)");
    }
  };

  return (
    <div className="space-y-4">
      {/* Inline Error Alert */}
      {errorMessage && (
        <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-start gap-2.5 animate-in fade-in duration-200">
          <AlertCircle className="h-4 w-4 shrink-0 text-rose-400 mt-0.5" />
          <span className="leading-relaxed">{errorMessage}</span>
        </div>
      )}

      {/* 1. Google OAuth2 (Primary CTA) */}
      <button
        type="button"
        onClick={onGoogleLogin}
        disabled={isGoogleSubmitting || isSubmitting}
        className="w-full h-11 rounded-xl border border-white/10 bg-white/[0.04] hover:bg-white/[0.08] hover:border-white/20 text-white font-medium text-sm flex items-center justify-center gap-3 transition-all duration-200 active:scale-[0.98] shadow-sm cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isGoogleSubmitting ? (
          <Loader2 className="h-4 w-4 animate-spin text-cyan-400" />
        ) : (
          <svg className="h-4 w-4 shrink-0" viewBox="0 0 24 24">
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
        )}
        <span>
          {isGoogleSubmitting
            ? "Đang xác thực Google..."
            : "Tiếp tục với tài khoản Google"}
        </span>
      </button>

      {/* 2. Divider */}
      <div className="relative my-4">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-white/[0.08]" />
        </div>
        <div className="relative flex justify-center text-xs">
          <span className="bg-[#0f172a] px-3 text-[11px] font-medium tracking-wide text-slate-400 select-none">
            Hoặc tiếp tục với tài khoản hệ thống
          </span>
        </div>
      </div>

      {/* 3. Standard Form (Email & Password) */}
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Input Email */}
        <div className="space-y-1.5">
          <label
            htmlFor="login-email"
            className="block text-xs font-medium text-slate-300"
          >
            Địa chỉ Email
          </label>
          <div className="relative">
            <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 pointer-events-none" />
            <input
              id="login-email"
              type="email"
              required
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="name@company.com"
              className="w-full h-11 pl-10 pr-3 rounded-xl border border-white/10 bg-slate-950/50 text-sm text-white placeholder:text-slate-500 focus:outline-none focus:border-cyan-500/80 focus:ring-1 focus:ring-cyan-500/50 transition-colors"
            />
          </div>
        </div>

        {/* Input Password */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between">
            <label
              htmlFor="login-password"
              className="block text-xs font-medium text-slate-300"
            >
              Mật khẩu
            </label>
            <button
              type="button"
              onClick={() => toast.info("Vui lòng liên hệ quản trị viên để khôi phục mật khẩu.")}
              className="text-xs text-cyan-400 hover:text-cyan-300 hover:underline transition-colors"
            >
              Quên mật khẩu?
            </button>
          </div>
          <div className="relative">
            <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 pointer-events-none" />
            <input
              id="login-password"
              type={showPassword ? "text" : "password"}
              required
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full h-11 pl-10 pr-10 rounded-xl border border-white/10 bg-slate-950/50 text-sm text-white placeholder:text-slate-500 focus:outline-none focus:border-cyan-500/80 focus:ring-1 focus:ring-cyan-500/50 transition-colors"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              aria-label={showPassword ? "Ẩn mật khẩu" : "Hiện mật khẩu"}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200 p-1 focus:outline-none transition-colors cursor-pointer"
            >
              {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
        </div>

        {/* Checkbox: Remember Session */}
        <div className="flex items-center gap-2 pt-0.5">
          <input
            id="remember-session"
            type="checkbox"
            checked={rememberMe}
            onChange={(e) => setRememberMe(e.target.checked)}
            className="h-4 w-4 rounded border-white/20 bg-slate-950/60 text-cyan-500 focus:ring-cyan-500/30 accent-cyan-500 cursor-pointer"
          />
          <label
            htmlFor="remember-session"
            className="text-xs text-slate-300 select-none cursor-pointer"
          >
            Ghi nhớ phiên đăng nhập
          </label>
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={isSubmitting || isGoogleSubmitting}
          className="w-full h-11 rounded-xl bg-gradient-to-r from-cyan-400 via-teal-300 to-indigo-400 hover:from-cyan-300 hover:to-indigo-300 text-slate-950 font-bold text-sm shadow-lg shadow-cyan-500/20 active:scale-[0.98] transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isSubmitting ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin text-slate-950" />
              <span>Đang kết nối...</span>
            </>
          ) : (
            <>
              <LogIn className="h-4 w-4 text-slate-950" />
              <span>Đăng Nhập Vào Hệ Thống</span>
            </>
          )}
        </button>

        {/* Link to Register */}
        <div className="text-center pt-1.5">
          <p className="text-xs text-slate-400">
            Chưa có tài khoản?{" "}
            <Link
              href="/register"
              className="text-cyan-400 hover:text-cyan-300 font-semibold hover:underline transition-colors"
            >
              Đăng ký ngay
            </Link>
          </p>
        </div>
      </form>

      {/* 4. Dev Mode Bypass Accordion */}
      <DevBypassAccordion onApplyPreset={handleApplyPreset} />
    </div>
  );
}

