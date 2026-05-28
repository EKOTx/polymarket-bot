"use client";

const DEMO_OPPORTUNITIES = [
  { type: "VALUE", market: "Fed rate cut by Sep 2025?", edge: "+6.4%", ev: "+5.1%", conf: "82%", vig: "2.1%" },
  { type: "SPREAD", market: "Trump wins 2026 midterms?", edge: "+4.8%", ev: "+3.9%", conf: "76%", vig: "3.5%" },
  { type: "HIGH_VIG", market: "Bitcoin above $100k EOY?", edge: "+3.2%", ev: "+2.4%", conf: "68%", vig: "8.9%" },
  { type: "VALUE", market: "Ukraine ceasefire Q3 2025?", edge: "+7.1%", ev: "+6.0%", conf: "88%", vig: "1.8%" },
  { type: "SPREAD", market: "Apple WWDC AI announcement?", edge: "+2.9%", ev: "+2.1%", conf: "71%", vig: "4.2%" },
];

const TYPE_COLORS: Record<string, string> = {
  VALUE: "bg-emerald-900/40 text-emerald-400 border-emerald-800/40",
  SPREAD: "bg-blue-900/40 text-blue-400 border-blue-800/40",
  HIGH_VIG: "bg-amber-900/40 text-amber-400 border-amber-800/40",
};

const STATS = [
  { label: "Markets Scanned", value: "4,218", change: "+12%" },
  { label: "Signals Found", value: "37", change: "+5" },
  { label: "Avg Edge", value: "4.9%", change: "+0.3%" },
  { label: "Portfolio PnL", value: "$1,240", change: "+12.4%" },
];

export function DashboardPreview() {
  return (
    <section id="dashboard-preview" className="py-24 px-4">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-12">
          <div className="inline-block bg-amber-900/30 border border-amber-700/40 rounded-full px-4 py-1 text-xs text-amber-400 mb-4">
            DEMO — Simulated data for illustration only
          </div>
          <h2 className="text-3xl md:text-4xl font-bold text-[#e6edf3] mb-4">
            Professional-grade analytics
          </h2>
          <p className="text-[#8b949e] max-w-xl mx-auto">
            Everything you need to identify mispricings and build a systematic edge.
          </p>
        </div>

        {/* Fake dashboard shell */}
        <div className="bg-[#0d1117] border border-[#30363d] rounded-xl overflow-hidden shadow-2xl">
          {/* Fake title bar */}
          <div className="bg-[#161b22] border-b border-[#30363d] px-4 py-3 flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-red-500/60" />
            <div className="w-3 h-3 rounded-full bg-amber-500/60" />
            <div className="w-3 h-3 rounded-full bg-emerald-500/60" />
            <span className="ml-3 text-xs text-[#484f58] font-mono">polymarket-iq / dashboard</span>
          </div>

          {/* KPI row */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-px bg-[#30363d]">
            {STATS.map((s) => (
              <div key={s.label} className="bg-[#0d1117] px-5 py-4">
                <p className="text-xs text-[#6e7681] mb-1">{s.label}</p>
                <p className="text-xl font-semibold font-mono text-[#e6edf3]">{s.value}</p>
                <p className="text-xs text-emerald-400 font-mono mt-0.5">{s.change}</p>
              </div>
            ))}
          </div>

          {/* Opportunities table */}
          <div className="overflow-x-auto">
            <table className="w-full text-xs font-mono">
              <thead>
                <tr className="border-b border-[#30363d]">
                  {["Type", "Market", "Edge", "EV", "Confidence", "Vig"].map((h) => (
                    <th
                      key={h}
                      className="px-4 py-3 text-left text-[#6e7681] font-medium uppercase tracking-wide text-[10px]"
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {DEMO_OPPORTUNITIES.map((o, i) => (
                  <tr key={i} className="border-b border-[#21262d] hover:bg-[#161b22] transition-colors">
                    <td className="px-4 py-3">
                      <span
                        className={`px-2 py-0.5 rounded border text-[10px] font-semibold ${
                          TYPE_COLORS[o.type] ?? "bg-gray-800 text-gray-400 border-gray-700"
                        }`}
                      >
                        {o.type}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-[#c9d1d9] max-w-[200px] truncate">{o.market}</td>
                    <td className="px-4 py-3 text-emerald-400 font-semibold">{o.edge}</td>
                    <td className="px-4 py-3 text-emerald-300">{o.ev}</td>
                    <td className="px-4 py-3 text-[#8b949e]">{o.conf}</td>
                    <td className="px-4 py-3 text-amber-400">{o.vig}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="px-4 py-3 bg-[#161b22] border-t border-[#30363d] text-center">
            <p className="text-[10px] text-[#484f58]">
              Simulated data · For illustration only · Past performance does not indicate future results
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
