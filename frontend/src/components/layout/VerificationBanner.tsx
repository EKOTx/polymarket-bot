"use client";

import { useState } from "react";
import { authApi } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export function VerificationBanner() {
  const { user } = useAuth();
  const [sent, setSent] = useState(false);
  const [sending, setSending] = useState(false);
  const [devLink, setDevLink] = useState<string | null>(null);

  if (!user || user.is_verified) return null;

  async function handleResend() {
    setSending(true);
    try {
      const res = await authApi.resendVerification();
      setSent(true);
      if (res.dev_token) {
        setDevLink(`/verify-email?token=${res.dev_token}`);
      }
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="border-b border-yellow-500/30 bg-yellow-500/10 px-4 py-2.5">
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-yellow-200">
        <span>
          Verify your email address to unlock all features.
          Check your inbox for a verification link.
        </span>
        {!sent ? (
          <button
            onClick={handleResend}
            disabled={sending}
            className="ml-auto shrink-0 rounded px-3 py-1 text-xs font-medium text-yellow-100 underline-offset-2 hover:underline disabled:opacity-50"
          >
            {sending ? "Sending…" : "Resend email"}
          </button>
        ) : (
          <span className="ml-auto shrink-0 text-xs text-yellow-300">
            Sent!{" "}
            {devLink && (
              <a href={devLink} className="underline">
                [dev: verify now]
              </a>
            )}
          </span>
        )}
      </div>
    </div>
  );
}
