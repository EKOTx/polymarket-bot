import type { Metadata } from "next";

export const metadata: Metadata = { title: "Refund Policy — PolymarketIQ" };

export default function RefundPolicyPage() {
  return (
    <article className="max-w-2xl mx-auto px-4 py-16">
      <h1 className="text-2xl font-bold text-[#e6edf3] mb-2">Refund Policy</h1>
      <p className="text-xs text-[#6e7681] mb-8">Last updated: May 2025 · <span className="text-amber-400">Draft — pending legal review</span></p>

      <Section title="7-day money-back guarantee">
        If you subscribe to a paid plan for the first time and are not satisfied, you may request a
        full refund within 7 days of your first payment. This guarantee applies once per customer.
      </Section>

      <Section title="Monthly subscriptions">
        Monthly plans can be cancelled at any time. Cancellation takes effect at the end of the current
        billing period — you will retain access until that date. No partial refunds are issued for
        unused days on monthly plans beyond the 7-day guarantee window.
      </Section>

      <Section title="Annual plans">
        If annual plans are offered: cancellations within 30 days of first payment are eligible for
        a prorated refund. After 30 days, no refund is issued for annual plans.
      </Section>

      <Section title="How to request a refund">
        Contact us via the <a href="/contact" className="text-[#388bfd] hover:underline">contact form</a> with
        your account email and reason. We aim to process refunds within 5–10 business days.
        Refunds are returned to the original payment method.
      </Section>

      <Section title="Exceptions">
        Refunds will not be issued where: (a) the account has been terminated for terms violations;
        (b) abuse of the refund policy is detected; (c) the request is outside the eligible window.
      </Section>

      <Section title="Free plan">
        The free plan has no payment associated and is not subject to this policy.
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
