import * as React from "react";
import { Camera } from "lucide-react";

export function LoginBrandHeader() {
  return (
    <div className="text-center space-y-3">
      <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-tr from-cyan-500 to-indigo-600 shadow-lg shadow-cyan-500/25 ring-1 ring-white/20 transition-transform hover:scale-105 duration-300">
        <Camera className="h-7 w-7 text-white" />
      </div>
      <div className="space-y-1.5">
        <h1 className="text-2xl font-bold tracking-tight text-white">
          Chào mừng trở lại
        </h1>
        <p className="text-xs text-slate-400 font-normal leading-relaxed max-w-xs mx-auto">
          Đăng nhập để trải nghiệm mua sắm thông minh cùng Trợ lý Thị giác AI
        </p>
      </div>
    </div>
  );
}

