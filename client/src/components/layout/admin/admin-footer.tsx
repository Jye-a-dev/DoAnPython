import * as React from "react";
import { Cpu, Database, Activity, GitBranch } from "lucide-react";

export function AdminFooter() {
  return (
    <footer className="w-full border-t border-border bg-card/60 px-6 py-3 text-xs text-muted-foreground backdrop-blur-sm">
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
        {/* Left: System Status Indicators */}
        <div className="flex flex-wrap items-center gap-4 text-[11px] font-mono">
          <div className="flex items-center gap-1.5 text-emerald-600 dark:text-emerald-400">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
            </span>
            <span>Gateway Operational</span>
          </div>

          <div className="flex items-center gap-1">
            <Activity className="h-3 w-3 text-indigo-500" />
            <span>Latency: ~38ms</span>
          </div>

          <div className="flex items-center gap-1">
            <Database className="h-3 w-3 text-cyan-500" />
            <span>SQLite WAL: Synced</span>
          </div>

          <div className="flex items-center gap-1">
            <Cpu className="h-3 w-3 text-blue-500" />
            <span>YOLO11x Core</span>
          </div>
        </div>

        {/* Right: Version and Protocol */}
        <div className="flex items-center gap-3 text-[11px]">
          <span className="flex items-center gap-1 font-mono text-muted-foreground">
            <GitBranch className="h-3 w-3" />
            v2.0-enterprise
          </span>
          <span className="text-muted-foreground/60">•</span>
          <span>Camera-to-Shop Control Plane</span>
        </div>
      </div>
    </footer>
  );
}

