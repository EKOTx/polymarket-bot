"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { authApi } from "@/lib/api";
import { useAuth } from "@/lib/auth";

function VerifyEmailContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { loadUser } = useAuth();
  const [status, setStatus] = useState<"verifying" | "success" | "error">("verifying");
  const [message, setMessage] = useState("");

  useEffect(() => {
    const token = searchParams.get("token");
    if (!token) {
      setStatus("error");
      setMessage("No verification token found in link.");
      return;
    }

    authApi
      .verifyEmail(token)
      .then(async () => {
        await loadUser();
        setStatus("success");
        setMessage("Email verified! Redirecting to dashboard…");
        setTimeout(() => router.push("/dashboard"), 2000);
      })
      .catch((err) => {
        setStatus("error");
        setMessage(
          err?.response?.data?.detail ?? "Invalid or expired verification link."
        );
      });
  }, [searchParams, router, loadUser]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-950 px-4">
      <div className="w-full max-w-sm rounded-xl border border-gray-800 bg-gray-900 p-8 text-center">
        {status === "verifying" && (
          <>
            <div className="mx-auto mb-4 h-8 w-8 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent" />
            <p className="text-gray-300">Verifying your email…</p>
          </>
        )}
        {status === "success" && (
          <>
            <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-green-500/20 text-green-400 text-2xl">
              ✓
            </div>
            <h1 className="mb-2 text-xl font-semibold text-white">Email Verified</h1>
            <p className="text-gray-400">{message}</p>
          </>
        )}
        {status === "error" && (
          <>
            <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-red-500/20 text-red-400 text-2xl">
              ✕
            </div>
            <h1 className="mb-2 text-xl font-semibold text-white">Verification Failed</h1>
            <p className="mb-6 text-gray-400">{message}</p>
            <a
              href="/dashboard"
              className="inline-block rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
            >
              Go to Dashboard
            </a>
          </>
        )}
      </div>
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={
      <div className="flex min-h-screen items-center justify-center bg-gray-950">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent" />
      </div>
    }>
      <VerifyEmailContent />
    </Suspense>
  );
}
