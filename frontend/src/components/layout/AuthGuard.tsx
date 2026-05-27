"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const { token, user, isLoading, loadUser } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!token) {
      router.push("/login");
    } else if (!user) {
      loadUser();
    }
  }, [token, user, loadUser, router]);

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
