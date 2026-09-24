"use client";

import * as React from "react";
import { Loader2, Pause, Play, RefreshCw, Volume2 } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ReviewTTSPlayerProps {
  previewAudioUrl: string | null;
  isSynthesizing: boolean;
  isPlaying: boolean;
  canSynthesize: boolean;
  onSynthesize: () => void;
  onTogglePlay: () => void;
  onEnded: () => void;
  onError: () => void;
  audioRef: React.RefObject<HTMLAudioElement | null>;
}

export function ReviewTTSPlayer({
  previewAudioUrl,
  isSynthesizing,
  isPlaying,
  canSynthesize,
  onSynthesize,
  onTogglePlay,
  onEnded,
  onError,
  audioRef,
}: ReviewTTSPlayerProps) {
  return (
    <div className="p-3.5 rounded-xl border border-border bg-muted/20 space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-500/10 text-indigo-500">
            <Volume2 className="h-4 w-4" />
          </div>
          <div>
            <span className="text-xs font-semibold text-foreground">
              One-Click Neural TTS Preview Player
            </span>
            <p className="text-[10px] text-muted-foreground font-mono">
              Voice: vi-VN-HoaiMyNeural (Edge-TTS Fallback)
            </p>
          </div>
        </div>

        <Button
          onClick={onSynthesize}
          disabled={isSynthesizing || !canSynthesize}
          size="sm"
          variant="outline"
          className="h-7 text-xs gap-1.5 cursor-pointer text-indigo-500 border-indigo-500/30 hover:bg-indigo-500/10"
        >
          {isSynthesizing ? (
            <Loader2 className="h-3 w-3 animate-spin" />
          ) : (
            <RefreshCw className="h-3 w-3" />
          )}
          <span>Nghe thử phát âm</span>
        </Button>
      </div>

      {/* Audio Controller Bar */}
      <div className="flex items-center gap-3 p-2 rounded-lg bg-background border border-border/80">
        <Button
          onClick={onTogglePlay}
          disabled={!previewAudioUrl}
          size="icon"
          variant="ghost"
          className="h-8 w-8 text-primary cursor-pointer shrink-0"
        >
          {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
        </Button>

        <div className="flex-1 min-w-0">
          <div className="h-2 rounded-full bg-muted overflow-hidden relative">
            <div
              className={`h-full bg-indigo-500 rounded-full ${
                isPlaying
                  ? "animate-pulse w-full"
                  : previewAudioUrl
                  ? "w-full"
                  : "w-0"
              }`}
            />
          </div>
        </div>

        <span className="text-[11px] font-mono text-muted-foreground shrink-0">
          {previewAudioUrl ? "Sẵn sàng" : "Chưa sinh audio"}
        </span>

        {/* Hidden Native Audio Element */}
        <audio
          ref={audioRef}
          onEnded={onEnded}
          onError={onError}
          className="hidden"
        />
      </div>
    </div>
  );
}

