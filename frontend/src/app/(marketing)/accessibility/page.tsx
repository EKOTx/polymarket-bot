import type { Metadata } from "next";

export const metadata: Metadata = { title: "Accessibility — PolymarketIQ" };

export default function AccessibilityPage() {
  return (
    <article className="max-w-2xl mx-auto px-4 py-16">
      <h1 className="text-2xl font-bold text-[#e6edf3] mb-2">Accessibility Statement</h1>
      <p className="text-xs text-[#6e7681] mb-8">Last updated: May 2025</p>

      <Section title="Our commitment">
        PolymarketIQ is committed to making the platform accessible to all users, including those
        with disabilities. We aim to conform to WCAG 2.1 Level AA guidelines.
      </Section>

      <Section title="Current status">
        We are an early-stage product. Current accessibility features include:
        <ul>
          <li>Semantic HTML with appropriate landmark roles</li>
          <li>Keyboard navigable interface</li>
          <li>ARIA labels on interactive elements</li>
          <li>Sufficient colour contrast in our dark theme (4.5:1 minimum)</li>
          <li>Focus indicators on all interactive elements</li>
          <li>No content that flashes more than 3 times per second</li>
        </ul>
      </Section>

      <Section title="Known limitations">
        Some data tables and charts may have limited screen-reader support. We are actively working
        to improve these areas. Complex data visualisations include text alternatives where possible.
      </Section>

      <Section title="Assistive technology support">
        The platform has been tested with:
        <ul>
          <li>VoiceOver (macOS / iOS)</li>
          <li>Keyboard-only navigation (Chrome, Firefox, Safari)</li>
        </ul>
        We aim to expand testing to include NVDA and JAWS.
      </Section>

      <Section title="Feedback and contact">
        If you encounter an accessibility barrier, please contact us via our{" "}
        <a href="/contact" className="text-[#388bfd] hover:underline">contact form</a>. We aim to
        respond within 5 business days and resolve confirmed barriers within 30 days.
      </Section>

      <Section title="Enforcement">
        If you are in the EU and are not satisfied with our response, you may contact your national
        enforcement body or the relevant supervisory authority under the European Accessibility Act.
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
