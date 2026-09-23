import * as React from "react";

interface AuthLayoutProps {
  children: React.ReactNode;
}

export default function AuthLayout({ children }: AuthLayoutProps) {
  return (
    <div className="relative min-h-screen flex flex-col justify-center items-center bg-background text-foreground overflow-hidden">
      {/* Subtle Ambient Radial Glow */}
      <div className="pointer-events-none absolute -top-40 -left-40 h-125 w-125 rounded-full bg-blue-500/10 blur-[120px]" />
      <div className="pointer-events-none absolute -bottom-40 -right-40 h-125 w-125 rounded-full bg-indigo-500/10 blur-[120px]" />
      
      <main className="relative z-10 w-full flex flex-col items-center justify-center p-4">
        {children}
      </main>
    </div>
  );
}

