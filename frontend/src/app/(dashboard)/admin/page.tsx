"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { TopBar } from "@/components/layout/TopBar";
import { Card, CardHeader } from "@/components/ui/Card";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";

type Tab = "users" | "waitlist" | "contact";

interface AdminUser {
  id: number;
  email: string;
  full_name: string | null;
  plan: string;
  is_verified: boolean;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string | null;
  last_login: string | null;
}

interface WaitlistEntry {
  id: number;
  email: string;
  marketing_consent: boolean;
  created_at: string | null;
}

interface ContactMsg {
  id: number;
  name: string;
  email: string;
  subject: string;
  message: string;
  is_read: boolean;
  created_at: string | null;
}

export default function AdminPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [tab, setTab] = useState<Tab>("users");

  const [users, setUsers] = useState<AdminUser[]>([]);
  const [waitlist, setWaitlist] = useState<WaitlistEntry[]>([]);
  const [contact, setContact] = useState<ContactMsg[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (user && !user.is_superuser) {
      router.push("/dashboard");
    }
  }, [user, router]);

  useEffect(() => {
    if (!user?.is_superuser) return;
    setLoading(true);
    setError("");
    const endpoints: Record<Tab, string> = {
      users: "/api/v1/admin/users",
      waitlist: "/api/v1/admin/waitlist",
      contact: "/api/v1/admin/contact",
    };
    api
      .get(endpoints[tab])
      .then((r) => {
        if (tab === "users") setUsers(r.data.items);
        if (tab === "waitlist") setWaitlist(r.data.items);
        if (tab === "contact") setContact(r.data.items);
      })
      .catch(() => setError("Failed to load data"))
      .finally(() => setLoading(false));
  }, [tab, user]);

  const markRead = async (id: number) => {
    await api.patch(`/api/v1/admin/contact/${id}/read`);
    setContact((prev) => prev.map((m) => (m.id === id ? { ...m, is_read: true } : m)));
  };

  const updatePlan = async (userId: number, plan: string) => {
    await api.patch(`/api/v1/admin/users/${userId}`, { plan });
    setUsers((prev) => prev.map((u) => (u.id === userId ? { ...u, plan } : u)));
  };

  if (!user?.is_superuser) {
    return null;
  }

  const TABS: { key: Tab; label: string }[] = [
    { key: "users", label: "Users" },
    { key: "waitlist", label: "Waitlist" },
    { key: "contact", label: "Contact" },
  ];

  return (
    <div>
      <TopBar title="Admin" />
      <div className="p-6 space-y-4 max-w-5xl">
        {/* Tab bar */}
        <div className="flex gap-1 border-b border-[#30363d] pb-0">
          {TABS.map((t) => (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px ${
                tab === t.key
                  ? "border-blue-400 text-blue-400"
                  : "border-transparent text-[#6e7681] hover:text-[#e6edf3]"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {error && (
          <p className="text-sm text-red-400 bg-red-900/20 border border-red-800/30 rounded px-3 py-2">
            {error}
          </p>
        )}

        {loading && <p className="text-sm text-[#6e7681]">Loading…</p>}

        {/* Users tab */}
        {tab === "users" && !loading && (
          <Card>
            <CardHeader title={`Users (${users.length})`} />
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-[#6e7681] border-b border-[#30363d]">
                    <th className="text-left py-2 pr-4">Email</th>
                    <th className="text-left py-2 pr-4">Plan</th>
                    <th className="text-left py-2 pr-4">Verified</th>
                    <th className="text-left py-2 pr-4">Active</th>
                    <th className="text-left py-2 pr-4">Joined</th>
                    <th className="text-left py-2">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((u) => (
                    <tr key={u.id} className="border-b border-[#21262d] text-[#e6edf3]">
                      <td className="py-2 pr-4 font-mono">{u.email}</td>
                      <td className="py-2 pr-4">
                        <span className={`font-mono ${u.plan === "premium" ? "text-amber-400" : u.plan === "pro" ? "text-blue-400" : "text-[#6e7681]"}`}>
                          {u.plan}
                        </span>
                      </td>
                      <td className="py-2 pr-4">{u.is_verified ? "✓" : "✗"}</td>
                      <td className="py-2 pr-4">{u.is_active ? "✓" : "✗"}</td>
                      <td className="py-2 pr-4 text-[#6e7681]">
                        {u.created_at ? new Date(u.created_at).toLocaleDateString() : "—"}
                      </td>
                      <td className="py-2">
                        <select
                          value={u.plan}
                          onChange={(e) => updatePlan(u.id, e.target.value)}
                          className="bg-[#0d1117] border border-[#30363d] rounded px-1 py-0.5 text-xs text-[#e6edf3]"
                        >
                          <option value="free">free</option>
                          <option value="pro">pro</option>
                          <option value="premium">premium</option>
                        </select>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {users.length === 0 && <p className="text-[#6e7681] text-sm py-4">No users.</p>}
            </div>
          </Card>
        )}

        {/* Waitlist tab */}
        {tab === "waitlist" && !loading && (
          <Card>
            <CardHeader title={`Waitlist (${waitlist.length})`} />
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-[#6e7681] border-b border-[#30363d]">
                    <th className="text-left py-2 pr-4">Email</th>
                    <th className="text-left py-2 pr-4">Marketing</th>
                    <th className="text-left py-2">Joined</th>
                  </tr>
                </thead>
                <tbody>
                  {waitlist.map((e) => (
                    <tr key={e.id} className="border-b border-[#21262d] text-[#e6edf3]">
                      <td className="py-2 pr-4 font-mono">{e.email}</td>
                      <td className="py-2 pr-4">{e.marketing_consent ? "✓" : "✗"}</td>
                      <td className="py-2 text-[#6e7681]">
                        {e.created_at ? new Date(e.created_at).toLocaleDateString() : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {waitlist.length === 0 && <p className="text-[#6e7681] text-sm py-4">No waitlist entries.</p>}
            </div>
          </Card>
        )}

        {/* Contact tab */}
        {tab === "contact" && !loading && (
          <div className="space-y-3">
            {contact.length === 0 && <p className="text-[#6e7681] text-sm">No messages.</p>}
            {contact.map((m) => (
              <Card key={m.id}>
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-[#e6edf3]">{m.subject}</p>
                    <p className="text-xs text-[#6e7681] mt-0.5">
                      {m.name} &lt;{m.email}&gt; ·{" "}
                      {m.created_at ? new Date(m.created_at).toLocaleDateString() : "—"}
                    </p>
                    <p className="text-sm text-[#8b949e] mt-2 whitespace-pre-wrap">{m.message}</p>
                  </div>
                  <div className="shrink-0">
                    {m.is_read ? (
                      <span className="text-xs text-[#484f58]">Read</span>
                    ) : (
                      <button
                        onClick={() => markRead(m.id)}
                        className="text-xs px-2 py-1 rounded border border-[#30363d] text-[#6e7681] hover:text-[#e6edf3] transition-colors"
                      >
                        Mark read
                      </button>
                    )}
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
