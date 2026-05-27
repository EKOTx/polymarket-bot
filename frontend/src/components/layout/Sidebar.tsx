"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BarChart3,
  TrendingUp,
  Briefcase,
  Bell,
  Settings,
  LogOut,
  Activity,
  ChevronRight,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/lib/auth";

const NAV = [
  { href: "/dashboard", label: "Dashboard", icon: BarChart3 },
  { href: "/opportunities", label: "Opportunities", icon: TrendingUp },
  { href: "/trades", label: "Paper Trades", icon: Briefcase },
  { href: "/alerts", label: "Alerts", icon: Bell },
  { href: "/settings", label: "Settings", icon: Settings },
];

const PLAN_COLORS: Record<string, string> = {
  free: "bg-gray-700 text-gray-300",
  pro: "bg-blue-900 text-blue-300",
  premium: "bg-amber-900 text-amber-300",
};

export function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  return (
    <aside className="w-56 shrink-0 flex flex-col border-r border-[#30363d] bg-[#161b22] h-screen sticky top-0">
      {/* Logo */}
      <div className="flex items-center gap-2 px-4 py-4 border-b border-[#30363d]">
        <Activity className="w-5 h-5 text-emerald-400" />
        <span className="text-sm font-semibold text-[#e6edf3] tracking-wide">
          PM Intel
        </span>
      </div>

      {/* Nav */}
      <nav className="flex-1 py-4 space-y-0.5 px-2">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || pathname.startsWith(href + "/");
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-2.5 px-3 py-2 rounded text-sm transition-colors",
                active
                  ? "bg-[#21262d] text-[#e6edf3]"
                  : "text-[#8b949e] hover:bg-[#21262d] hover:text-[#e6edf3]"
              )}
            >
              <Icon className="w-4 h-4 shrink-0" />
              {label}
              {active && (
                <ChevronRight className="w-3 h-3 ml-auto text-[#6e7681]" />
              )}
            </Link>
          );
        })}
      </nav>

      {/* User */}
      {user && (
        <div className="border-t border-[#30363d] px-3 py-3 space-y-2">
          <div className="flex items-center justify-between">
            <div className="min-w-0">
              <p className="text-xs text-[#e6edf3] truncate">
                {user.full_name ?? user.email}
              </p>
              <p className="text-xs text-[#6e7681] truncate">{user.email}</p>
            </div>
            <span
              className={cn(
                "ml-2 text-xs px-1.5 py-0.5 rounded font-mono shrink-0",
                PLAN_COLORS[user.plan] ?? PLAN_COLORS.free
              )}
            >
              {user.plan}
            </span>
          </div>
          <button
            onClick={logout}
            className="flex items-center gap-2 text-xs text-[#8b949e] hover:text-red-400 transition-colors w-full"
          >
            <LogOut className="w-3.5 h-3.5" />
            Sign out
          </button>
        </div>
      )}
    </aside>
  );
}
