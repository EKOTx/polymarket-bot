"use client";

import { useEffect } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // TODO: Send error to Sentry when configured
    console.error("[DashboardError]", error);
  }, [error]);

  return (
    <div className="flex-1 flex items-center justify-center p-12">
      <div className="max-w-sm w-full text-center">
        <div className="w-10 h-10 rounded-lg bg-red-900/20 border border-red-800/40 flex items-center justify-center mx-auto mb-4">
          <AlertTriangle className="w-5 h-5 text-red-400" />
        </div>
        <h2 className="text-sm font-semibold text-[#e6edf3] mb-2">Failed to load</h2>
        <p className="text-xs text-[#6e7681] mb-5">
          {error.message || "An unexpected error occurred on this page."}
        </p>
        {error.digest && (
          <p className="text-xs text-[#484f58] font-mono mb-4">ID: {error.digest}</p>
        )}
        <button
          onClick={reset}
          className="inline-flex items-center gap-2 px-4 py-2 text-xs bg-[#21262d] border border-[#30363d] rounded text-[#e6edf3] hover:bg-[#30363d] transition-colors"
        >
          <RefreshCw className="w-3 h-3" />
          Retry
        </button>
      </div>
    </div>
  );
}
