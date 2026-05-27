"use client";

import { useEffect, useState } from "react";
import { opportunitiesApi, ScannerStatus } from "@/lib/api";
import { formatTs } from "@/lib/utils";
import { Circle } from "lucide-react";

export function TopBar({ title }: { title: string }) {
  const [status, setStatus] = useState<ScannerStatus | null>(null);

  useEffect(() => {
    opportunitiesApi.scannerStatus().then(setStatus).catch(() => {});
    const id = setInterval(
      () => opportunitiesApi.scannerStatus().then(setStatus).catch(() => {}),
      30_000
    );
    return () => clearInterval(id);
  }, []);

  return (
    <header className="flex items-center justify-between px-6 py-3 border-b border-[#30363d] bg-[#161b22]">
      <h1 className="text-sm font-semibold tracking-wide text-[#e6edf3]">
        {title}
      </h1>

      {status && (
        <div className="flex items-center gap-3 text-xs text-[#6e7681]">
          <span className="flex items-center gap-1.5">
            <Circle
              className={`w-2 h-2 fill-current ${
                status.is_running ? "text-emerald-400" : "text-red-500"
              }`}
            />
            {status.is_running ? "Scanner live" : "Scanner idle"}
          </span>
          {status.last_scan_at && (
            <span>Last scan: {formatTs(status.last_scan_at)}</span>
          )}
          <span>{status.opportunities_found} opps found</span>
        </div>
      )}
    </header>
  );
}
