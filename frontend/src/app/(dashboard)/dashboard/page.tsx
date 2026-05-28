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
import { Badge } from "@/components/ui/Badge";
import {
  opportunitiesApi,
  tradesApi,
  Opportunity,
  Portfolio,
  PortfolioHistory,
} from "@/lib/api";
import { useScannerStore } from "@/lib/scannerStore";
import { formatUsd, formatEdge, formatTs } from "@/lib/utils";

export default function DashboardPage() {
  const { refreshKey } = useScannerStore();
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [history, setHistory] = useState<PortfolioHistory[]>([]);
  const [latest, setLatest] = useState<Opportunity[]>([]);

  useEffect(() => {
    tradesApi.portfolio().then(setPortfolio).catch(console.error);
    tradesApi.portfolioHistory(100).then(setHistory).catch(console.error);
    opportunitiesApi.latest(5).then(setLatest).catch(console.error);
  }, [refreshKey]);

  const totalPnl = portfolio
    ? portfolio.realized_pnl + portfolio.unrealized_pnl
    : 0;

  return (
    <div>
      <TopBar title="Dashboard" />
      <div className="p-6 space-y-6">
        {/* KPI row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card>
            <Stat
              label="Balance"
              value={formatUsd(portfolio?.balance ?? 10000)}
              sub={`Started ${formatUsd(portfolio?.starting_balance ?? 10000)}`}
            />
          </Card>
          <Card>
            <Stat
              label="Total PnL"
              value={formatUsd(totalPnl)}
              color={totalPnl >= 0 ? "text-emerald-400" : "text-red-400"}
              sub={`Realized ${formatUsd(portfolio?.realized_pnl ?? 0)}`}
            />
          </Card>
          <Card>
            <Stat
              label="Open Positions"
              value={portfolio?.open_positions ?? 0}
              sub={`Total trades ${portfolio?.total_trades ?? 0}`}
            />
          </Card>
          <Card>
            <Stat
              label="Invested"
              value={formatUsd(portfolio?.total_invested ?? 0)}
              sub={`Unrealized ${formatUsd(portfolio?.unrealized_pnl ?? 0)}`}
              color={(portfolio?.unrealized_pnl ?? 0) >= 0 ? "text-emerald-400" : "text-red-400"}
            />
          </Card>
        </div>

        {/* Portfolio chart */}
        {history.length > 0 && (
          <Card>
            <CardHeader title="Portfolio Balance" />
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={history}>
                <defs>
                  <linearGradient id="balGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3fb950" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#3fb950" stopOpacity={0} />
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
                  stroke="#3fb950"
                  strokeWidth={1.5}
                  fill="url(#balGrad)"
                  dot={false}
                />
              </AreaChart>
            </ResponsiveContainer>
          </Card>
        )}

        {/* Latest opportunities */}
        <Card>
          <CardHeader title="Latest Opportunities" subtitle="From most recent scan" />
          {latest.length === 0 ? (
            <p className="text-sm text-[#6e7681]">No opportunities yet.</p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Type</th>
                  <th>Market</th>
                  <th>Edge</th>
                  <th>Confidence</th>
                  <th>Scanned</th>
                </tr>
              </thead>
              <tbody>
                {latest.map((o) => (
                  <tr key={o.id}>
                    <td>
                      <Badge type={o.opportunity_type}>{o.opportunity_type}</Badge>
                    </td>
                    <td className="max-w-xs truncate text-xs">{o.title}</td>
                    <td className="font-mono text-emerald-400">
                      {formatEdge(o.edge_pct)}
                    </td>
                    <td className="font-mono text-[#8b949e]">
                      {(o.confidence * 100).toFixed(0)}%
                    </td>
                    <td className="text-[#6e7681] text-xs">{formatTs(o.timestamp)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Card>
      </div>
    </div>
  );
}
