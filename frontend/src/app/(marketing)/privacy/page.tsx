import type { Metadata } from "next";

export const metadata: Metadata = { title: "Privacy Policy — PolymarketIQ" };

export default function PrivacyPage() {
  return (
    <article className="max-w-2xl mx-auto px-4 py-16 prose-legal">
      <h1 className="text-2xl font-bold text-[#e6edf3] mb-2">Privacy Policy</h1>
      <p className="text-xs text-[#6e7681] mb-8">Last updated: May 2025 · <span className="text-amber-400">Draft — pending legal review</span></p>

      <Section title="1. Who we are">
        PolymarketIQ (&ldquo;we&rdquo;, &ldquo;our&rdquo;, &ldquo;the platform&rdquo;) is an analytics service providing
        prediction market research tools. We do not execute real trades or hold user funds.
      </Section>

      <Section title="2. Data we collect">
        <ul>
          <li><strong>Account data:</strong> email address, hashed password, display name.</li>
          <li><strong>Usage data:</strong> pages visited, features used, paper trades placed (server-side logs).</li>
          <li><strong>Alert configuration:</strong> Discord/Slack webhook URLs you provide (stored encrypted).</li>
          <li><strong>Cookies:</strong> session cookie (necessary), optional analytics cookie (consent required).</li>
        </ul>
        We do not collect payment card numbers directly — billing is handled by a third-party processor.
      </Section>

      <Section title="3. Legal basis (GDPR)">
        <ul>
          <li><strong>Contract performance:</strong> processing account data to deliver the service.</li>
          <li><strong>Legitimate interest:</strong> security logging, fraud prevention.</li>
          <li><strong>Consent:</strong> marketing emails, analytics cookies — opt-in only.</li>
        </ul>
      </Section>

      <Section title="4. How we use your data">
        <ul>
          <li>Authenticate you and maintain your session.</li>
          <li>Deliver scanner results, alerts, and paper trade records.</li>
          <li>Send service emails (password reset, waitlist confirmation).</li>
          <li>Send marketing emails <em>only</em> if you opted in.</li>
          <li>Improve the platform using aggregated, anonymised analytics.</li>
        </ul>
      </Section>

      <Section title="5. Data sharing">
        We do not sell or rent your personal data. We may share it with:
        <ul>
          <li>Hosting infrastructure providers (server-side only, no marketing access).</li>
          <li>Payment processors (only billing-relevant data).</li>
          <li>Law enforcement where required by law.</li>
        </ul>
      </Section>

      <Section title="6. Data retention">
        Account data is retained while your account is active and for 30 days after deletion request.
        Scanner logs are retained for 90 days. Anonymised aggregate data may be retained indefinitely.
      </Section>

      <Section title="7. Your rights (GDPR/CCPA)">
        You have the right to: access, rectify, erase, restrict, or port your data; withdraw consent at
        any time; lodge a complaint with your national data protection authority.
        Contact us at the email below to exercise these rights.
      </Section>

      <Section title="8. Cookies">
        See our <a href="/cookies" className="text-[#388bfd] hover:underline">Cookie Policy</a> for full details.
      </Section>

      <Section title="9. Security">
        Passwords are hashed with bcrypt. Webhook URLs are stored encrypted. TLS enforced in transit.
        See our <a href="/security" className="text-[#388bfd] hover:underline">Security page</a>.
      </Section>

      <Section title="10. Contact">
        Questions about this policy: <a href="/contact" className="text-[#388bfd] hover:underline">contact form</a> or
        privacy@polymarketiq.com
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
