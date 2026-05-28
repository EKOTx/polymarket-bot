import Link from "next/link";
import { BarChart2 } from "lucide-react";

const LEGAL_LINKS = [
  { href: "/privacy", label: "Privacy Policy" },
  { href: "/terms", label: "Terms of Service" },
  { href: "/cookies", label: "Cookie Policy" },
  { href: "/disclaimer", label: "Disclaimer" },
  { href: "/accessibility", label: "Accessibility" },
  { href: "/refund-policy", label: "Refund Policy" },
  { href: "/security", label: "Security" },
  { href: "/contact", label: "Contact" },
];

const NAV_LINKS = [
  { href: "#features", label: "Features" },
  { href: "#pricing", label: "Pricing" },
  { href: "#faq", label: "FAQ" },
  { href: "/dashboard", label: "Dashboard" },
];

export function Footer() {
  const year = new Date().getFullYear();

  return (
    <footer className="border-t border-[#30363d] bg-[#0d1117]">
      <div className="max-w-6xl mx-auto px-4 py-12">
        <div className="grid md:grid-cols-3 gap-8 mb-10">
          {/* Brand */}
          <div>
            <div className="flex items-center gap-2 mb-3">
              <div className="w-6 h-6 rounded bg-[#388bfd] flex items-center justify-center">
                <BarChart2 className="w-3.5 h-3.5 text-white" />
              </div>
              <span className="text-sm font-semibold text-[#e6edf3]">
                Polymarket<span className="text-[#388bfd]">IQ</span>
              </span>
            </div>
            <p className="text-xs text-[#6e7681] leading-relaxed max-w-xs">
              Research-grade prediction market analytics. Not financial advice.
              No real trading executed.
            </p>
          </div>

          {/* Navigation */}
          <div>
            <p className="text-xs font-semibold text-[#8b949e] uppercase tracking-widest mb-4">
              Product
            </p>
            <ul className="space-y-2">
              {NAV_LINKS.map((l) => (
                <li key={l.href}>
                  <Link href={l.href} className="text-xs text-[#6e7681] hover:text-[#e6edf3] transition-colors">
                    {l.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Legal */}
          <div>
            <p className="text-xs font-semibold text-[#8b949e] uppercase tracking-widest mb-4">
              Legal
            </p>
            <ul className="space-y-2">
              {LEGAL_LINKS.map((l) => (
                <li key={l.href}>
                  <Link href={l.href} className="text-xs text-[#6e7681] hover:text-[#e6edf3] transition-colors">
                    {l.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="border-t border-[#21262d] pt-6 flex flex-col md:flex-row items-center justify-between gap-3">
          <p className="text-xs text-[#484f58]">© {year} PolymarketIQ. All rights reserved.</p>
          <p className="text-xs text-[#484f58] text-center md:text-right max-w-md">
            This platform is for informational and research purposes only. Nothing on this site
            constitutes financial, investment, or trading advice.
          </p>
        </div>
      </div>
    </footer>
  );
}
