"use client";

import { useState } from "react";
import { X } from "lucide-react";
import { tradesApi, Opportunity } from "@/lib/api";
import { formatUsd, cn } from "@/lib/utils";

interface Props {
  opportunity: Opportunity;
  onClose: () => void;
  onSuccess: () => void;
}

const SIZE_PRESETS = [25, 50, 100, 200];
const SLIPPAGE = 0.002;
const FEE_PCT = 0.01;

function calcPreview(ask: number, sizeUsd: number) {
  const entry = Math.min(ask * (1 + SLIPPAGE), 0.999);
  const fee = sizeUsd * FEE_PCT;
  const total = sizeUsd + fee;
  const shares = sizeUsd / entry;
  return { entry, fee, total, shares };
}

export function TradeModal({ opportunity: opp, onClose, onSuccess }: Props) {
  const [outcome, setOutcome] = useState<"YES" | "NO">("YES");
  const [sizeUsd, setSizeUsd] = useState(
    Math.min(opp.suggested_size_usd || 50, 200)
  );
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const ask =
    outcome === "YES"
      ? (opp.yes_ask ?? 0.5)
      : (opp.no_ask ?? 1 - (opp.yes_bid ?? 0.5));

  const { entry, fee, total, shares } = calcPreview(ask, sizeUsd);

  const submit = async () => {
    setError(null);
    setSubmitting(true);
    try {
      await tradesApi.place({ opportunity_id: opp.id, outcome, size_usd: sizeUsd });
      onSuccess();
      onClose();
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })
        ?.response?.data?.detail;
      setError(detail ?? "Trade failed");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="bg-[#161b22] border border-[#30363d] rounded-lg w-full max-w-md mx-4 shadow-xl">

        {/* Header */}
        <div className="flex items-start justify-between p-5 border-b border-[#30363d]">
          <div className="pr-4">
            <h2 className="text-sm font-semibold text-[#e6edf3]">Paper Trade</h2>
            <p className="text-xs text-[#6e7681] mt-0.5 line-clamp-2">{opp.title}</p>
          </div>
          <button onClick={onClose} className="text-[#6e7681] hover:text-[#e6edf3] shrink-0">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="p-5 space-y-5">

          {/* Outcome */}
          <div>
            <label className="text-xs text-[#6e7681] block mb-2">Outcome</label>
            <div className="flex gap-2">
              {(["YES", "NO"] as const).map((o) => (
                <button
                  key={o}
                  onClick={() => setOutcome(o)}
                  className={cn(
                    "flex-1 py-2 text-sm font-mono rounded border transition-colors",
                    outcome === o
                      ? o === "YES"
                        ? "bg-emerald-900/50 border-emerald-600 text-emerald-300"
                        : "bg-red-900/50 border-red-700 text-red-300"
                      : "bg-[#1c2128] border-[#30363d] text-[#6e7681] hover:border-[#6e7681]"
                  )}
                >
                  {o}
                  <span className="ml-2 text-xs opacity-70">
                    @{o === "YES" ? (opp.yes_ask ?? "—") : (opp.no_ask ?? "—")}
                  </span>
                </button>
              ))}
            </div>
          </div>

          {/* Size */}
          <div>
            <label className="text-xs text-[#6e7681] block mb-2">Size (USD)</label>
            <div className="flex gap-2 mb-2">
              {SIZE_PRESETS.map((p) => (
                <button
                  key={p}
                  onClick={() => setSizeUsd(p)}
                  className={cn(
                    "flex-1 py-1 text-xs rounded border transition-colors font-mono",
                    sizeUsd === p
                      ? "bg-[#21262d] border-[#6e7681] text-[#e6edf3]"
                      : "bg-[#1c2128] border-[#30363d] text-[#6e7681] hover:border-[#6e7681]"
                  )}
                >
                  ${p}
                </button>
              ))}
            </div>
            <input
              type="number"
              value={sizeUsd}
              onChange={(e) => setSizeUsd(Math.max(1, Number(e.target.value)))}
              min={1}
              max={500}
              step={5}
              className="w-full bg-[#0d1117] border border-[#30363d] rounded px-3 py-2 text-sm text-[#e6edf3] font-mono"
            />
          </div>

          {/* Preview */}
          <div className="bg-[#0d1117] rounded border border-[#30363d] divide-y divide-[#21262d] text-xs font-mono">
            {[
              { label: "Entry price", value: entry.toFixed(4) },
              { label: "Shares", value: shares.toFixed(2) },
              { label: "Fee (1%)", value: formatUsd(fee) },
              { label: "Total cost", value: formatUsd(total), bold: true },
            ].map(({ label, value, bold }) => (
              <div key={label} className="flex justify-between px-3 py-2">
                <span className="text-[#6e7681]">{label}</span>
                <span className={cn("text-[#e6edf3]", bold && "font-semibold")}>{value}</span>
              </div>
            ))}
          </div>

          {error && (
            <p className="text-xs text-red-400 bg-red-900/20 border border-red-800/40 rounded px-3 py-2">
              {error}
            </p>
          )}

          {/* Actions */}
          <div className="flex gap-3">
            <button
              onClick={onClose}
              className="flex-1 py-2 text-sm rounded border border-[#30363d] text-[#6e7681] hover:text-[#e6edf3] transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={submit}
              disabled={submitting || sizeUsd <= 0}
              className="flex-1 py-2 text-sm rounded bg-emerald-700 hover:bg-emerald-600 disabled:opacity-50 text-white transition-colors font-mono"
            >
              {submitting ? "Placing…" : "Execute paper trade"}
            </button>
          </div>

          <p className="text-xs text-center text-[#6e7681]">
            Paper trade only — no real money involved
          </p>
        </div>
      </div>
    </div>
  );
}
