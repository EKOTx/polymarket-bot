"use client";

import Link from "next/link";
import { ArrowRight, TrendingUp, Shield, Zap } from "lucide-react";

const PILLS = [
  { icon: TrendingUp, label: "Edge Detection" },
  { icon: Shield, label: "Risk Analytics" },
  { icon: Zap, label: "Real-time Signals" },
];

export function Hero() {
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden pt-16">
      {/* Background grid */}
      <div
        className="absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage:
            "linear-gradient(#388bfd 1px, transparent 1px), linear-gradient(to right, #388bfd 1px, transparent 1px)",
          backgroundSize: "40px 40px",
        }}
      />
      {/* Glow */}
      <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[400px] bg-[#388bfd]/8 rounded-full blur-[120px] pointer-events-none" />

      <div className="relative z-10 max-w-4xl mx-auto px-4 text-center">
        {/* Tag */}
        <div className="inline-flex items-center gap-2 bg-[#161b22] border border-[#30363d] rounded-full px-4 py-1.5 text-xs text-[#8b949e] mb-8">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
          Analytics-only platform · Paper trading · No real funds
        </div>

        {/* Headline */}
        <h1 className="text-4xl md:text-6xl font-bold tracking-tight mb-6 leading-tight">
          <span
            style={{
              background: "linear-gradient(135deg, #e6edf3 0%, #8b949e 100%)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
              backgroundClip: "text",
            }}
          >
            Prediction Market Intelligence
          </span>
          <br />
          <span
            style={{
              background: "linear-gradient(135deg, #388bfd 0%, #a371f7 100%)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
              backgroundClip: "text",
            }}
          >
            for Serious Traders
          </span>
        </h1>

        {/* Subheadline */}
        <p className="text-lg text-[#8b949e] max-w-2xl mx-auto mb-10 leading-relaxed">
          Track Polymarket inefficiencies, vig, liquidity, external odds divergence,
          and market signals in one professional analytics dashboard.
        </p>

        {/* Pills */}
        <div className="flex flex-wrap justify-center gap-3 mb-10">
          {PILLS.map(({ icon: Icon, label }) => (
            <span
              key={label}
              className="flex items-center gap-1.5 bg-[#161b22] border border-[#30363d] rounded-full px-3 py-1 text-xs text-[#8b949e]"
            >
              <Icon className="w-3 h-3 text-[#388bfd]" />
              {label}
            </span>
          ))}
        </div>

        {/* CTAs */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link
            href="#waitlist"
            className="flex items-center gap-2 bg-[#388bfd] hover:bg-[#1f6feb] text-white px-6 py-3 rounded-md font-medium transition-colors text-sm"
          >
            Join Waitlist
            <ArrowRight className="w-4 h-4" />
          </Link>
          <Link
            href="#dashboard-preview"
            className="flex items-center gap-2 bg-[#161b22] hover:bg-[#21262d] border border-[#30363d] text-[#e6edf3] px-6 py-3 rounded-md font-medium transition-colors text-sm"
          >
            View Dashboard Preview
          </Link>
        </div>

        {/* Social proof */}
        <p className="mt-8 text-xs text-[#484f58]">
          Research tool only · Analytics and simulation · Not financial advice
        </p>
      </div>
    </section>
  );
}
