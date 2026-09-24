"use client";

import * as React from "react";
import Image from "next/image";
import { Badge } from "@/components/ui/badge";
import { resolveMediaUrl } from "@/lib/api-client";
import type { ReviewQueueItem } from "@/types";

interface ReviewQueueListProps {
  items: ReviewQueueItem[];
  selectedItem: ReviewQueueItem | null;
  onSelect: (item: ReviewQueueItem) => void;
}

export function ReviewQueueList({
  items,
  selectedItem,
  onSelect,
}: ReviewQueueListProps) {
  return (
    <div className="lg:col-span-4 space-y-3">
      <div className="flex items-center justify-between text-xs text-muted-foreground px-1">
        <span>Bản ghi chờ duyệt</span>
        <span className="font-mono font-semibold">{items.length} items</span>
      </div>

      <div className="space-y-2 max-h-175 overflow-y-auto pr-1">
        {items.map((item) => {
          const isSelected = selectedItem?.id === item.id;
          const isLowConf = item.confidence_score < 0.85;

          return (
            <div
              key={item.id}
              onClick={() => onSelect(item)}
              className={`p-3 rounded-xl border transition-all cursor-pointer flex gap-3 items-center ${
                isSelected
                  ? "border-primary bg-primary/5 shadow-sm"
                  : "border-border bg-card/60 hover:bg-muted/40"
              }`}
            >
              <div className="relative h-14 w-14 rounded-lg overflow-hidden border border-border bg-muted shrink-0">
                {item.image_url ? (
                  <Image
                    src={resolveMediaUrl(item.image_url)}
                    alt="Scan Photo"
                    fill
                    className="object-cover"
                  />
                ) : (
                  <div className="h-full w-full flex items-center justify-center text-[10px] text-muted-foreground">
                    No IMG
                  </div>
                )}
              </div>

              <div className="flex-1 min-w-0 space-y-1">
                <div className="flex items-center justify-between gap-1">
                  <span className="text-xs font-semibold text-foreground truncate">
                    {item.raw_detected_text || "Chưa có nhãn"}
                  </span>
                  <Badge
                    variant={isLowConf ? "destructive" : "secondary"}
                    className="text-[10px] px-1.5 py-0 font-mono shrink-0"
                  >
                    {Math.round(item.confidence_score * 100)}%
                  </Badge>
                </div>
                <p className="text-[11px] text-muted-foreground font-mono truncate">
                  ID: {item.id.slice(0, 8)}...
                </p>
                <div className="flex items-center gap-1.5 text-[10px] text-muted-foreground">
                  <span>{new Date(item.created_at).toLocaleTimeString("vi-VN")}</span>
                  <span>•</span>
                  <span className="text-amber-500 font-medium">Chờ duyệt</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

