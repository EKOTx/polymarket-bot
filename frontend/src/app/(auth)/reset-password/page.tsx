"use client";

import { useState, Suspense } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Activity, CheckCircle } from "lucide-react";
import { authApi } from "@/lib/api";

function ResetPasswordForm() {
  const router = useRouter();
  const params = useSearchParams();
  const token = params.get("token") ?? "";

  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState("");

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password !== confirm) {
      setError("Passwords do not match");
      return;
    }
    setError("");
    setLoading(true);
    try {
      await authApi.resetPassword(token, password);
      setDone(true);
      setTimeout(() => router.push("/login"), 2500);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg ?? "Reset failed. The link may have expired.");
    } finally {
      setLoading(false);
    }
  };

  if (!token) {
    return (
      <div className="text-center space-y-3">
        <p className="text-sm text-red-400">Invalid reset link.</p>
        <Link href="/forgot-password" className="text-xs text-[#388bfd] hover:underline">
          Request a new one
        </Link>
      </div>
    );
  }

  return (
    <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-8">
      {done ? (
        <div className="text-center space-y-4">
          <CheckCircle className="w-10 h-10 text-emerald-400 mx-auto" />
          <h1 className="text-sm font-semibold text-[#e6edf3]">Password updated</h1>
          <p className="text-xs text-[#6e7681]">Redirecting to sign in…</p>
        </div>
      ) : (
        <>
          <h1 className="text-sm font-semibold text-[#e6edf3] mb-5">Set new password</h1>

          {error && (
            <div className="mb-4 p-3 bg-red-900/30 border border-red-800 rounded text-red-400 text-xs">
              {error}
            </div>
          )}

          <form onSubmit={submit} className="space-y-4">
            <div>
              <label className="text-xs text-[#6e7681] block mb-1">New password</label>
              <input
                type="password"
                required
                minLength={8}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-[#0d1117] border border-[#30363d] rounded px-3 py-2 text-sm text-[#e6edf3] placeholder-[#6e7681]"
                placeholder="min 8 characters"
                autoComplete="new-password"
              />
            </div>
            <div>
              <label className="text-xs text-[#6e7681] block mb-1">Confirm password</label>
              <input
                type="password"
                required
                minLength={8}
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                className="w-full bg-[#0d1117] border border-[#30363d] rounded px-3 py-2 text-sm text-[#e6edf3] placeholder-[#6e7681]"
                placeholder="repeat password"
                autoComplete="new-password"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full py-2 text-sm font-mono rounded bg-emerald-700 hover:bg-emerald-600 text-white transition-colors disabled:opacity-50"
            >
              {loading ? "Updating…" : "Update password →"}
            </button>
          </form>

          <p className="mt-4 text-xs text-center text-[#6e7681]">
            <Link href="/login" className="text-[#388bfd] hover:underline">Back to sign in</Link>
          </p>
        </>
      )}
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0d1117]">
      <div className="w-full max-w-sm">
        <div className="flex items-center justify-center gap-2 mb-8">
          <Activity className="w-6 h-6 text-emerald-400" />
          <span className="text-lg font-semibold text-[#e6edf3] tracking-wide font-mono">
            Polymarket Intel
          </span>
        </div>
        <Suspense fallback={<div className="text-xs text-[#6e7681] text-center">Loading…</div>}>
          <ResetPasswordForm />
        </Suspense>
      </div>
    </div>
  );
}
