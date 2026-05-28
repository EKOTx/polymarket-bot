"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { TopBar } from "@/components/layout/TopBar";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { TradeModal } from "@/components/trades/TradeModal";
import { opportunitiesApi, Opportunity } from "@/lib/api";
import { useScannerStore } from "@/lib/scannerStore";
import { formatEdge, formatUsd, formatTs, cn } from "@/lib/utils";

const TYPE_OPTIONS = ["", "VALUE", "SPREAD", "HIGH_VIG", "TOURNAMENT_ARB"];

export default function OpportunitiesPage() {
  const { refreshKey } = useScannerStore();
  const [items, setItems] = useState<Opportunity[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [oppType, setOppType] = useState("");
  const [minEdge, setMinEdge] = useState(0);
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState<number | null>(null);
  const [tradeTarget, setTradeTarget] = useState<Opportunity | null>(null);

  useEffect(() => {
    setLoading(true);
    opportunitiesApi
      .list({
        opp_type: oppType || undefined,
        min_edge: minEdge,
        page,
        page_size: 50,
      })
      .then((r) => {
        setItems(r.items);
        setTotal(r.total);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [oppType, minEdge, page, refreshKey]);

  return (
    <div>
      {tradeTarget && (
        <TradeModal
          opportunity={tradeTarget}
          onClose={() => setTradeTarget(null)}
          onSuccess={() => setTradeTarget(null)}
        />
      )}
      <TopBar title="Opportunities" />
      <div className="p-6 space-y-4">
        {/* Filters */}
        <div className="flex items-center gap-3 flex-wrap">
          <select
            value={oppType}
            onChange={(e) => { setOppType(e.target.value); setPage(1); }}
            className="bg-[#1c2128] border border-[#30363d] text-[#e6edf3] text-sm rounded px-3 py-1.5"
          >
            {TYPE_OPTIONS.map((t) => (
              <option key={t} value={t}>{t || "All types"}</option>
            ))}
          </select>

          <div className="flex items-center gap-2">
            <label className="text-xs text-[#6e7681]">Min edge</label>
            <input
              type="number"
              value={minEdge}
              onChange={(e) => { setMinEdge(Number(e.target.value)); setPage(1); }}
              className="bg-[#1c2128] border border-[#30363d] text-[#e6edf3] text-sm rounded px-2 py-1.5 w-20"
              min={0}
              step={0.5}
            />
            <span className="text-xs text-[#6e7681]">%</span>
          </div>

          <span className="text-xs text-[#6e7681] ml-auto">{total} results</span>
        </div>

        {/* Table */}
        <Card className="p-0 overflow-hidden">
          {loading ? (
            <p className="text-sm text-[#6e7681] p-6">Loading…</p>
          ) : items.length === 0 ? (
            <p className="text-sm text-[#6e7681] p-6">No opportunities match filters.</p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Type</th>
                  <th>Market</th>
                  <th>Edge</th>
                  <th>Confidence</th>
                  <th>EV</th>
                  <th>Suggested</th>
                  <th>Vig</th>
                  <th>Scanned</th>
                </tr>
              </thead>
              <tbody>
                {items.map((o) => (
                  <React.Fragment key={o.id}>
                    <tr
                      className="cursor-pointer"
                      onClick={() => setExpanded(expanded === o.id ? null : o.id)}
                    >
                      <td><Badge type={o.opportunity_type}>{o.opportunity_type}</Badge></td>
                      <td className="max-w-xs">
                        {o.market_id ? (
                          <Link
                            href={`/markets/${encodeURIComponent(o.market_id)}`}
                            className="block truncate text-xs text-[#388bfd] hover:underline"
                            onClick={(e) => e.stopPropagation()}
                          >
                            {o.title}
                          </Link>
                        ) : (
                          <p className="truncate text-xs">{o.title}</p>
                        )}
                        <p className="text-xs text-[#6e7681] truncate">{o.event_title}</p>
                      </td>
                      <td>
                        <span className={cn("font-mono font-semibold", o.edge_pct >= 5 ? "text-emerald-400" : "text-emerald-300")}>
                          {formatEdge(o.edge_pct)}
                        </span>
                      </td>
                      <td className="font-mono text-[#8b949e]">
                        {(o.confidence * 100).toFixed(0)}%
                      </td>
                      <td className={cn("font-mono", o.expected_value >= 0 ? "text-emerald-400" : "text-red-400")}>
                        {formatEdge(o.expected_value)}
                      </td>
                      <td className="font-mono text-[#8b949e]">{formatUsd(o.suggested_size_usd, 0)}</td>
                      <td className="font-mono text-amber-400">
                        {o.vig_pct != null ? formatEdge(o.vig_pct) : "—"}
                      </td>
                      <td className="text-xs text-[#6e7681]">{formatTs(o.timestamp)}</td>
                    </tr>
                    {expanded === o.id && (
                      <tr key={`${o.id}-detail`}>
                        <td colSpan={8} className="bg-[#161b22] px-4 py-3">
                          <div className="grid grid-cols-2 gap-4 text-xs">
                            <div>
                              <p className="text-[#6e7681] mb-1">Market ID</p>
                              <p className="font-mono text-[#8b949e]">{o.market_id ?? "—"}</p>
                            </div>
                            <div>
                              <p className="text-[#6e7681] mb-1">Bid / Ask</p>
                              <p className="font-mono">
                                {o.yes_bid != null ? o.yes_bid.toFixed(3) : "—"} /{" "}
                                {o.yes_ask != null ? o.yes_ask.toFixed(3) : "—"}
                              </p>
                            </div>
                            <div>
                              <p className="text-[#6e7681] mb-1">Liquidity</p>
                              <p className="font-mono">{formatUsd(o.liquidity, 0)}</p>
                            </div>
                            {o.warnings.length > 0 && (
                              <div>
                                <p className="text-[#6e7681] mb-1">Warnings</p>
                                {o.warnings.map((w, i) => (
                                  <p key={i} className="text-amber-400">⚠ {w}</p>
                                ))}
                              </div>
                            )}
                            <div className="col-span-2 flex items-center gap-2 pt-1">
                              <button
                                onClick={(e) => { e.stopPropagation(); setTradeTarget(o); }}
                                className="px-3 py-1.5 text-xs rounded bg-emerald-700 hover:bg-emerald-600 text-white font-mono transition-colors"
                              >
                                Paper trade
                              </button>
                            </div>
                            {Object.keys(o.details).length > 0 && (
                              <div className="col-span-2">
                                <p className="text-[#6e7681] mb-1">Details</p>
                                <pre className="text-[#8b949e] text-xs overflow-x-auto">
                                  {JSON.stringify(o.details, null, 2)}
                                </pre>
                              </div>
                            )}
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                ))}
              </tbody>
            </table>
          )}
        </Card>

        {/* Pagination */}
        {total > 50 && (
          <div className="flex items-center gap-3">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-3 py-1 text-xs bg-[#1c2128] border border-[#30363d] rounded disabled:opacity-40 text-[#e6edf3] hover:bg-[#21262d]"
            >
              ← Prev
            </button>
            <span className="text-xs text-[#6e7681]">
              Page {page} of {Math.ceil(total / 50)}
            </span>
            <button
              onClick={() => setPage((p) => p + 1)}
              disabled={page >= Math.ceil(total / 50)}
              className="px-3 py-1 text-xs bg-[#1c2128] border border-[#30363d] rounded disabled:opacity-40 text-[#e6edf3] hover:bg-[#21262d]"
            >
              Next →
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
