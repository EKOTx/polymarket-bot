"use client";

import { useState } from "react";
import Link from "next/link";
import { Activity, ArrowLeft, CheckCircle } from "lucide-react";
import { authApi } from "@/lib/api";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);
  const [devToken, setDevToken] = useState<string | null>(null);
  const [error, setError] = useState("");

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await authApi.forgotPassword(email);
      setDone(true);
      if (res.dev_token) setDevToken(res.dev_token);
    } catch {
      setError("Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0d1117]">
      <div className="w-full max-w-sm">
        <div className="flex items-center justify-center gap-2 mb-8">
          <Activity className="w-6 h-6 text-emerald-400" />
          <span className="text-lg font-semibold text-[#e6edf3] tracking-wide font-mono">
            Polymarket Intel
          </span>
        </div>

        <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-8">
          {done ? (
            <div className="text-center space-y-4">
              <CheckCircle className="w-10 h-10 text-emerald-400 mx-auto" />
              <h1 className="text-sm font-semibold text-[#e6edf3]">Check your email</h1>
              <p className="text-xs text-[#6e7681] leading-relaxed">
                If <span className="text-[#e6edf3]">{email}</span> is registered, a reset
                link has been sent. Check your spam folder if it doesn&rsquo;t arrive.
              </p>
              {devToken && (
                <div className="mt-4 bg-amber-900/20 border border-amber-700/40 rounded p-3 text-left">
                  <p className="text-xs text-amber-400 font-semibold mb-1">Dev mode — no SMTP configured</p>
                  <p className="text-xs text-[#6e7681] mb-2">Use this link to reset:</p>
                  <Link
                    href={`/reset-password?token=${devToken}`}
                    className="text-xs text-[#388bfd] hover:underline break-all font-mono"
                  >
                    /reset-password?token={devToken}
                  </Link>
                </div>
              )}
              <Link href="/login" className="block text-xs text-[#388bfd] hover:underline mt-4">
                Back to sign in
              </Link>
            </div>
          ) : (
            <>
              <div className="flex items-center gap-2 mb-6">
                <Link href="/login" className="text-[#6e7681] hover:text-[#e6edf3]">
                  <ArrowLeft className="w-4 h-4" />
                </Link>
                <h1 className="text-sm font-semibold text-[#e6edf3]">Reset password</h1>
              </div>

              <p className="text-xs text-[#6e7681] mb-5">
                Enter your account email and we&rsquo;ll send a reset link.
              </p>

              {error && (
                <div className="mb-4 p-3 bg-red-900/30 border border-red-800 rounded text-red-400 text-xs">
                  {error}
                </div>
              )}

              <form onSubmit={submit} className="space-y-4">
                <div>
                  <label className="text-xs text-[#6e7681] block mb-1">Email</label>
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full bg-[#0d1117] border border-[#30363d] rounded px-3 py-2 text-sm text-[#e6edf3] placeholder-[#6e7681]"
                    placeholder="you@example.com"
                    autoComplete="email"
                  />
                </div>
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-2 text-sm font-mono rounded bg-[#388bfd] hover:bg-[#1f6feb] text-white transition-colors disabled:opacity-50"
                >
                  {loading ? "Sending…" : "Send reset link →"}
                </button>
              </form>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
