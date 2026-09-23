import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  // Allow Next.js build time worker to collect page data without redirecting
  if (process.env.NEXT_PHASE === "phase-production-build") {
    return NextResponse.next();
  }

  const { pathname } = request.nextUrl;
  const token = request.cookies.get("auth_token")?.value;
  const role = request.cookies.get("auth_role")?.value;

  const isAdminRoute = pathname.startsWith("/admin");
  const isUserProtectedRoute =
    pathname.startsWith("/profile") || pathname.startsWith("/orders");
  const isAuthRoute = pathname === "/login" || pathname === "/register";

  // 1. Tuyến /admin
  if (isAdminRoute) {
    if (!token) {
      const loginUrl = new URL("/login", request.url);
      loginUrl.searchParams.set("redirect", pathname);
      return NextResponse.redirect(loginUrl);
    }
    if (role !== "1") {
      return NextResponse.redirect(new URL("/", request.url));
    }
  }

  // 2. Tuyến cá nhân người dùng
  if (isUserProtectedRoute) {
    if (!token) {
      const loginUrl = new URL("/login", request.url);
      loginUrl.searchParams.set("redirect", pathname);
      return NextResponse.redirect(loginUrl);
    }
  }

  // 3. Tuyến Auth (/login, /register)
  if (isAuthRoute && token) {
    // Tránh redirect loop: điều hướng thẳng về /admin hoặc /, bỏ qua redirect query param
    return NextResponse.redirect(
      new URL(role === "1" ? "/admin" : "/", request.url)
    );
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};
