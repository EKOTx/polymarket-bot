"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  ComposedChart,
  Area,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { ArrowLeft, ExternalLink } from "lucide-react";
import { TopBar } from "@/components/layout/TopBar";
import { Card, CardHeader, Stat } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { marketsApi, MarketDetail, PricePoint } from "@/lib/api";
import { formatUsd, formatEdge, formatTs, cn } from "@/lib/utils";
import { useScannerStore } from "@/lib/scannerStore";

function latest(history: PricePoint[], outcome = "YES"): PricePoint | undefined {
  return [...history].reverse().find((p) => p.outcome === outcome);
}

function chartData(history: PricePoint[], outcome = "YES") {
  return history
    .filter((p) => p.outcome === outcome && p.mid != null)
    .map((p) => ({
      t: new Date(p.timestamp).getTime(),
      mid: p.mid,
      bid: p.bid,
      ask: p.ask,
    }));
}

export default function MarketDetailPage() {
  const { marketId } = useParams<{ marketId: string }>();
  const router = useRouter();
  const { refreshKey } = useScannerStore();
  const [market, setMarket] = useState<MarketDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!marketId) return;
    setLoading(true);
    marketsApi
      .detail(marketId)
      .then(setMarket)
      .catch(() => setError("Market not found"))
      .finally(() => setLoading(false));
  }, [marketId, refreshKey]);

  if (loading) {
    return (
      <div>
        <TopBar title="Market Detail" />
        <div className="p-6 text-sm text-[#6e7681]">Loading…</div>
      </div>
    );
  }

  if (error || !market) {
    return (
      <div>
        <TopBar title="Market Detail" />
        <div className="p-6 text-sm text-red-400">{error ?? "Unknown error"}</div>
      </div>
    );
  }

  const primary = latest(market.price_history, "YES");
  const cd = chartData(market.price_history, "YES");

  return (
    <div>
      <TopBar title="Market Detail" />
      <div className="p-6 space-y-6">

        {/* Header */}
        <div>
          <button
            onClick={() => router.back()}
            className="flex items-center gap-1.5 text-xs text-[#6e7681] hover:text-[#e6edf3] mb-3 transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            Back
          </button>
          <div className="flex items-start justify-between gap-4">
            <div>
              <h2 className="text-base font-semibold text-[#e6edf3] leading-snug">
                {market.question}
              </h2>
              {market.event_title && (
                <p className="text-sm text-[#6e7681] mt-0.5">{market.event_title}</p>
              )}
            </div>
            <a
              href={`https://polymarket.com/event/${market.id}`}
              target="_blank"
              rel="noopener noreferrer"
              className="shrink-0 flex items-center gap-1 text-xs text-[#388bfd] hover:underline"
            >
              Polymarket <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        </div>

        {/* KPIs */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card>
            <Stat
              label="Mid (YES)"
              value={primary?.mid != null ? primary.mid.toFixed(3) : "—"}
              sub={`Bid ${primary?.bid?.toFixed(3) ?? "—"} / Ask ${primary?.ask?.toFixed(3) ?? "—"}`}
            />
          </Card>
          <Card>
            <Stat
              label="Spread"
              value={primary?.spread != null ? formatEdge(primary.spread * 100) : "—"}
              color={
                primary?.spread != null && primary.spread < 0.03
                  ? "text-emerald-400"
                  : "text-amber-400"
              }
            />
          </Card>
          <Card>
            <Stat label="Liquidity" value={formatUsd(market.liquidity, 0)} />
          </Card>
          <Card>
            <Stat label="Volume" value={formatUsd(market.volume, 0)} />
          </Card>
        </div>

        {/* Depth */}
        {primary && (
          <div className="grid grid-cols-2 gap-4">
            <Card>
              <Stat
                label="Bid depth"
                value={primary.bid_depth_usd != null ? formatUsd(primary.bid_depth_usd, 0) : "—"}
              />
            </Card>
            <Card>
              <Stat
                label="Ask depth"
                value={primary.ask_depth_usd != null ? formatUsd(primary.ask_depth_usd, 0) : "—"}
              />
            </Card>
          </div>
        )}

        {/* Price chart */}
        {cd.length > 1 && (
          <Card>
            <CardHeader title="Price History (YES)" subtitle="Bid / mid / ask" />
            <ResponsiveContainer width="100%" height={220}>
              <ComposedChart data={cd}>
                <defs>
                  <linearGradient id="midGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#388bfd" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="#388bfd" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis
                  dataKey="t"
                  type="number"
                  scale="time"
                  domain={["auto", "auto"]}
                  tickFormatter={(t) => new Date(t).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                  tick={{ fontSize: 10, fill: "#6e7681" }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  domain={["auto", "auto"]}
                  tickFormatter={(v) => v.toFixed(2)}
                  tick={{ fontSize: 10, fill: "#6e7681" }}
                  axisLine={false}
                  tickLine={false}
                  width={42}
                />
                <Tooltip
                  contentStyle={{
                    background: "#1c2128",
                    border: "1px solid #30363d",
                    borderRadius: 4,
                    fontSize: 11,
                  }}
                  labelFormatter={(t) => new Date(t).toLocaleString()}
                  formatter={(v: number, name: string) => [v?.toFixed(4), name]}
                />
                <Legend
                  wrapperStyle={{ fontSize: 11, color: "#8b949e" }}
                  iconType="plainline"
                />
                <Area
                  type="monotone"
                  dataKey="mid"
                  stroke="#388bfd"
                  strokeWidth={1.5}
                  fill="url(#midGrad)"
                  dot={false}
                  name="mid"
                />
                <Line
                  type="monotone"
                  dataKey="bid"
                  stroke="#3fb950"
                  strokeWidth={1}
                  dot={false}
                  strokeDasharray="3 3"
                  name="bid"
                />
                <Line
                  type="monotone"
                  dataKey="ask"
                  stroke="#f85149"
                  strokeWidth={1}
                  dot={false}
                  strokeDasharray="3 3"
                  name="ask"
                />
              </ComposedChart>
            </ResponsiveContainer>
          </Card>
        )}

        {/* Recent opportunities */}
        {market.recent_opportunities.length > 0 && (
          <Card className="p-0 overflow-hidden">
            <div className="p-4 border-b border-[#30363d]">
              <span className="text-sm font-semibold text-[#e6edf3]">Recent Signals</span>
            </div>
            <table>
              <thead>
                <tr>
                  <th>Type</th>
                  <th>Edge</th>
                  <th>Confidence</th>
                  <th>EV</th>
                  <th>Scanned</th>
                </tr>
              </thead>
              <tbody>
                {market.recent_opportunities.map((o) => (
                  <tr key={o.id}>
                    <td><Badge type={o.opportunity_type}>{o.opportunity_type}</Badge></td>
                    <td className="font-mono text-emerald-400">{formatEdge(o.edge_pct)}</td>
                    <td className="font-mono text-[#8b949e]">{(o.confidence * 100).toFixed(0)}%</td>
                    <td className={cn("font-mono", o.expected_value >= 0 ? "text-emerald-400" : "text-red-400")}>
                      {formatEdge(o.expected_value)}
                    </td>
                    <td className="text-xs text-[#6e7681]">{formatTs(o.timestamp)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        )}

        {/* Trades */}
        {market.open_trades.length > 0 && (
          <Card className="p-0 overflow-hidden">
            <div className="p-4 border-b border-[#30363d]">
              <span className="text-sm font-semibold text-[#e6edf3]">Paper Trades</span>
            </div>
            <table>
              <thead>
                <tr>
                  <th>Status</th>
                  <th>Outcome</th>
                  <th>Strategy</th>
                  <th>Entry</th>
                  <th>Shares</th>
                  <th>Cost</th>
                  <th>PnL</th>
                </tr>
              </thead>
              <tbody>
                {market.open_trades.map((t) => {
                  const pnl = t.status === "OPEN" ? (t.unrealized_pnl ?? 0) : (t.realized_pnl ?? 0);
                  return (
                    <tr key={t.id}>
                      <td>
                        <span className={cn(
                          "text-xs font-mono px-1.5 py-0.5 rounded",
                          t.status === "OPEN"
                            ? "bg-blue-900/40 text-blue-300"
                            : "bg-gray-800 text-gray-400"
                        )}>
                          {t.status}
                        </span>
                      </td>
                      <td className="text-xs">{t.outcome}</td>
                      <td className="text-xs text-[#8b949e]">{t.strategy}</td>
                      <td className="font-mono text-xs">{t.entry_price.toFixed(3)}</td>
                      <td className="font-mono text-xs">{t.size_shares.toFixed(0)}</td>
                      <td className="font-mono text-xs">{formatUsd(t.cost_usd)}</td>
                      <td className={cn("font-mono text-xs font-semibold", pnl >= 0 ? "text-emerald-400" : "text-red-400")}>
                        {formatUsd(pnl)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </Card>
        )}

        {/* Meta */}
        <div className="text-xs text-[#6e7681] space-y-1">
          <p>Market ID: <span className="font-mono">{market.id}</span></p>
          <p>First seen: {formatTs(market.first_seen)} · Last updated: {formatTs(market.last_updated)}</p>
        </div>

      </div>
    </div>
  );
}
