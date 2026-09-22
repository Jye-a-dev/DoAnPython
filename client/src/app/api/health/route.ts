import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json(
    {
      status: "ok",
      timestamp: new Date().toISOString(),
      uptime: process.uptime(),
      version: "1.0.0",
      framework: "Next.js 15+ App Router",
      engine: "React 19",
    },
    { status: 200 }
  );
}

