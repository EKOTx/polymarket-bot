"use client";

import { useEffect, useState } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { TopBar } from "@/components/layout/TopBar";
import { Card, CardHeader, Stat } from "@/components/ui/Card";
import { CloseModal } from "@/components/trades/CloseModal";
import { tradesApi, PaperTrade, Portfolio, PortfolioHistory } from "@/lib/api";
import { useScannerStore } from "@/lib/scannerStore";
import { formatUsd, formatTs, cn } from "@/lib/utils";

export default function TradesPage() {
  const { refreshKey } = useScannerStore();
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [history, setHistory] = useState<PortfolioHistory[]>([]);
  const [trades, setTrades] = useState<PaperTrade[]>([]);
  const [filter, setFilter] = useState<"ALL" | "OPEN" | "CLOSED">("ALL");
  const [closeTarget, setCloseTarget] = useState<PaperTrade | null>(null);
  const [localKey, setLocalKey] = useState(0);

  useEffect(() => {
    tradesApi.portfolio().then(setPortfolio).catch(console.error);
    tradesApi.portfolioHistory(200).then(setHistory).catch(console.error);
    tradesApi.list({ limit: 200 }).then(setTrades).catch(console.error);
  }, [refreshKey, localKey]);

  const filtered = filter === "ALL" ? trades : trades.filter((t) => t.status === filter);
  const open = trades.filter((t) => t.status === "OPEN");
  const closed = trades.filter((t) => t.status === "CLOSED");

  const winRate =
    closed.length > 0
      ? (closed.filter((t) => (t.realized_pnl ?? 0) > 0).length / closed.length) * 100
      : null;

  return (
    <div>
      {closeTarget && (
        <CloseModal
          trade={closeTarget}
          onClose={() => setCloseTarget(null)}
          onSuccess={() => { setCloseTarget(null); setLocalKey((k) => k + 1); }}
        />
      )}
      <TopBar title="Paper Trades" />
      <div className="p-6 space-y-6">
        {/* KPIs */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card>
            <Stat label="Balance" value={formatUsd(portfolio?.balance ?? 10000)} />
          </Card>
          <Card>
            <Stat
              label="Realized PnL"
              value={formatUsd(portfolio?.realized_pnl ?? 0)}
              color={(portfolio?.realized_pnl ?? 0) >= 0 ? "text-emerald-400" : "text-red-400"}
            />
          </Card>
          <Card>
            <Stat
              label="Unrealized PnL"
              value={formatUsd(portfolio?.unrealized_pnl ?? 0)}
              color={(portfolio?.unrealized_pnl ?? 0) >= 0 ? "text-emerald-400" : "text-red-400"}
            />
          </Card>
          <Card>
            <Stat
              label="Win Rate"
              value={winRate != null ? `${winRate.toFixed(1)}%` : "—"}
              sub={`${closed.length} closed trades`}
              color={winRate != null && winRate >= 50 ? "text-emerald-400" : "text-[#e6edf3]"}
            />
          </Card>
        </div>

        {/* Balance chart */}
        {history.length > 0 && (
          <Card>
            <CardHeader title="Portfolio History" />
            <ResponsiveContainer width="100%" height={160}>
              <AreaChart data={history}>
                <defs>
                  <linearGradient id="balGrad2" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#388bfd" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#388bfd" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis
                  dataKey="timestamp"
                  tickFormatter={(t) => new Date(t).toLocaleDateString()}
                  tick={{ fontSize: 10, fill: "#6e7681" }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  tickFormatter={(v) => `$${(v / 1000).toFixed(1)}k`}
                  tick={{ fontSize: 10, fill: "#6e7681" }}
                  axisLine={false}
                  tickLine={false}
                  width={50}
                />
                <Tooltip
                  contentStyle={{
                    background: "#1c2128",
                    border: "1px solid #30363d",
                    borderRadius: 4,
                    fontSize: 12,
                  }}
                  formatter={(v: number) => [formatUsd(v), "Balance"]}
                />
                <Area
                  type="monotone"
                  dataKey="balance"
                  stroke="#388bfd"
                  strokeWidth={1.5}
                  fill="url(#balGrad2)"
                  dot={false}
                />
              </AreaChart>
            </ResponsiveContainer>
          </Card>
        )}

        {/* Trades table */}
        <Card className="p-0 overflow-hidden">
          <div className="flex items-center gap-2 p-4 border-b border-[#30363d]">
            <span className="text-sm font-semibold text-[#e6edf3]">Trades</span>
            <div className="ml-auto flex items-center gap-1">
              {(["ALL", "OPEN", "CLOSED"] as const).map((f) => (
                <button
                  key={f}
                  onClick={() => setFilter(f)}
                  className={cn(
                    "px-2.5 py-1 text-xs rounded",
                    filter === f
                      ? "bg-[#21262d] text-[#e6edf3]"
                      : "text-[#6e7681] hover:text-[#e6edf3]"
                  )}
                >
                  {f}
                  {f === "OPEN" && ` (${open.length})`}
                  {f === "CLOSED" && ` (${closed.length})`}
                </button>
              ))}
            </div>
          </div>

          {filtered.length === 0 ? (
            <p className="text-sm text-[#6e7681] p-6">No trades.</p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Status</th>
                  <th>Market</th>
                  <th>Strategy</th>
                  <th>Entry</th>
                  <th>Exit</th>
                  <th>Shares</th>
                  <th>Cost</th>
                  <th>PnL</th>
                  <th>Opened</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((t) => {
                  const pnl = t.status === "OPEN"
                    ? (t.unrealized_pnl ?? 0)
                    : (t.realized_pnl ?? 0);
                  return (
                    <tr key={t.id}>
                      <td>
                        <span
                          className={cn(
                            "text-xs font-mono px-1.5 py-0.5 rounded",
                            t.status === "OPEN"
                              ? "bg-blue-900/40 text-blue-300"
                              : "bg-gray-800 text-gray-400"
                          )}
                        >
                          {t.status}
                        </span>
                      </td>
                      <td className="max-w-xs">
                        <p className="truncate text-xs">{t.question}</p>
                        <p className="text-xs text-[#6e7681]">
                          {t.outcome} | {t.resolution && (
                            t.resolution === "YES" ? "✅ YES" : "❌ NO"
                          )}
                        </p>
                      </td>
                      <td className="text-xs text-[#8b949e]">{t.strategy}</td>
                      <td className="font-mono text-xs">{t.entry_price.toFixed(3)}</td>
                      <td className="font-mono text-xs">
                        {t.exit_price != null ? t.exit_price.toFixed(3) : "—"}
                      </td>
                      <td className="font-mono text-xs">{t.size_shares.toFixed(0)}</td>
                      <td className="font-mono text-xs">{formatUsd(t.cost_usd)}</td>
                      <td
                        className={cn(
                          "font-mono text-xs font-semibold",
                          pnl >= 0 ? "text-emerald-400" : "text-red-400"
                        )}
                      >
                        {formatUsd(pnl)}
                        <span className="text-[#6e7681] font-normal">
                          {t.status === "OPEN" ? " unrlz" : ""}
                        </span>
                      </td>
                      <td className="text-xs text-[#6e7681]">{formatTs(t.opened_at)}</td>
                      <td>
                        {t.status === "OPEN" && (
                          <button
                            onClick={() => setCloseTarget(t)}
                            className="px-2 py-1 text-xs rounded border border-red-800/60 text-red-400 hover:bg-red-900/30 transition-colors font-mono"
                          >
                            Close
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </Card>
      </div>
    </div>
  );
}
