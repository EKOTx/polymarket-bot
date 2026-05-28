"use client";

import { useScannerStore } from "@/lib/scannerStore";
import { formatTs } from "@/lib/utils";
import { Circle } from "lucide-react";

export function TopBar({ title }: { title: string }) {
  const { status, refreshKey } = useScannerStore();

  return (
    <header className="flex items-center justify-between px-6 py-3 border-b border-[#30363d] bg-[#161b22]">
      <h1 className="text-sm font-semibold tracking-wide text-[#e6edf3]">
        {title}
      </h1>

      <div className="flex items-center gap-3 text-xs text-[#6e7681]">
        {refreshKey > 0 && (
          <span className="text-emerald-500 font-mono">↻ #{refreshKey}</span>
        )}
        {status && (
          <>
            <span className="flex items-center gap-1.5">
              <Circle
                className={`w-2 h-2 fill-current ${
                  status.is_running ? "text-emerald-400" : "text-[#6e7681]"
                }`}
              />
              {status.is_running ? "Scanner live" : "Scanner idle"}
            </span>
            {status.last_scan_at && (
              <span>Last scan: {formatTs(status.last_scan_at)}</span>
            )}
            <span>{status.opportunities_found} opps</span>
          </>
        )}
      </div>
    </header>
  );
}
