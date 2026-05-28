"use client";

import { useEffect, useState } from "react";
import { TopBar } from "@/components/layout/TopBar";
import { Card, CardHeader } from "@/components/ui/Card";
import { alertsApi, AlertConfig, AlertTestResult } from "@/lib/api";
import { cn } from "@/lib/utils";

function StatusDot({ ok }: { ok: boolean }) {
  return (
    <span
      className={cn(
        "inline-block w-2 h-2 rounded-full",
        ok ? "bg-emerald-400" : "bg-[#30363d]"
      )}
    />
  );
}

function TestBadge({ result }: { result: boolean | null }) {
  if (result === null) return <span className="text-[#6e7681]">—</span>;
  return result ? (
    <span className="text-emerald-400">✓ sent</span>
  ) : (
    <span className="text-red-400">✗ failed</span>
  );
}

export default function AlertsPage() {
  const [config, setConfig] = useState<AlertConfig | null>(null);
  const [testResult, setTestResult] = useState<AlertTestResult | null>(null);
  const [testing, setTesting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    alertsApi.config().then(setConfig).catch(() => setError("Failed to load alert config"));
  }, []);

  const sendTest = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const r = await alertsApi.test();
      setTestResult(r);
    } catch {
      setError("Test request failed");
    } finally {
      setTesting(false);
    }
  };

  const noneConfigured = config && !config.discord_configured && !config.slack_configured;

  return (
    <div>
      <TopBar title="Alerts" />
      <div className="p-6 space-y-6 max-w-2xl">

        {/* Webhook status */}
        <Card>
          <CardHeader
            title="Webhook Status"
            subtitle="Configure webhook URLs in .env to enable alerts"
          />
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <StatusDot ok={config?.discord_configured ?? false} />
                <span className="text-sm text-[#e6edf3]">Discord</span>
              </div>
              <span className={cn("text-xs font-mono", config?.discord_configured ? "text-emerald-400" : "text-[#6e7681]")}>
                {config?.discord_configured ? "configured" : "not set"}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <StatusDot ok={config?.slack_configured ?? false} />
                <span className="text-sm text-[#e6edf3]">Slack</span>
              </div>
              <span className={cn("text-xs font-mono", config?.slack_configured ? "text-emerald-400" : "text-[#6e7681]")}>
                {config?.slack_configured ? "configured" : "not set"}
              </span>
            </div>
          </div>

          {noneConfigured && (
            <div className="mt-4 p-3 bg-amber-900/20 border border-amber-800/40 rounded text-xs text-amber-400 space-y-1">
              <p className="font-semibold">No webhooks configured</p>
              <p className="font-mono text-amber-500">DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...</p>
              <p className="font-mono text-amber-500">SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...</p>
            </div>
          )}
        </Card>

        {/* Thresholds */}
        <Card>
          <CardHeader title="Alert Thresholds" subtitle="Read from .env" />
          {config ? (
            <div className="space-y-2">
              {[
                { label: "Min edge to alert", value: `${config.min_edge_pct}%` },
                { label: "Cooldown between same alert", value: `${config.cooldown_minutes} min` },
                { label: "Daily digest (UTC hour)", value: `${config.digest_hour}:00` },
              ].map(({ label, value }) => (
                <div key={label} className="flex items-center justify-between text-sm">
                  <span className="text-[#6e7681]">{label}</span>
                  <span className="font-mono text-[#e6edf3]">{value}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-[#6e7681]">Loading…</p>
          )}
        </Card>

        {/* Alert types */}
        <Card>
          <CardHeader title="What Triggers Alerts" />
          <div className="space-y-2 text-sm">
            {[
              { label: "VALUE signal", desc: `Edge ≥ ${config?.min_edge_pct ?? 3}%` },
              { label: "TOURNAMENT_ARB detected", desc: "Any confirmed arb" },
              { label: "Paper trade closed", desc: "Win or loss" },
              { label: "Daily digest", desc: `First scan after ${config?.digest_hour ?? 8}:00 UTC` },
            ].map(({ label, desc }) => (
              <div key={label} className="flex items-center justify-between">
                <span className="text-[#e6edf3]">{label}</span>
                <span className="text-xs text-[#6e7681]">{desc}</span>
              </div>
            ))}
          </div>
        </Card>

        {/* Test */}
        <Card>
          <CardHeader title="Test Alerts" subtitle="Sends a test message to all configured webhooks" />
          <div className="flex items-center gap-4">
            <button
              onClick={sendTest}
              disabled={testing || noneConfigured === true}
              className={cn(
                "px-4 py-2 text-sm rounded font-mono transition-colors",
                noneConfigured
                  ? "bg-[#1c2128] text-[#6e7681] cursor-not-allowed"
                  : "bg-[#21262d] border border-[#30363d] text-[#e6edf3] hover:bg-[#30363d]"
              )}
            >
              {testing ? "Sending…" : "Send test alert"}
            </button>

            {testResult && (
              <div className="flex items-center gap-4 text-xs font-mono">
                <span className="text-[#6e7681]">Discord:</span>
                <TestBadge result={testResult.discord} />
                <span className="text-[#6e7681]">Slack:</span>
                <TestBadge result={testResult.slack} />
              </div>
            )}
          </div>

          {error && (
            <p className="mt-3 text-xs text-red-400">{error}</p>
          )}
        </Card>

      </div>
    </div>
  );
}
