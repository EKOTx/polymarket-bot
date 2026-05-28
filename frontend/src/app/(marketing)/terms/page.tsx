import type { Metadata } from "next";

export const metadata: Metadata = { title: "Terms of Service — PolymarketIQ" };

export default function TermsPage() {
  return (
    <article className="max-w-2xl mx-auto px-4 py-16">
      <h1 className="text-2xl font-bold text-[#e6edf3] mb-2">Terms of Service</h1>
      <p className="text-xs text-[#6e7681] mb-8">Last updated: May 2025 · <span className="text-amber-400">Draft — pending legal review</span></p>

      <Section title="1. Acceptance">
        By accessing PolymarketIQ you agree to these terms. If you do not agree, do not use the platform.
      </Section>

      <Section title="2. Description of service">
        PolymarketIQ provides prediction market analytics, signal detection, and paper trading simulation.
        We do not execute real trades, hold funds, or operate as a financial broker. The platform is a
        research tool only.
      </Section>

      <Section title="3. Not financial advice">
        Nothing on this platform constitutes financial, investment, or trading advice. All signals,
        scores, and analytics are informational only. You are solely responsible for any decisions made
        based on information obtained through the platform.
      </Section>

      <Section title="4. Eligibility">
        You must be at least 18 years old to use this platform. By registering, you confirm you meet
        this requirement and that your use complies with applicable local laws.
      </Section>

      <Section title="5. Acceptable use">
        You agree not to: (a) use the platform for illegal purposes; (b) attempt to reverse-engineer
        or scrape the API beyond your plan limits; (c) share account credentials; (d) impersonate
        another user or entity.
      </Section>

      <Section title="6. Paper trading">
        Paper trades use simulated funds and do not represent real financial transactions. Results do
        not guarantee equivalent real-world outcomes. Simulated performance may differ materially from
        actual trading results.
      </Section>

      <Section title="7. Subscriptions and payments">
        Paid plans are billed monthly in advance. Cancellation takes effect at the end of the billing
        period. See our <a href="/refund-policy" className="text-[#388bfd] hover:underline">Refund Policy</a> for
        refund eligibility.
      </Section>

      <Section title="8. Termination">
        We may suspend or terminate accounts that violate these terms, without prior notice. You may
        delete your account at any time via account settings.
      </Section>

      <Section title="9. Disclaimer of warranties">
        The platform is provided &ldquo;as is&rdquo; without warranties of any kind. We do not guarantee
        uptime, accuracy of data, or fitness for any particular purpose.
      </Section>

      <Section title="10. Limitation of liability">
        To the maximum extent permitted by law, PolymarketIQ shall not be liable for any indirect,
        incidental, or consequential damages arising from use of the platform.
      </Section>

      <Section title="11. Governing law">
        These terms are governed by the laws of the jurisdiction in which PolymarketIQ is incorporated.
        Disputes shall be resolved by binding arbitration unless prohibited by local law.
      </Section>

      <Section title="12. Changes">
        We may update these terms. Material changes will be notified by email or in-app banner. Continued
        use after the effective date constitutes acceptance.
      </Section>

      <Section title="13. Contact">
        <a href="/contact" className="text-[#388bfd] hover:underline">Contact us</a> with questions.
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
