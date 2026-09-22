import * as React from "react";
import Link from "next/link";

export function LoginFooter() {
  return (
    <div className="border-t border-white/[0.06] pt-4 text-center">
      <p className="text-[11px] text-slate-500 leading-relaxed">
        Bằng việc tiếp tục, bạn đồng ý với{" "}
        <Link
          href="/terms"
          className="text-slate-400 hover:text-slate-300 underline underline-offset-2 transition-colors"
        >
          Điều khoản dịch vụ
        </Link>{" "}
        và{" "}
        <Link
          href="/privacy"
          className="text-slate-400 hover:text-slate-300 underline underline-offset-2 transition-colors"
        >
          Chính sách bảo mật
        </Link>{" "}
        của Visual AI Store.
      </p>
    </div>
  );
}

