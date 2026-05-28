import { Search, Filter, FlaskConical } from "lucide-react";

const STEPS = [
  {
    step: "01",
    icon: Search,
    title: "Scanner ingests live markets",
    description:
      "Automated scanner fetches all active Polymarket markets every few minutes, capturing bid/ask/mid prices, liquidity depth, and event context.",
  },
  {
    step: "02",
    icon: Filter,
    title: "Signals are scored and ranked",
    description:
      "Each market is evaluated for vig, edge vs. external benchmarks, confidence calibration, and liquidity. Only actionable signals surface to your dashboard.",
  },
  {
    step: "03",
    icon: FlaskConical,
    title: "You test and track strategies",
    description:
      "Paper-trade signals with realistic simulation, monitor portfolio performance over time, and refine your approach before committing real capital elsewhere.",
  },
];

export function HowItWorks() {
  return (
    <section id="how-it-works" className="py-24 px-4 bg-[#161b22]/40">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-[#e6edf3] mb-4">How it works</h2>
          <p className="text-[#8b949e]">Three layers from raw market data to actionable insight.</p>
        </div>

        <div className="space-y-8">
          {STEPS.map(({ step, icon: Icon, title, description }, i) => (
            <div key={step} className="flex gap-6 group">
              {/* Step connector */}
              <div className="flex flex-col items-center">
                <div className="w-12 h-12 rounded-xl bg-[#0d1117] border border-[#30363d] flex items-center justify-center flex-shrink-0 group-hover:border-[#388bfd]/50 transition-colors">
                  <Icon className="w-5 h-5 text-[#388bfd]" />
                </div>
                {i < STEPS.length - 1 && (
                  <div className="w-px flex-1 bg-[#30363d] my-3 min-h-[32px]" />
                )}
              </div>

              {/* Content */}
              <div className="pt-2 pb-8">
                <div className="flex items-center gap-3 mb-2">
                  <span className="text-xs font-mono text-[#388bfd]">STEP {step}</span>
                </div>
                <h3 className="text-base font-semibold text-[#e6edf3] mb-2">{title}</h3>
                <p className="text-sm text-[#6e7681] leading-relaxed">{description}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
