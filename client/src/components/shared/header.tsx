"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Menu, Layers, ArrowRight } from "lucide-react";

function GithubIcon(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4" />
      <path d="M9 18c-4.51 2-5-2-7-2" />
    </svg>
  );
}
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/shared/theme-toggle";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { label: "Trang chủ", href: "/" },
  { label: "Dashboard", href: "/dashboard" },
  { label: "Đăng nhập", href: "/login" },
];

export function Header() {
  const pathname = usePathname();
  const [isOpen, setIsOpen] = React.useState(false);

  return (
    <header className="sticky top-0 z-40 w-full border-b bg-background/80 backdrop-blur-md">
      <div className="container mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-8">
        <div className="flex items-center gap-6">
          <Link href="/" className="flex items-center gap-2 font-bold text-lg tracking-tight">
            <div className="flex size-9 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-xs">
              <Layers className="size-5" />
            </div>
            <span className="hidden sm:inline-block">Next.js Template</span>
          </Link>

          <nav className="hidden md:flex items-center gap-6 text-sm font-medium">
            {NAV_ITEMS.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "transition-colors hover:text-foreground",
                  pathname === item.href
                    ? "text-foreground font-semibold"
                    : "text-muted-foreground"
                )}
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </div>

        <div className="flex items-center gap-2">
          <ThemeToggle />

          <Button variant="ghost" size="icon" asChild className="hidden sm:inline-flex">
            <Link
              href="https://github.com/Jye-a-dev/template_next_client"
              target="_blank"
              rel="noreferrer"
              aria-label="GitHub Repository"
            >
              <GithubIcon className="size-4" />
            </Link>
          </Button>

          <Button size="sm" asChild className="hidden sm:inline-flex gap-1">
            <Link href="/dashboard">
              Khám phá <ArrowRight className="size-3.5" />
            </Link>
          </Button>

          <div className="md:hidden">
            <Sheet open={isOpen} onOpenChange={setIsOpen}>
              <SheetTrigger asChild>
                <Button variant="ghost" size="icon" aria-label="Open Menu">
                  <Menu className="size-5" />
                </Button>
              </SheetTrigger>
              <SheetContent side="right">
                <SheetHeader>
                  <SheetTitle className="flex items-center gap-2">
                    <Layers className="size-5 text-primary" />
                    <span>Next.js Client</span>
                  </SheetTitle>
                </SheetHeader>
                <div className="flex flex-col gap-4 mt-8">
                  {NAV_ITEMS.map((item) => (
                    <Link
                      key={item.href}
                      href={item.href}
                      onClick={() => setIsOpen(false)}
                      className={cn(
                        "text-base font-medium transition-colors py-2 border-b border-border/40",
                        pathname === item.href
                          ? "text-primary font-semibold"
                          : "text-muted-foreground hover:text-foreground"
                      )}
                    >
                      {item.label}
                    </Link>
                  ))}
                  <Button asChild className="mt-4 w-full">
                    <Link href="/dashboard" onClick={() => setIsOpen(false)}>
                      Truy cập Dashboard
                    </Link>
                  </Button>
                </div>
              </SheetContent>
            </Sheet>
          </div>
        </div>
      </div>
    </header>
  );
}
