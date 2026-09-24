"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import {
  Sparkles,
  Search,
  ArrowRight,
  Database,
  Terminal,
  AlertCircle,
  Loader2,
  CornerDownLeft,
} from "lucide-react";
import { useAdminStore } from "@/stores/admin-store";
import { adminService } from "@/services/admin.service";
import type { CopilotQueryResult } from "@/types";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

const PRESET_QUERIES = [
  "Lọc các bản ghi quét bị lỗi trong hôm nay",
  "Thống kê sản phẩm laptop bán chạy và tồn kho dưới 5",
  "Hiển thị các bản ghi quét camera chưa được duyệt của tuần này",
];

export function AdminCopilotModal() {
  const router = useRouter();
  const { isCopilotOpen, closeCopilot } = useAdminStore();
  const [query, setQuery] = React.useState("");
  const [isLoading, setIsLoading] = React.useState(false);
  const [result, setResult] = React.useState<CopilotQueryResult | null>(null);
  const [error, setError] = React.useState<string | null>(null);

  const handleExecute = async (inputQuery: string) => {
    const q = inputQuery.trim();
    if (!q) return;
    setIsLoading(true);
    setError(null);
    try {
      const res = await adminService.queryCopilot(q);
      setResult(res.data);
    } catch (err: unknown) {
      const msg =
        err && typeof err === "object" && "response" in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : "Không thể thực thi truy vấn an toàn.";
      setError(String(msg || "Lỗi truy vấn Copilot."));
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleExecute(query);
    }
  };

  const handleNavigate = (route: string) => {
    closeCopilot();
    router.push(route);
  };

  return (
    <Dialog open={isCopilotOpen} onOpenChange={(open) => !open && closeCopilot()}>
      <DialogContent className="sm:max-w-2xl max-h-[85vh] flex flex-col p-0 overflow-hidden border-border bg-card/95 backdrop-blur-md">
        <DialogHeader className="p-4 pb-2 border-b border-border/80">
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-500/10 text-indigo-500">
              <Sparkles className="h-4 w-4" />
            </div>
            <DialogTitle className="text-base font-semibold">
              Admin Copilot & Text-to-SQL
            </DialogTitle>
            <Badge variant="outline" className="text-[10px] border-emerald-500/30 text-emerald-500 font-mono">
              READ-ONLY SAFE
            </Badge>
          </div>
          <DialogDescription className="text-xs text-muted-foreground">
            Truy vấn cơ sở dữ liệu SQLite qua câu lệnh Tiếng Việt tự nhiên hoặc SQL SELECT an toàn.
          </DialogDescription>
        </DialogHeader>

        {/* Input Bar */}
        <div className="p-4 pb-3 space-y-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Nhập câu lệnh tiếng Việt hoặc SELECT query..."
              className="h-10 w-full rounded-lg border border-border bg-muted/30 pl-9 pr-10 text-xs placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary font-medium"
              autoFocus
            />
            <Button
              onClick={() => handleExecute(query)}
              disabled={isLoading || !query.trim()}
              size="icon"
              variant="ghost"
              className="absolute right-1 top-1/2 -translate-y-1/2 h-8 w-8 text-muted-foreground hover:text-foreground"
            >
              {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <CornerDownLeft className="h-4 w-4" />}
            </Button>
          </div>

          {/* Preset Prompts */}
          <div className="flex flex-wrap gap-1.5">
            {PRESET_QUERIES.map((preset, idx) => (
              <button
                key={idx}
                onClick={() => {
                  setQuery(preset);
                  handleExecute(preset);
                }}
                className="text-[11px] px-2.5 py-1 rounded-full bg-muted/60 hover:bg-muted text-muted-foreground hover:text-foreground transition-colors cursor-pointer text-left truncate max-w-full"
              >
                {preset}
              </button>
            ))}
          </div>
        </div>

        {/* Result & Feedback Area */}
        <div className="flex-1 overflow-y-auto px-4 pb-4 space-y-3 min-h-40">
          {error && (
            <div className="flex items-start gap-2 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-500 text-xs">
              <AlertCircle className="h-4 w-4 mt-0.5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {isLoading && (
            <div className="py-12 flex flex-col items-center justify-center text-muted-foreground text-xs space-y-2">
              <Loader2 className="h-6 w-6 animate-spin text-primary" />
              <span>Copilot đang phân tích câu hỏi và sinh SQL an toàn...</span>
            </div>
          )}

          {result && !isLoading && (
            <div className="space-y-3">
              {/* Explanation & Intent */}
              <div className="flex items-start justify-between gap-3 p-3 rounded-lg bg-muted/40 border border-border/60">
                <div className="space-y-1">
                  <div className="flex items-center gap-1.5 text-xs font-semibold text-foreground">
                    <Database className="h-3.5 w-3.5 text-indigo-500" />
                    <span>Giải Thích Truy Vấn</span>
                  </div>
                  <p className="text-xs text-muted-foreground">{result.explanation}</p>
                </div>
                {result.route_suggestion && (
                  <Button
                    onClick={() => handleNavigate(result.route_suggestion!)}
                    size="sm"
                    className="gap-1.5 text-xs bg-indigo-600 hover:bg-indigo-500 text-white shrink-0 cursor-pointer"
                  >
                    <span>Mở trang chi tiết</span>
                    <ArrowRight className="h-3.5 w-3.5" />
                  </Button>
                )}
              </div>

              {/* Safe SQL Fenced Code */}
              {result.safe_sql && (
                <div className="space-y-1">
                  <div className="flex items-center gap-1 text-[11px] font-mono text-muted-foreground">
                    <Terminal className="h-3 w-3" />
                    <span>SAFE READ-ONLY SQL (LIMIT 50):</span>
                  </div>
                  <pre className="p-2.5 rounded-lg bg-background border border-border/80 font-mono text-[11px] text-cyan-500 overflow-x-auto">
                    {result.safe_sql}
                  </pre>
                </div>
              )}

              {/* Query Results Preview */}
              <div className="space-y-1">
                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <span>Kết quả truy vấn ({result.count} dòng):</span>
                </div>
                {result.results.length === 0 ? (
                  <div className="p-6 text-center text-xs text-muted-foreground border border-dashed rounded-lg">
                    Không có bản ghi nào khớp với điều kiện tìm kiếm.
                  </div>
                ) : (
                  <div className="border border-border rounded-lg overflow-x-auto max-h-56">
                    <table className="w-full text-[11px] text-left border-collapse">
                      <thead>
                        <tr className="border-b border-border bg-muted/50 text-muted-foreground font-semibold">
                          {Object.keys(result.results[0]).map((col) => (
                            <th key={col} className="p-2 pl-3 whitespace-nowrap">
                              {col}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border/60">
                        {result.results.map((row, rIdx) => (
                          <tr key={rIdx} className="hover:bg-muted/30 font-mono">
                            {Object.values(row).map((val, cIdx) => (
                              <td key={cIdx} className="p-2 pl-3 whitespace-nowrap truncate max-w-40 text-foreground">
                                {typeof val === "object" ? JSON.stringify(val) : String(val ?? "N/A")}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

