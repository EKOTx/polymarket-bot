"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { Cookie, X } from "lucide-react";

const STORAGE_KEY = "cookie_consent_v1";

export function CookieBanner() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) setVisible(true);
  }, []);

  const accept = () => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ necessary: true, analytics: true, ts: Date.now() }));
    setVisible(false);
  };

  const necessaryOnly = () => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ necessary: true, analytics: false, ts: Date.now() }));
    setVisible(false);
  };

  if (!visible) return null;

  return (
    <div className="fixed bottom-4 left-4 right-4 z-50 flex justify-center pointer-events-none">
      <div className="pointer-events-auto w-full max-w-xl bg-[#161b22] border border-[#30363d] rounded-xl shadow-2xl px-5 py-4">
        <div className="flex items-start gap-3">
          <Cookie className="w-5 h-5 text-[#6e7681] flex-shrink-0 mt-0.5" />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-[#e6edf3] mb-1">This site uses cookies</p>
            <p className="text-xs text-[#6e7681] leading-relaxed">
              We use necessary cookies for authentication and session management. With your consent,
              we also collect anonymous analytics to improve the product.{" "}
              <Link href="/cookies" className="text-[#388bfd] hover:underline">
                Cookie Policy
              </Link>
              {" · "}
              <Link href="/privacy" className="text-[#388bfd] hover:underline">
                Privacy Policy
              </Link>
            </p>
          </div>
          <button
            onClick={necessaryOnly}
            className="text-[#6e7681] hover:text-[#e6edf3] flex-shrink-0"
            aria-label="Dismiss"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
        <div className="flex gap-2 mt-4 justify-end">
          <button
            onClick={necessaryOnly}
            className="px-4 py-2 text-xs rounded-md border border-[#30363d] text-[#8b949e] hover:text-[#e6edf3] hover:bg-[#21262d] transition-colors"
          >
            Necessary only
          </button>
          <button
            onClick={accept}
            className="px-4 py-2 text-xs rounded-md bg-[#388bfd] hover:bg-[#1f6feb] text-white font-medium transition-colors"
          >
            Accept all
          </button>
        </div>
      </div>
    </div>
  );
}
