"use client";

import * as React from "react";
import { Sparkles, ChevronDown, ShieldCheck, UserCheck } from "lucide-react";

interface DevBypassAccordionProps {
  onApplyPreset: (type: "admin" | "user") => void;
}

export function DevBypassAccordion({ onApplyPreset }: DevBypassAccordionProps) {
  const [isOpen, setIsOpen] = React.useState(false);

  return (
    <div className="border-t border-white/[0.06] pt-3">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center justify-between w-full text-xs text-slate-400 hover:text-slate-300 transition-colors py-1 group cursor-pointer"
      >
        <span className="flex items-center gap-1.5 font-medium">
          <Sparkles className="h-3.5 w-3.5 text-cyan-400" />
          ⚡ Chế độ Kiểm thử Nhà phát triển
        </span>
        <ChevronDown
          className={`h-3.5 w-3.5 transition-transform duration-200 text-slate-500 group-hover:text-slate-300 ${
            isOpen ? "rotate-180" : ""
          }`}
        />
      </button>

      {isOpen && (
        <div className="mt-2.5 p-3 rounded-xl bg-slate-950/60 border border-white/[0.06] space-y-2 animate-in fade-in slide-in-from-top-1 duration-200">
          <p className="text-[11px] text-slate-400">
            Tự động điền thông tin đăng nhập kiểm thử:
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            <button
              type="button"
              onClick={() => onApplyPreset("admin")}
              className="flex items-center gap-2 p-2 rounded-lg border border-white/5 bg-white/[0.03] hover:bg-white/[0.07] hover:border-cyan-500/30 text-left transition-all group/btn cursor-pointer"
            >
              <ShieldCheck className="h-4 w-4 text-cyan-400 shrink-0" />
              <div className="truncate">
                <div className="text-xs font-semibold text-slate-200 group-hover/btn:text-cyan-300 truncate">
                  Quản trị viên (Admin)
                </div>
                <div className="text-[10px] text-slate-400 truncate">
                  admin@system.local
                </div>
              </div>
            </button>

            <button
              type="button"
              onClick={() => onApplyPreset("user")}
              className="flex items-center gap-2 p-2 rounded-lg border border-white/5 bg-white/[0.03] hover:bg-white/[0.07] hover:border-indigo-500/30 text-left transition-all group/btn cursor-pointer"
            >
              <UserCheck className="h-4 w-4 text-indigo-400 shrink-0" />
              <div className="truncate">
                <div className="text-xs font-semibold text-slate-200 group-hover/btn:text-indigo-300 truncate">
                  Khách hàng (User)
                </div>
                <div className="text-[10px] text-slate-400 truncate">
                  customer@shop.vn
                </div>
              </div>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

