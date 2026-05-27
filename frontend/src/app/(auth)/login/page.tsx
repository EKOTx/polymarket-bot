"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Activity } from "lucide-react";
import { useAuth } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
      router.push("/dashboard");
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg ?? "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0d1117]">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="flex items-center justify-center gap-2 mb-8">
          <Activity className="w-6 h-6 text-emerald-400" />
          <span className="text-lg font-semibold text-[#e6edf3] tracking-wide font-mono">
            Polymarket Intel
          </span>
        </div>

        {/* Card */}
        <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-8">
          <h1 className="text-sm font-semibold text-[#e6edf3] mb-6">Sign in</h1>

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
            <div>
              <label className="text-xs text-[#6e7681] block mb-1">Password</label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-[#0d1117] border border-[#30363d] rounded px-3 py-2 text-sm text-[#e6edf3] placeholder-[#6e7681]"
                placeholder="••••••••"
                autoComplete="current-password"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2 text-sm font-mono rounded bg-emerald-700 hover:bg-emerald-600 text-white transition-colors disabled:opacity-50"
            >
              {loading ? "Signing in…" : "Sign in →"}
            </button>
          </form>

          <p className="mt-4 text-xs text-center text-[#6e7681]">
            No account?{" "}
            <Link href="/register" className="text-[#388bfd] hover:underline">
              Register
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
