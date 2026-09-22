# Next.js Enterprise Client Template

Template Next.js Client chuẩn Production, hiện đại, tối ưu SEO, hiệu năng Web Vitals (LCP, CLS, INP) và tích hợp hệ thống UI/UX cao cấp (ui-skills).

## 1. Tech Stack & Kiến Trúc

- **Core Engine**: Next.js 15+ (App Router), React 19, TypeScript (Strict Mode).
- **Styling & UI Ecosystem**:
  - Tailwind CSS v4 kết hợp Radix UI primitives (zero runtime overhead, accessible).
  - Lucide React icons.
  - Motion micro-interactions (60fps).
  - Hỗ trợ `next-themes` cho Dark/Light mode chống hiện tượng FOUC/giật sáng.
- **State Management & Caching**:
  - React Server Components (RSC) cho việc prefetch dữ liệu ban đầu và SEO tối ưu.
  - TanStack Query v5 cho client-side polling, dynamic caching và optimistic updates.
  - Nuqs (Type-safe search params manager) đồng bộ URL search params làm state hai chiều.
  - Zustand với persistence cho global client state.
- **Form & Validation**:
  - Next.js Server Actions với `useActionState` và `revalidatePath`.
  - React Hook Form + Zod v4 cho end-to-end type safety.
  - Sonner Toast cho thông báo tương tác.

---

## 2. Cấu Trúc Thư Mục Chuẩn (`src/`)

```text
src/
├── app/                      # App router
│   ├── (auth)/               # Route groups (auth pages: login, register)
│   ├── (dashboard)/          # Route groups (dashboard pages)
│   ├── api/                  # Route handlers (BFF health check)
│   ├── layout.tsx            # Root layout (Fonts, SEO metadata, Providers)
│   ├── page.tsx              # Landing page
│   ├── error.tsx             # Global client error boundary
│   ├── not-found.tsx         # 404 page
│   └── loading.tsx           # Fallback loading skeleton
├── components/
│   ├── ui/                   # Shadcn/Radix components cơ sở (button, dialog, sheet, popover, card, input...)
│   └── shared/               # Components dùng chung (Header, Footer, ThemeToggle, Providers, EmptyState...)
├── features/                 # Domain-driven features
│   └── items/
│       ├── actions/          # Server Actions
│       ├── components/       # RSC và Client components riêng của feature
│       ├── hooks/            # Custom client hooks (Nuqs + TanStack Query)
│       ├── types/            # Type definitions & Zod schemas
│       └── utils/            # Feature helper logic
├── hooks/                    # Global hooks (useMounted, useMediaQuery, useDebounce...)
├── lib/                      # Cấu hình Fetcher/API client, env validation, cn helper, queryClient, zustand store
└── styles/                   # globals.css và Tailwind variables
```

---

## 3. Khởi Chạy Dự Án

### Yêu cầu
- Node.js 20+
- npm 10+

### Cài đặt
```bash
npm install
```

### Chạy Development Server
```bash
npm run dev
```

### Kiểm tra Kiểu dữ liệu & Build Production
```bash
npx tsc --noEmit
npm run build
npm run start
```
