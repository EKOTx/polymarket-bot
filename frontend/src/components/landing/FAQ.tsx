"use client";

import { useState } from "react";
import { ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";

const FAQS = [
  {
    q: "Does this platform place real trades?",
    a: "No. PolymarketIQ is a research and analytics tool only. All trading functionality is paper trading (simulation) with no real money involved. We do not connect to any trading accounts or wallets.",
  },
  {
    q: "What markets does the scanner cover?",
    a: "The scanner covers all active Polymarket markets — political events, crypto, macroeconomics, sports, science, and more. New markets are detected automatically as they are listed.",
  },
  {
    q: "How is 'edge' calculated?",
    a: "Edge is the difference between our fair-value estimate and the current market mid price. Fair value is derived from external reference probabilities (polls, forecasting aggregators, implied odds) calibrated against historical market accuracy.",
  },
  {
    q: "Is my data shared with anyone?",
    a: "No. Your account data, paper trades, and alert configurations are private and never shared with or sold to third parties. See our Privacy Policy for full details.",
  },
  {
    q: "What is the refund policy?",
    a: "Paid plans can be cancelled anytime. We offer a 7-day money-back guarantee on first payments if the platform does not meet your expectations. See Refund Policy for details.",
  },
  {
    q: "Is this financial advice?",
    a: "No. All signals, scores, and analytics are informational only and do not constitute financial or investment advice. Past performance of simulated trades does not guarantee future real-world results. Always do your own research.",
  },
];

export function FAQ() {
  const [open, setOpen] = useState<number | null>(null);

  return (
    <section id="faq" className="py-24 px-4 bg-[#161b22]/40">
      <div className="max-w-2xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold text-[#e6edf3] mb-4">
            Frequently asked questions
          </h2>
        </div>

        <div className="space-y-2">
          {FAQS.map((faq, i) => (
            <div
              key={i}
              className="border border-[#30363d] rounded-lg overflow-hidden"
            >
              <button
                className="w-full text-left px-5 py-4 flex items-center justify-between gap-4 hover:bg-[#161b22] transition-colors"
                onClick={() => setOpen(open === i ? null : i)}
                aria-expanded={open === i}
              >
                <span className="text-sm font-medium text-[#e6edf3]">{faq.q}</span>
                <ChevronDown
                  className={cn(
                    "w-4 h-4 text-[#6e7681] flex-shrink-0 transition-transform duration-200",
                    open === i && "rotate-180"
                  )}
                />
              </button>
              {open === i && (
                <div className="px-5 pb-4 text-sm text-[#8b949e] leading-relaxed border-t border-[#21262d] pt-3">
                  {faq.a}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
