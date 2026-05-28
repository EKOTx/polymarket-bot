"use client";

import { useState } from "react";
import { ArrowRight, CheckCircle } from "lucide-react";

export function WaitlistCTA() {
  const [email, setEmail] = useState("");
  const [marketing, setMarketing] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;
    setLoading(true);
    setError(null);
    try {
      // Waitlist signup — stores email + consent for future outreach
      const res = await fetch("/api/waitlist", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, marketing_consent: marketing }),
      });
      if (!res.ok) {
        const d = await res.json().catch(() => ({}));
        throw new Error(d.detail ?? "Signup failed");
      }
      setSubmitted(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section id="waitlist" className="py-24 px-4">
      <div className="max-w-2xl mx-auto text-center">
        {/* Glow */}
        <div className="absolute left-1/2 -translate-x-1/2 w-[400px] h-[200px] bg-[#388bfd]/6 rounded-full blur-[80px] pointer-events-none" />

        <div className="relative bg-[#161b22] border border-[#30363d] rounded-2xl px-8 py-12">
          {submitted ? (
            <div className="flex flex-col items-center gap-4">
              <CheckCircle className="w-12 h-12 text-emerald-400" />
              <h2 className="text-2xl font-bold text-[#e6edf3]">You&rsquo;re on the list!</h2>
              <p className="text-[#8b949e] text-sm">
                We&rsquo;ll notify you at <span className="text-[#388bfd]">{email}</span> when your
                access is ready.
              </p>
            </div>
          ) : (
            <>
              <h2 className="text-2xl md:text-3xl font-bold text-[#e6edf3] mb-3">
                Get early access
              </h2>
              <p className="text-[#8b949e] text-sm mb-8 max-w-md mx-auto">
                Join analysts already tracking prediction market signals. We&rsquo;re rolling out
                access progressively — be first in line.
              </p>

              <form onSubmit={submit} className="space-y-4">
                <div className="flex gap-2">
                  <input
                    type="email"
                    required
                    placeholder="you@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="flex-1 bg-[#0d1117] border border-[#30363d] rounded-md px-4 py-2.5 text-sm text-[#e6edf3] placeholder-[#484f58] focus:outline-none focus:border-[#388bfd]"
                  />
                  <button
                    type="submit"
                    disabled={loading}
                    className="flex items-center gap-2 bg-[#388bfd] hover:bg-[#1f6feb] disabled:opacity-50 text-white px-5 py-2.5 rounded-md text-sm font-medium transition-colors"
                  >
                    {loading ? "Joining…" : "Join"}
                    {!loading && <ArrowRight className="w-4 h-4" />}
                  </button>
                </div>

                {/* GDPR marketing consent */}
                <label className="flex items-start gap-3 cursor-pointer text-left">
                  <input
                    type="checkbox"
                    checked={marketing}
                    onChange={(e) => setMarketing(e.target.checked)}
                    className="mt-0.5 w-4 h-4 accent-[#388bfd] flex-shrink-0"
                  />
                  <span className="text-xs text-[#6e7681] leading-relaxed">
                    I agree to receive product updates and announcements by email. You can unsubscribe
                    at any time. Your email is used only for waitlist and service communication.
                    See our{" "}
                    <a href="/privacy" className="text-[#388bfd] hover:underline">
                      Privacy Policy
                    </a>
                    .
                  </span>
                </label>

                {error && (
                  <p className="text-xs text-red-400 bg-red-900/20 border border-red-800/30 rounded px-3 py-2">
                    {error}
                  </p>
                )}
              </form>
            </>
          )}
        </div>
      </div>
    </section>
  );
}
