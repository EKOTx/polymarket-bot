import { TrendingUp, BarChart2, Target, BookOpen, AlertTriangle, LineChart } from "lucide-react";

const FEATURES = [
  {
    icon: TrendingUp,
    title: "Edge Detection",
    description:
      "Automatically identifies markets where odds deviate from fair value using multi-source probability models and historical calibration.",
  },
  {
    icon: BarChart2,
    title: "Vig & Spread Analysis",
    description:
      "Real-time house-edge measurement across all active markets. Filter out high-friction markets and focus on tradeable inefficiencies.",
  },
  {
    icon: Target,
    title: "Liquidity Intelligence",
    description:
      "Track bid/ask depth, market impact costs, and historical liquidity trends before sizing any position.",
  },
  {
    icon: LineChart,
    title: "Price History & Charts",
    description:
      "Full bid/mid/ask time-series for every market. Spot mean-reversion setups and track how your signals evolve over time.",
  },
  {
    icon: BookOpen,
    title: "Paper Trading Simulator",
    description:
      "Test strategies with realistic slippage and fees — no real money at risk. Build a performance track record before going live.",
  },
  {
    icon: AlertTriangle,
    title: "Signal Alerts",
    description:
      "Discord and Slack webhooks notify you the moment a high-edge opportunity is detected, with full context attached.",
  },
];

export function Features() {
  return (
    <section id="features" className="py-24 px-4">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-[#e6edf3] mb-4">
            Everything in one terminal
          </h2>
          <p className="text-[#8b949e] max-w-xl mx-auto">
            Built for analysts who want data-driven signals — not hunches.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {FEATURES.map(({ icon: Icon, title, description }) => (
            <div
              key={title}
              className="bg-[#161b22] border border-[#30363d] rounded-xl p-6 hover:border-[#388bfd]/50 transition-colors group"
            >
              <div className="w-10 h-10 rounded-lg bg-[#0d1117] border border-[#30363d] flex items-center justify-center mb-4 group-hover:border-[#388bfd]/50 transition-colors">
                <Icon className="w-5 h-5 text-[#388bfd]" />
              </div>
              <h3 className="text-sm font-semibold text-[#e6edf3] mb-2">{title}</h3>
              <p className="text-sm text-[#6e7681] leading-relaxed">{description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
