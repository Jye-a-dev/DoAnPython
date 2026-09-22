import Link from "next/link";
import { Compass, Home } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center p-6 text-center">
      <div className="flex size-16 items-center justify-center rounded-2xl bg-muted text-muted-foreground mb-4">
        <Compass className="size-8 animate-pulse text-primary" />
      </div>
      <span className="font-mono text-xs font-semibold uppercase tracking-widest text-primary">
        404 - Not Found
      </span>
      <h1 className="mt-2 text-3xl font-extrabold tracking-tight sm:text-4xl">
        Không tìm thấy trang yêu cầu
      </h1>
      <p className="mt-3 text-sm text-muted-foreground max-w-md">
        Đường dẫn bạn đang truy cập không tồn tại hoặc đã được di dời sang vị trí khác.
      </p>
      <div className="mt-6">
        <Button asChild className="gap-2">
          <Link href="/">
            <Home className="size-4" />
            <span>Trở về Trang chủ</span>
          </Link>
        </Button>
      </div>
    </div>
  );
}

