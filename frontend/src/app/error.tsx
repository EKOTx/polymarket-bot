"use client";

import { useEffect } from "react";
import * as Sentry from "@sentry/nextjs";
import { AlertTriangle } from "lucide-react";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    Sentry.captureException(error);
    console.error("[GlobalError]", error);
  }, [error]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0d1117]">
      <div className="max-w-sm w-full mx-4 text-center">
        <div className="w-12 h-12 rounded-full bg-red-900/30 border border-red-800/50 flex items-center justify-center mx-auto mb-4">
          <AlertTriangle className="w-6 h-6 text-red-400" />
        </div>
        <h1 className="text-base font-semibold text-[#e6edf3] mb-2">Something went wrong</h1>
        <p className="text-sm text-[#6e7681] mb-6">
          An unexpected error occurred. If this keeps happening, contact support.
        </p>
        {error.digest && (
          <p className="text-xs text-[#484f58] font-mono mb-4">Error ID: {error.digest}</p>
        )}
        <button
          onClick={reset}
          className="px-4 py-2 text-sm bg-[#21262d] border border-[#30363d] rounded text-[#e6edf3] hover:bg-[#30363d] transition-colors"
        >
          Try again
        </button>
      </div>
    </div>
  );
}
