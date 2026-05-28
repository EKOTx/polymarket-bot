"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { TopBar } from "@/components/layout/TopBar";
import { Card, CardHeader } from "@/components/ui/Card";
import { useAuth } from "@/lib/auth";
import { authApi } from "@/lib/api";
import { cn } from "@/lib/utils";

const PLAN_LABELS: Record<string, { label: string; color: string; desc: string }> = {
  free:    { label: "Free",    color: "text-gray-400",  desc: "Delayed data · 10 results/scan · 3 paper positions" },
  pro:     { label: "Pro",     color: "text-blue-400",  desc: "Live data · 100 results · 10 paper positions · alerts" },
  premium: { label: "Premium", color: "text-amber-400", desc: "Live data · unlimited · 20 positions · API access" },
};

export default function SettingsPage() {
  const router = useRouter();
  const { user, logout } = useAuth();

  // Profile
  const [fullName, setFullName] = useState(user?.full_name ?? "");
  const [profileSaving, setProfileSaving] = useState(false);
  const [profileSaved, setProfileSaved] = useState(false);

  // Change password
  const [currentPw, setCurrentPw] = useState("");
  const [newPw, setNewPw] = useState("");
  const [confirmPw, setConfirmPw] = useState("");
  const [pwLoading, setPwLoading] = useState(false);
  const [pwError, setPwError] = useState("");
  const [pwSuccess, setPwSuccess] = useState(false);

  // Delete account
  const [deleteEmail, setDeleteEmail] = useState("");
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [deleteError, setDeleteError] = useState("");
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const plan = user?.plan ?? "free";
  const planInfo = PLAN_LABELS[plan] ?? PLAN_LABELS.free;

  const saveProfile = async () => {
    setProfileSaving(true);
    await authApi.updateMe(fullName);
    setProfileSaving(false);
    setProfileSaved(true);
    setTimeout(() => setProfileSaved(false), 2000);
  };

  const changePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setPwError("");
    if (newPw !== confirmPw) { setPwError("Passwords do not match"); return; }
    if (newPw.length < 8) { setPwError("Password must be at least 8 characters"); return; }
    setPwLoading(true);
    try {
      await authApi.changePassword(currentPw, newPw);
      setPwSuccess(true);
      setCurrentPw(""); setNewPw(""); setConfirmPw("");
      setTimeout(() => setPwSuccess(false), 3000);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setPwError(msg ?? "Failed to change password");
    } finally {
      setPwLoading(false);
    }
  };

  const deleteAccount = async () => {
    if (deleteEmail.toLowerCase() !== user?.email?.toLowerCase()) {
      setDeleteError("Email does not match your account email");
      return;
    }
    setDeleteLoading(true);
    setDeleteError("");
    try {
      await authApi.deleteAccount(deleteEmail);
      logout();
      router.push("/");
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setDeleteError(msg ?? "Failed to delete account");
      setDeleteLoading(false);
    }
  };

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
                readOnly
                value={user?.email ?? ""}
                className="w-full bg-[#0d1117] border border-[#30363d] rounded px-3 py-2 text-sm text-[#6e7681] font-mono"
              />
            </div>
            <div>
              <label className="text-xs text-[#6e7681] block mb-1">Full name</label>
              <input
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="w-full bg-[#0d1117] border border-[#30363d] rounded px-3 py-2 text-sm text-[#e6edf3]"
                placeholder="Your name"
              />
            </div>
            <button
              onClick={saveProfile}
              disabled={profileSaving}
              className={cn(
                "px-4 py-2 text-sm rounded font-mono transition-colors",
                profileSaved
                  ? "bg-emerald-800 text-emerald-200"
                  : "bg-[#21262d] border border-[#30363d] text-[#e6edf3] hover:bg-[#30363d]"
              )}
            >
              {profileSaved ? "✓ Saved" : profileSaving ? "Saving…" : "Save changes"}
            </button>
          </div>
        </Card>

        {/* Change password */}
        <Card>
          <CardHeader title="Change Password" />
          {pwSuccess ? (
            <p className="text-sm text-emerald-400">✓ Password changed successfully.</p>
          ) : (
            <form onSubmit={changePassword} className="space-y-3">
              <div>
                <label className="text-xs text-[#6e7681] block mb-1">Current password</label>
                <input
                  type="password"
                  required
                  value={currentPw}
                  onChange={(e) => setCurrentPw(e.target.value)}
                  className="w-full bg-[#0d1117] border border-[#30363d] rounded px-3 py-2 text-sm text-[#e6edf3]"
                  autoComplete="current-password"
                />
              </div>
              <div>
                <label className="text-xs text-[#6e7681] block mb-1">New password</label>
                <input
                  type="password"
                  required
                  minLength={8}
                  value={newPw}
                  onChange={(e) => setNewPw(e.target.value)}
                  className="w-full bg-[#0d1117] border border-[#30363d] rounded px-3 py-2 text-sm text-[#e6edf3]"
                  autoComplete="new-password"
                />
              </div>
              <div>
                <label className="text-xs text-[#6e7681] block mb-1">Confirm new password</label>
                <input
                  type="password"
                  required
                  minLength={8}
                  value={confirmPw}
                  onChange={(e) => setConfirmPw(e.target.value)}
                  className="w-full bg-[#0d1117] border border-[#30363d] rounded px-3 py-2 text-sm text-[#e6edf3]"
                  autoComplete="new-password"
                />
              </div>
              {pwError && (
                <p className="text-xs text-red-400 bg-red-900/20 border border-red-800/30 rounded px-3 py-2">
                  {pwError}
                </p>
              )}
              <button
                type="submit"
                disabled={pwLoading}
                className="px-4 py-2 text-sm rounded bg-[#21262d] border border-[#30363d] text-[#e6edf3] hover:bg-[#30363d] transition-colors font-mono disabled:opacity-50"
              >
                {pwLoading ? "Updating…" : "Update password"}
              </button>
            </form>
          )}
        </Card>

        {/* Subscription */}
        <Card>
          <CardHeader title="Subscription" />
          <div className="flex items-start justify-between mb-4">
            <div>
              <p className={cn("text-lg font-semibold font-mono", planInfo.color)}>{planInfo.label}</p>
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
          <div className="space-y-2 border-t border-[#30363d] pt-4">
            {Object.entries(PLAN_LABELS).map(([key, info]) => (
              <div key={key} className="flex items-center gap-3">
                <span className={cn("w-2 h-2 rounded-full", key === plan ? "bg-emerald-400" : "bg-[#30363d]")} />
                <span className={cn("text-sm font-mono", info.color)}>{info.label}</span>
                <span className="text-xs text-[#6e7681]">{info.desc}</span>
              </div>
            ))}
          </div>
        </Card>

        {/* Delete account */}
        <Card>
          <CardHeader title="Danger Zone" />
          {!showDeleteConfirm ? (
            <div>
              <p className="text-sm text-[#6e7681] mb-3">
                Permanently delete your account and all associated data. This cannot be undone.
              </p>
              <button
                onClick={() => setShowDeleteConfirm(true)}
                className="px-4 py-2 text-sm rounded border border-red-800/60 text-red-400 hover:bg-red-900/20 transition-colors font-mono"
              >
                Delete account…
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              <p className="text-sm text-red-400 font-medium">
                This will permanently delete your account, all paper trades, and portfolio history.
              </p>
              <p className="text-xs text-[#6e7681]">
                Type your email address <span className="text-[#e6edf3] font-mono">{user?.email}</span> to confirm:
              </p>
              <input
                type="email"
                value={deleteEmail}
                onChange={(e) => setDeleteEmail(e.target.value)}
                placeholder={user?.email ?? ""}
                className="w-full bg-[#0d1117] border border-red-800/60 rounded px-3 py-2 text-sm text-[#e6edf3] font-mono"
              />
              {deleteError && (
                <p className="text-xs text-red-400">{deleteError}</p>
              )}
              <div className="flex gap-3">
                <button
                  onClick={() => { setShowDeleteConfirm(false); setDeleteEmail(""); setDeleteError(""); }}
                  className="px-4 py-2 text-sm rounded border border-[#30363d] text-[#6e7681] hover:text-[#e6edf3] transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={deleteAccount}
                  disabled={deleteLoading}
                  className="px-4 py-2 text-sm rounded bg-red-800 hover:bg-red-700 disabled:opacity-50 text-white transition-colors font-mono"
                >
                  {deleteLoading ? "Deleting…" : "Delete my account"}
                </button>
              </div>
            </div>
          )}
        </Card>

      </div>
    </div>
  );
}
