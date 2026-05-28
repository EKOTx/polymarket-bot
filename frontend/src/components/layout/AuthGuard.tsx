"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const [mounted, setMounted] = useState(false);
  const { token, user, isLoading, loadUser } = useAuth();
  const router = useRouter();

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted) return;
    if (!token) {
      router.push("/login");
    } else if (!user) {
      loadUser();
    }
  }, [mounted, token, user, loadUser, router]);

  if (!mounted) return null;
  if (!token) return null;
  if (!user && isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <span className="text-[#6e7681] text-sm animate-pulse">Loading…</span>
      </div>
    );
  }

  return <>{children}</>;
}
