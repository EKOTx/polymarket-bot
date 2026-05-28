import type { Metadata } from "next";

export const metadata: Metadata = { title: "Cookie Policy — PolymarketIQ" };

export default function CookiesPage() {
  return (
    <article className="max-w-2xl mx-auto px-4 py-16">
      <h1 className="text-2xl font-bold text-[#e6edf3] mb-2">Cookie Policy</h1>
      <p className="text-xs text-[#6e7681] mb-8">Last updated: May 2025 · <span className="text-amber-400">Draft — pending legal review</span></p>

      <Section title="What are cookies?">
        Cookies are small text files stored in your browser when you visit a website. We use
        localStorage for consent state and session data, plus server-set HTTP cookies for authentication.
      </Section>

      <Section title="Cookies we use">
        <table className="w-full text-xs border border-[#30363d] rounded overflow-hidden">
          <thead>
            <tr className="bg-[#161b22]">
              <th className="px-3 py-2 text-left text-[#6e7681]">Name</th>
              <th className="px-3 py-2 text-left text-[#6e7681]">Type</th>
              <th className="px-3 py-2 text-left text-[#6e7681]">Purpose</th>
              <th className="px-3 py-2 text-left text-[#6e7681]">Duration</th>
            </tr>
          </thead>
          <tbody>
            {[
              ["access_token", "Necessary", "JWT authentication token (localStorage)", "Session"],
              ["cookie_consent_v1", "Necessary", "Stores your cookie consent choice", "1 year"],
              ["_analytics", "Analytics", "Anonymous usage analytics (with consent)", "30 days"],
            ].map(([name, type, purpose, duration]) => (
              <tr key={name} className="border-t border-[#21262d]">
                <td className="px-3 py-2 font-mono text-[#388bfd]">{name}</td>
                <td className="px-3 py-2 text-[#8b949e]">{type}</td>
                <td className="px-3 py-2 text-[#8b949e]">{purpose}</td>
                <td className="px-3 py-2 text-[#8b949e]">{duration}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>

      <Section title="Necessary cookies">
        These are required for the platform to function. They enable authentication and remember your
        privacy preferences. You cannot opt out of necessary cookies without stopping use of the service.
      </Section>

      <Section title="Analytics cookies">
        With your consent, we use anonymised analytics to understand how users navigate the platform
        and improve features. No personally identifiable data is included in analytics events.
        You can withdraw consent at any time by clicking &ldquo;Necessary only&rdquo; in the cookie banner.
      </Section>

      <Section title="Third-party cookies">
        We do not currently embed third-party advertising or social media widgets that set their own cookies.
        If we integrate a payment processor on the billing page, that provider may set cookies subject
        to their own privacy policy.
      </Section>

      <Section title="Managing cookies">
        You can clear cookies and localStorage data at any time via your browser&rsquo;s developer tools or
        privacy settings. Clearing the authentication token will log you out.
      </Section>

      <Section title="Contact">
        Questions: <a href="/contact" className="text-[#388bfd] hover:underline">contact form</a>
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
