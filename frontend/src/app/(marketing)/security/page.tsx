import type { Metadata } from "next";
import { Shield, Lock, Eye, AlertTriangle } from "lucide-react";

export const metadata: Metadata = { title: "Security — PolymarketIQ" };

const PRACTICES = [
  {
    icon: Lock,
    title: "Passwords hashed with bcrypt",
    description: "We never store plaintext passwords. All passwords use bcrypt with a work factor of 12.",
  },
  {
    icon: Shield,
    title: "TLS in transit",
    description: "All communication between your browser and our servers is encrypted via TLS 1.2+.",
  },
  {
    icon: Eye,
    title: "Minimal data collection",
    description: "We collect only the data required to run the service. We do not sell data.",
  },
  {
    icon: AlertTriangle,
    title: "Webhook URLs encrypted at rest",
    description: "Discord and Slack webhook URLs are stored encrypted — not readable by staff.",
  },
];

export default function SecurityPage() {
  return (
    <article className="max-w-2xl mx-auto px-4 py-16">
      <h1 className="text-2xl font-bold text-[#e6edf3] mb-2">Security</h1>
      <p className="text-xs text-[#6e7681] mb-8">Last updated: May 2025</p>

      <div className="grid sm:grid-cols-2 gap-4 mb-12">
        {PRACTICES.map(({ icon: Icon, title, description }) => (
          <div key={title} className="bg-[#161b22] border border-[#30363d] rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <Icon className="w-4 h-4 text-[#388bfd]" />
              <p className="text-sm font-medium text-[#e6edf3]">{title}</p>
            </div>
            <p className="text-xs text-[#6e7681] leading-relaxed">{description}</p>
          </div>
        ))}
      </div>

      <Section title="Authentication">
        We use JWT (JSON Web Tokens) with short expiry for session management. Tokens are stored in
        browser localStorage. We recommend using a unique, strong password and a password manager.
      </Section>

      <Section title="Infrastructure">
        The platform is hosted on reputable cloud infrastructure with automated security patching,
        network-level firewall rules, and isolated database access.
      </Section>

      <Section title="Dependencies">
        We regularly audit and update third-party dependencies to address known vulnerabilities.
        Backend API uses FastAPI (Python) with SQLAlchemy ORM to prevent SQL injection.
      </Section>

      <Section title="Responsible disclosure">
        If you discover a security vulnerability, please report it responsibly before public disclosure.
        Contact us via the <a href="/contact" className="text-[#388bfd] hover:underline">contact form</a> with
        subject &ldquo;Security Disclosure&rdquo;. We will acknowledge within 48 hours and coordinate a fix.
        We do not currently offer a bug bounty programme but will credit researchers with consent.
      </Section>

      <Section title="Scope of this document">
        This page describes our current practices as of the date above. Security is an ongoing process —
        we continuously review and improve our posture.
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
