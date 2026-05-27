"use client";

import { useState } from "react";
import { TopBar } from "@/components/layout/TopBar";
import { Card, CardHeader } from "@/components/ui/Card";
import { useAuth } from "@/lib/auth";
import { authApi } from "@/lib/api";
import { cn } from "@/lib/utils";

const PLAN_LABELS: Record<string, { label: string; color: string; desc: string }> = {
  free: { label: "Free", color: "text-gray-400", desc: "Delayed data, 10 results/scan" },
  pro: { label: "Pro", color: "text-blue-400", desc: "Live data, 100 results, all fields" },
  premium: { label: "Premium", color: "text-amber-400", desc: "Live + strategy internals, priority support" },
};

export default function SettingsPage() {
  const { user } = useAuth();
  const [fullName, setFullName] = useState(user?.full_name ?? "");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const save = async () => {
    setSaving(true);
    await authApi.updateMe(fullName);
    setSaving(false);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const plan = user?.plan ?? "free";
  const planInfo = PLAN_LABELS[plan] ?? PLAN_LABELS.free;

  return (
    <div>
      <TopBar title="Settings" />
      <div className="p-6 space-y-6 max-w-xl">
        {/* Profile */}
        <Card>
          <CardHeader title="Profile" />
          <div className="space-y-4">
            <div>
              <label className="text-xs text-[#6e7681] block mb-1">Email</label>
              <input
                type="text"
                readOnly
                value={user?.email ?? ""}
                className="w-full bg-[#0d1117] border border-[#30363d] rounded px-3 py-2 text-sm text-[#6e7681] font-mono"
              />
            </div>
            <div>
              <label className="text-xs text-[#6e7681] block mb-1">Full name</label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="w-full bg-[#0d1117] border border-[#30363d] rounded px-3 py-2 text-sm text-[#e6edf3]"
                placeholder="Your name"
              />
            </div>
            <button
              onClick={save}
              disabled={saving}
              className={cn(
                "px-4 py-2 text-sm rounded font-mono transition-colors",
                saved
                  ? "bg-emerald-800 text-emerald-200"
                  : "bg-[#21262d] border border-[#30363d] text-[#e6edf3] hover:bg-[#30363d]"
              )}
            >
              {saved ? "✓ Saved" : saving ? "Saving…" : "Save changes"}
            </button>
          </div>
        </Card>

        {/* Plan */}
        <Card>
          <CardHeader title="Subscription" />
          <div className="flex items-start justify-between">
            <div>
              <p className={cn("text-lg font-semibold font-mono", planInfo.color)}>
                {planInfo.label}
              </p>
              <p className="text-sm text-[#6e7681] mt-0.5">{planInfo.desc}</p>
            </div>
            {plan === "free" && (
              <button className="px-4 py-2 text-sm rounded bg-blue-700 hover:bg-blue-600 text-white transition-colors">
                Upgrade → Pro
              </button>
            )}
            {plan === "pro" && (
              <button className="px-4 py-2 text-sm rounded bg-amber-700 hover:bg-amber-600 text-white transition-colors">
                Upgrade → Premium
              </button>
            )}
          </div>

          <div className="mt-4 space-y-2 border-t border-[#30363d] pt-4">
            {Object.entries(PLAN_LABELS).map(([key, info]) => (
              <div key={key} className="flex items-center gap-3">
                <span
                  className={cn(
                    "w-2 h-2 rounded-full",
                    key === plan ? "bg-emerald-400" : "bg-[#30363d]"
                  )}
                />
                <span className={cn("text-sm font-mono", info.color)}>{info.label}</span>
                <span className="text-xs text-[#6e7681]">{info.desc}</span>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
