import * as React from "react";
import { AdminGuard } from "@/components/admin/admin-guard";
import { AdminSidebar } from "@/components/layout/admin/admin-sidebar";
import { AdminHeader } from "@/components/layout/admin/admin-header";
import { AdminFooter } from "@/components/layout/admin/admin-footer";


interface AdminLayoutProps {
  children: React.ReactNode;
}

export default function AdminLayout({ children }: AdminLayoutProps) {
  return (
    <AdminGuard>
      <div className="flex min-h-screen bg-muted/20 text-foreground">
        {/* Collapsible Left Admin Sidebar */}
        <AdminSidebar />

        {/* Right Canvas */}
        <div className="flex flex-1 flex-col min-w-0">
          <AdminHeader />
          <main className="flex-1 p-4 sm:p-6 lg:p-8 overflow-y-auto">
            <div className="mx-auto max-w-[1600px] w-full space-y-6">
              {children}
            </div>
          </main>
          <AdminFooter />
        </div>
      </div>
    </AdminGuard>
  );
}

