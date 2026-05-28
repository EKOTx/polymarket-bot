import Link from "next/link";
import { Check } from "lucide-react";

const PLANS = [
  {
    name: "Free",
    price: "$0",
    period: "forever",
    description: "Explore the platform with limited access.",
    cta: "Get started",
    ctaHref: "/register",
    highlight: false,
    features: [
      "Up to 50 opportunities per scan",
      "Daily scanner (1× per day)",
      "Basic edge & vig metrics",
      "7-day price history",
      "Paper trading (5 open positions)",
      "Community support",
    ],
  },
  {
    name: "Pro",
    price: "$29",
    period: "per month",
    description: "Full scanner access for active analysts.",
    cta: "Join Waitlist",
    ctaHref: "#waitlist",
    highlight: true,
    features: [
      "Unlimited opportunities",
      "Real-time scanner (every 10 min)",
      "All signal types incl. arbitrage",
      "Full price history & charts",
      "Paper trading (unlimited)",
      "Discord & Slack alerts",
      "CSV export",
      "Priority support",
    ],
  },
  {
    name: "Premium",
    price: "$99",
    period: "per month",
    description: "For teams and serious quantitative researchers.",
    cta: "Join Waitlist",
    ctaHref: "#waitlist",
    highlight: false,
    features: [
      "Everything in Pro",
      "API access (REST)",
      "Custom alert webhooks",
      "Portfolio analytics & benchmarks",
      "Multi-user team access (up to 5)",
      "Data retention 1 year+",
      "Dedicated support",
      "Early access to new signals",
    ],
  },
];

export function Pricing() {
  return (
    <section id="pricing" className="py-24 px-4">
      <div className="max-w-5xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-[#e6edf3] mb-4">Simple pricing</h2>
          <p className="text-[#8b949e] max-w-lg mx-auto">
            Start free. Upgrade when you need more signal depth or automation.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          {PLANS.map((plan) => (
            <div
              key={plan.name}
              className={`relative rounded-xl border p-6 flex flex-col ${
                plan.highlight
                  ? "bg-[#161b22] border-[#388bfd]/60 shadow-lg shadow-[#388bfd]/10"
                  : "bg-[#161b22] border-[#30363d]"
              }`}
            >
              {plan.highlight && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                  <span className="bg-[#388bfd] text-white text-[10px] font-semibold px-3 py-1 rounded-full tracking-wide">
                    MOST POPULAR
                  </span>
                </div>
              )}

              <div className="mb-6">
                <p className="text-xs font-semibold text-[#6e7681] uppercase tracking-widest mb-2">
                  {plan.name}
                </p>
                <div className="flex items-end gap-2 mb-2">
                  <span className="text-3xl font-bold text-[#e6edf3]">{plan.price}</span>
                  <span className="text-sm text-[#6e7681] mb-1">{plan.period}</span>
                </div>
                <p className="text-xs text-[#6e7681]">{plan.description}</p>
              </div>

              <ul className="space-y-2.5 flex-1 mb-6">
                {plan.features.map((f) => (
                  <li key={f} className="flex items-start gap-2 text-xs text-[#8b949e]">
                    <Check className="w-3.5 h-3.5 text-emerald-400 mt-0.5 flex-shrink-0" />
                    {f}
                  </li>
                ))}
              </ul>

              <Link
                href={plan.ctaHref}
                className={`block text-center py-2.5 rounded-md text-sm font-medium transition-colors ${
                  plan.highlight
                    ? "bg-[#388bfd] hover:bg-[#1f6feb] text-white"
                    : "bg-[#21262d] hover:bg-[#30363d] text-[#e6edf3] border border-[#30363d]"
                }`}
              >
                {plan.cta}
              </Link>
            </div>
          ))}
        </div>

        <p className="text-center text-xs text-[#484f58] mt-8">
          All plans are analytics-only. No real trading executed on this platform.
        </p>
      </div>
    </section>
  );
}
