import Link from "next/link";
import { Layers } from "lucide-react";

export function Footer() {
  return (
    <footer className="border-t bg-muted/30">
      <div className="container mx-auto flex flex-col items-center justify-between gap-4 py-10 md:h-24 md:flex-row md:py-0 px-4 sm:px-8 max-w-7xl">
        <div className="flex flex-col items-center gap-4 px-8 md:flex-row md:gap-2 md:px-0">
          <div className="flex size-6 items-center justify-center rounded-md bg-primary text-primary-foreground">
            <Layers className="size-4" />
          </div>
          <p className="text-center text-sm leading-loose text-muted-foreground md:text-left">
            Được xây dựng với{" "}
            <Link
              href="https://nextjs.org"
              target="_blank"
              rel="noreferrer"
              className="font-medium underline underline-offset-4 hover:text-foreground"
            >
              Next.js 15+ App Router
            </Link>{" "}
            &amp; Tailwind CSS v4. Template tối ưu hiệu năng và UX.
          </p>
        </div>
      </div>
    </footer>
  );
}

