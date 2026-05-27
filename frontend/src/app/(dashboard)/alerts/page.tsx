"use client";

import { TopBar } from "@/components/layout/TopBar";
import { Card, CardHeader } from "@/components/ui/Card";

export default function AlertsPage() {
  return (
    <div>
      <TopBar title="Alerts" />
      <div className="p-6">
        <Card>
          <CardHeader
            title="Alert Rules"
            subtitle="Configure Discord / Slack webhook alerts"
          />
          <p className="text-sm text-[#6e7681]">
            Alert rule management coming soon. Configure webhook URLs in{" "}
            <code className="text-[#388bfd]">.env</code> for now:
          </p>
          <div className="mt-4 space-y-2 text-xs font-mono text-[#8b949e]">
            <p>DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...</p>
            <p>SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...</p>
            <p>ALERT_MIN_EDGE_PCT=3.0</p>
            <p>ALERT_COOLDOWN_MINUTES=60</p>
            <p>ALERT_DIGEST_HOUR=8</p>
          </div>
        </Card>
      </div>
    </div>
  );
}
