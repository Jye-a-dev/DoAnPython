import * as React from "react";

export function AuthBackground() {
  return (
    <>
      {/* Visual Depth: Ambient Glow & Radial Spotlights */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[540px] h-[540px] bg-gradient-to-tr from-cyan-500/15 via-indigo-600/15 to-transparent blur-[140px] rounded-full pointer-events-none -z-0" />
      <div className="absolute bottom-10 right-1/4 w-[380px] h-[380px] bg-indigo-500/10 blur-[120px] rounded-full pointer-events-none -z-0" />
      <div className="absolute top-12 left-1/4 w-[320px] h-[320px] bg-cyan-500/10 blur-[100px] rounded-full pointer-events-none -z-0" />

      {/* Cyberpunk Tech Grid Pattern */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#ffffff05_1px,transparent_1px),linear-gradient(to_bottom,#ffffff05_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_50%,#000_70%,transparent_100%)] pointer-events-none -z-0" />
    </>
  );
}

