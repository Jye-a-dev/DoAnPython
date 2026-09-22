import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import { Navbar } from "@/components/layout/navbar";
import { Footer } from "@/components/layout/footer";
import { Providers } from "@/components/shared/providers";
import "@/styles/globals.css";

const inter = Inter({
  subsets: ["latin", "vietnamese"],
  variable: "--font-sans",
  display: "swap",
});

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#ffffff" },
    { media: "(prefers-color-scheme: dark)", color: "#090d16" },
  ],
  width: "device-width",
  initialScale: 1,
};

export const metadata: Metadata = {
  title: {
    default: "Visual AI Store - Mua Sắm Bằng Thị Giác AI",
    template: "%s | Visual AI Store",
  },
  description:
    "Nền tảng mua sắm kết hợp mô hình YOLO AI nhận diện ảnh và công nghệ chuyển văn bản thành giọng nói (TTS) thời gian thực.",
  keywords: ["Visual AI", "YOLO", "E-Commerce", "Next.js 15", "App Router", "Object Detection", "Voice Checkout"],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="vi" suppressHydrationWarning className={inter.variable}>
      <body className="min-h-screen bg-background font-sans text-foreground antialiased flex flex-col">
        <Providers>
          <Navbar />
          <main className="flex-1 flex flex-col">{children}</main>
          <Footer />
        </Providers>
      </body>
    </html>
  );
}
