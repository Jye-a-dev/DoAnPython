import Link from "next/link";
import { Camera, Globe } from "lucide-react";

export function Footer() {
  return (
    <footer className="w-full border-t border-border/40 bg-muted/30 py-8">
      <div className="container mx-auto px-4 sm:px-8 flex flex-col md:flex-row items-center justify-between gap-4 text-center md:text-left">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground font-bold">
            <Camera className="h-4 w-4" />
          </div>
          <span className="font-semibold text-sm">Visual AI E-Commerce Platform</span>
        </div>

        <p className="text-xs text-muted-foreground">
          © {new Date().getFullYear()} Visual AI Store. Nền tảng mua sắm kết hợp nhận diện thị giác máy tính và giọng đọc AI.
        </p>

        <div className="flex items-center gap-4 text-xs text-muted-foreground">
          <Link
            href="https://github.com/Jye-a-dev/template_next_client"
            target="_blank"
            className="hover:text-foreground flex items-center gap-1 transition-colors"
          >
            <Globe className="h-4 w-4" />
            GitHub Template
          </Link>
        </div>
      </div>
    </footer>
  );
}

