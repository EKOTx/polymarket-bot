import type { Metadata } from "next";

export const metadata: Metadata = { title: "Disclaimer — PolymarketIQ" };

export default function DisclaimerPage() {
  return (
    <article className="max-w-2xl mx-auto px-4 py-16">
      <h1 className="text-2xl font-bold text-[#e6edf3] mb-2">Disclaimer</h1>
      <p className="text-xs text-[#6e7681] mb-8">Last updated: May 2025 · <span className="text-amber-400">Draft — pending legal review</span></p>

      <div className="bg-amber-900/20 border border-amber-700/40 rounded-lg px-5 py-4 mb-8">
        <p className="text-sm text-amber-300 font-medium">
          Nothing on this platform constitutes financial, investment, legal, or trading advice.
        </p>
      </div>

      <Section title="No financial advice">
        PolymarketIQ is an analytics and research tool. All signals, scores, edges, and analytics
        are provided for informational and educational purposes only. They do not constitute
        recommendations to trade any security, prediction market contract, or other financial instrument.
      </Section>

      <Section title="No guarantee of accuracy">
        Probability estimates and edge calculations are model-derived and may be materially wrong.
        Markets can be irrational, illiquid, or subject to manipulation. We make no warranty that
        any signal or metric is accurate, timely, or suitable for any purpose.
      </Section>

      <Section title="Past performance">
        Historical signal performance, backtested metrics, and simulated paper trade results do not
        guarantee equivalent results if applied in real trading. Past performance is not indicative
        of future results.
      </Section>

      <Section title="Regulatory notice">
        PolymarketIQ does not hold any financial services license and is not regulated by any
        financial authority. We do not execute real trades, hold user funds, or operate as a broker,
        exchange, or investment adviser.
      </Section>

      <Section title="Jurisdiction">
        Access to and use of prediction markets may be restricted or illegal in your jurisdiction.
        It is your sole responsibility to determine whether your use of this research platform and
        any real-money activity on third-party prediction markets complies with applicable laws.
      </Section>

      <Section title="User responsibility">
        Any trading or investment decisions you make are entirely your own. PolymarketIQ expressly
        disclaims all liability for any losses or damages arising from decisions made based on
        information obtained from this platform.
      </Section>
    </article>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="mb-8">
      <h2 className="text-base font-semibold text-[#e6edf3] mb-3">{title}</h2>
      <div className="text-sm text-[#8b949e] leading-relaxed space-y-2">{children}</div>
    </div>
  );
}
