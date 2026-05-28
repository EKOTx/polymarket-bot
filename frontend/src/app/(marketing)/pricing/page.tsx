import type { Metadata } from "next";
import { Pricing } from "@/components/landing/Pricing";

export const metadata: Metadata = { title: "Pricing — PolymarketIQ" };

export default function PricingPage() {
  return (
    <div className="min-h-screen">
      <div className="pt-8 pb-4 text-center">
        <h1 className="text-3xl font-bold text-[#e6edf3]">Pricing</h1>
        <p className="text-[#8b949e] mt-2 text-sm">Start free. Scale when you need more depth.</p>
      </div>
      <Pricing />
    </div>
  );
}
