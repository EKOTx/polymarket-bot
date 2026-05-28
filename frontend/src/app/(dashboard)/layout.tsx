"use client";

import { useEffect } from "react";
import { AuthGuard } from "@/components/layout/AuthGuard";
import { Sidebar } from "@/components/layout/Sidebar";
import { useScannerStore } from "@/lib/scannerStore";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { startPolling, stopPolling } = useScannerStore();

  useEffect(() => {
    startPolling();
    return () => stopPolling();
  }, [startPolling, stopPolling]);

  return (
    <AuthGuard>
      <div className="flex h-screen overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-y-auto">{children}</main>
      </div>
    </AuthGuard>
  );
}
