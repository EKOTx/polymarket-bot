"use client";

import { useState } from "react";
import { X } from "lucide-react";
import { tradesApi, PaperTrade } from "@/lib/api";
import { formatUsd, cn } from "@/lib/utils";

interface Props {
  trade: PaperTrade;
  onClose: () => void;
  onSuccess: () => void;
}

export function CloseModal({ trade, onClose, onSuccess }: Props) {
  const [exitPrice, setExitPrice] = useState<string>("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const parsedPrice = exitPrice !== "" ? parseFloat(exitPrice) : undefined;
  const proceeds = parsedPrice != null ? trade.size_shares * parsedPrice : null;
  const pnl = proceeds != null ? proceeds - trade.cost_usd : null;

  const submit = async () => {
    setError(null);
    setSubmitting(true);
    try {
      await tradesApi.close(trade.id, parsedPrice);
      onSuccess();
      onClose();
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })
        ?.response?.data?.detail;
      setError(detail ?? "Close failed");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="bg-[#161b22] border border-[#30363d] rounded-lg w-full max-w-sm mx-4 shadow-xl">

        {/* Header */}
        <div className="flex items-start justify-between p-5 border-b border-[#30363d]">
          <div className="pr-4">
            <h2 className="text-sm font-semibold text-[#e6edf3]">Close Position</h2>
            <p className="text-xs text-[#6e7681] mt-0.5 line-clamp-2">{trade.question}</p>
          </div>
          <button onClick={onClose} className="text-[#6e7681] hover:text-[#e6edf3] shrink-0">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="p-5 space-y-5">

          {/* Trade summary */}
          <div className="bg-[#0d1117] rounded border border-[#30363d] divide-y divide-[#21262d] text-xs font-mono">
            {[
              { label: "Outcome", value: trade.outcome },
              { label: "Entry price", value: trade.entry_price.toFixed(4) },
              { label: "Shares", value: trade.size_shares.toFixed(2) },
              { label: "Cost", value: formatUsd(trade.cost_usd) },
            ].map(({ label, value }) => (
              <div key={label} className="flex justify-between px-3 py-2">
                <span className="text-[#6e7681]">{label}</span>
                <span className="text-[#e6edf3]">{value}</span>
              </div>
            ))}
          </div>

          {/* Exit price */}
          <div>
            <label className="text-xs text-[#6e7681] block mb-1">
              Exit price <span className="text-[#484f58]">(leave blank to use current market price)</span>
            </label>
            <input
              type="number"
              value={exitPrice}
              onChange={(e) => setExitPrice(e.target.value)}
              placeholder="auto"
              min={0.001}
              max={0.999}
              step={0.001}
              className="w-full bg-[#0d1117] border border-[#30363d] rounded px-3 py-2 text-sm text-[#e6edf3] font-mono placeholder-[#484f58]"
            />
          </div>

          {/* PnL preview */}
          {pnl !== null && (
            <div className="flex justify-between text-xs font-mono bg-[#0d1117] rounded border border-[#30363d] px-3 py-2">
              <span className="text-[#6e7681]">Estimated PnL</span>
              <span className={cn("font-semibold", pnl >= 0 ? "text-emerald-400" : "text-red-400")}>
                {formatUsd(pnl)}
              </span>
            </div>
          )}

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
              disabled={submitting}
              className="flex-1 py-2 text-sm rounded bg-red-800 hover:bg-red-700 disabled:opacity-50 text-white transition-colors font-mono"
            >
              {submitting ? "Closing…" : "Close position"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
