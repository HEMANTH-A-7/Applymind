import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Privacy Policy",
  description: "How ApplyMind AI collects, uses, and protects your personal data.",
  robots: { index: true, follow: true },
};

const LAST_UPDATED = "18 June 2026";
const CONTACT_EMAIL = "privacy@applymind.ai";

export default function PrivacyPage() {
  return (
    <main
      className="min-h-screen py-20 px-6"
      style={{ background: "var(--bg)", color: "var(--text)", fontFamily: "var(--font-jakarta)" }}
    >
      <div className="max-w-3xl mx-auto">

        {/* Header */}
        <Link href="/" className="inline-flex items-center gap-2 mb-12 text-xs uppercase tracking-widest transition-opacity hover:opacity-60" style={{ color: "var(--acid)" }}>
          ← Back to ApplyMind AI
        </Link>

        <div className="mb-12">
          <span className="text-xs font-bold uppercase tracking-widest px-3 py-1 rounded-full mb-4 inline-block" style={{ background: "rgba(204,255,0,0.1)", color: "var(--acid)" }}>
            Legal
          </span>
          <h1 className="text-4xl font-bold mt-3 mb-2" style={{ fontFamily: "var(--font-syne)", color: "var(--text)" }}>
            Privacy Policy
          </h1>
          <p className="text-sm" style={{ color: "var(--text-muted)" }}>Last updated: {LAST_UPDATED}</p>
        </div>

        <div className="space-y-10 text-sm leading-relaxed" style={{ color: "var(--text-muted)" }}>

          {/* 1 */}
          <Section title="1. Who We Are">
            <p>ApplyMind AI ("we", "us", "our") is an AI-powered job application automation platform. We are the data controller for personal data collected through this website and our services. Contact us at <a href={`mailto:${CONTACT_EMAIL}`} className="underline" style={{ color: "var(--acid)" }}>{CONTACT_EMAIL}</a> for any privacy-related queries.</p>
          </Section>

          {/* 2 */}
          <Section title="2. Data We Collect">
            <Table rows={[
              ["Resume / CV", "Name, email, phone, work history, skills, education", "You upload it", "To parse and optimise your job applications"],
              ["Account data", "Email address, hashed password", "Registration form", "Authentication and account management"],
              ["Job application data", "Applications submitted, company names, status, timestamps", "Automated via our agents", "Analytics and reporting to you"],
              ["Usage analytics", "Pages visited, features used, session duration", "Cookies / localStorage", "Product improvement (with your consent)"],
              ["Platform credentials", "LinkedIn/Wellfound username, password, or API tokens", "You provide them", "Saved locally in browser cookies (never in database); sent in-memory during apply"],
            ]} headers={["Data type", "What it includes", "Source", "Purpose"]} />
          </Section>

          {/* 3 */}
          <Section title="3. Legal Basis for Processing (GDPR)">
            <ul className="space-y-2 list-none pl-0">
              {[
                ["Contract", "Processing your resume and submitting applications — necessary to deliver the service you signed up for."],
                ["Consent", "Analytics and marketing cookies — only set if you click 'Accept all'."],
                ["Legitimate interests", "Security monitoring, fraud prevention, improving product reliability."],
                ["Legal obligation", "Retaining records where required by law."],
              ].map(([basis, desc]) => (
                <li key={basis} className="pl-4 border-l-2" style={{ borderColor: "var(--acid)" }}>
                  <span className="font-bold" style={{ color: "var(--text)" }}>{basis}: </span>{desc}
                </li>
              ))}
            </ul>
          </Section>

          {/* 4 */}
          <Section title="4. Third-Party Services">
            <Table rows={[
              ["Groq Inc.", "USA", "AI text generation (resume parsing, cover letters, job enrichment)", "We send resume/job text. No personally identifiable financial data."],
              ["Vercel Inc.", "USA", "Frontend hosting and CDN", "IP address, request logs (standard web hosting)."],
              ["Railway / Render", "USA", "Backend API hosting", "Application data at rest and in transit."],
              ["PostgreSQL (hosted)", "EU/USA", "Database", "All structured user data. Encrypted at rest."],
            ]} headers={["Provider", "Location", "Purpose", "Data shared"]} />
            <p className="mt-3">All third parties are bound by Data Processing Agreements (DPAs) where required under GDPR. Transfers to the USA are covered by Standard Contractual Clauses.</p>
          </Section>

          {/* 5 */}
          <Section title="5. Data Retention">
            <ul className="space-y-1 list-disc pl-5">
              <li>Resume files: deleted immediately after parsing (not stored on disk)</li>
              <li>Parsed resume JSON: retained for the lifetime of your account</li>
              <li>Application history: retained for 24 months, then auto-deleted</li>
              <li>Account data: retained until you delete your account + 30-day grace period</li>
              <li>Logs: 90 days, no PII in log output</li>
            </ul>
          </Section>

          {/* 6 */}
          <Section title="6. Your Rights (GDPR / UK GDPR)">
            <p className="mb-3">You have the right to:</p>
            <ul className="space-y-1 list-disc pl-5">
              <li><strong style={{ color: "var(--text)" }}>Access</strong> — request a copy of your personal data</li>
              <li><strong style={{ color: "var(--text)" }}>Rectification</strong> — correct inaccurate data</li>
              <li><strong style={{ color: "var(--text)" }}>Erasure</strong> — request deletion of your account and all data</li>
              <li><strong style={{ color: "var(--text)" }}>Portability</strong> — receive your data in machine-readable format</li>
              <li><strong style={{ color: "var(--text)" }}>Restriction</strong> — limit how we process your data</li>
              <li><strong style={{ color: "var(--text)" }}>Object</strong> — opt out of processing based on legitimate interests</li>
              <li><strong style={{ color: "var(--text)" }}>Withdraw consent</strong> — at any time for consent-based processing (e.g. analytics cookies)</li>
            </ul>
            <p className="mt-3">To exercise any right, email <a href={`mailto:${CONTACT_EMAIL}`} className="underline" style={{ color: "var(--acid)" }}>{CONTACT_EMAIL}</a>. We will respond within 30 days.</p>
          </Section>

          {/* 7 */}
          <Section title="7. Cookies">
            <Table rows={[
              ["applymind-cookie-consent", "localStorage", "365 days", "Records your cookie consent choices. Essential."],
              ["applymind_creds_consent", "Cookie", "30 days", "Stores your consent to store platform credentials locally. Essential."],
              ["applymind_linkedin_creds", "Cookie", "30 days", "LinkedIn credentials for auto-applying. Optional."],
              ["applymind_wellfound_creds", "Cookie", "30 days", "Wellfound credentials/tokens for auto-applying. Optional."],
              ["_ga, _gid", "Cookie", "2 years / 24h", "Google Analytics (only if you consent to analytics)."],
            ]} headers={["Name", "Storage", "Duration", "Purpose"]} />
            <p className="mt-3">You can withdraw consent for credentials and clear cookie data at any time via the "Platform Credentials" settings modal in your Job Queue panel or by clearing your browser cookies.</p>
          </Section>

          {/* 8 */}
          <Section title="8. Security">
            <ul className="space-y-1 list-disc pl-5">
              <li>All data in transit encrypted via TLS 1.3</li>
              <li>Passwords hashed with bcrypt (cost factor 12)</li>
              <li>Platform credentials are stored client-side in browser cookies only</li>
              <li>Backend API processes credentials completely in-memory (never persisted at rest)</li>
              <li>JWT tokens expire after 24 hours</li>
              <li>API rate-limited to prevent brute-force attacks</li>
              <li>No PII in server logs</li>
            </ul>
          </Section>

          {/* 9 */}
          <Section title="9. Children's Privacy">
            <p>ApplyMind AI is not directed to individuals under the age of 16. We do not knowingly collect personal data from children. If you believe we have inadvertently collected such data, contact us immediately.</p>
          </Section>

          {/* 10 */}
          <Section title="10. Changes to This Policy">
            <p>We may update this policy. When we do, we update the "Last updated" date above and, for material changes, notify you by email. Continued use of the service after changes constitutes acceptance.</p>
          </Section>

          {/* 11 */}
          <Section title="11. Contact & Complaints">
            <p>Email: <a href={`mailto:${CONTACT_EMAIL}`} className="underline" style={{ color: "var(--acid)" }}>{CONTACT_EMAIL}</a></p>
            <p className="mt-2">If you are in the EU/UK and believe we are processing your data unlawfully, you have the right to lodge a complaint with your national data protection authority (e.g. ICO in the UK, CNIL in France).</p>
          </Section>

        </div>

        {/* Footer links */}
        <div className="mt-16 pt-8 border-t flex gap-6 text-xs" style={{ borderColor: "var(--border)", color: "var(--text-muted)" }}>
          <Link href="/terms" className="hover:underline" style={{ color: "var(--acid)" }}>Terms of Service</Link>
          <Link href="/" className="hover:underline">Home</Link>
        </div>
      </div>
    </main>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section>
      <h2 className="text-base font-bold mb-3" style={{ fontFamily: "var(--font-syne)", color: "var(--text)" }}>{title}</h2>
      {children}
    </section>
  );
}

function Table({ headers, rows }: { headers: string[]; rows: string[][] }) {
  return (
    <div className="overflow-x-auto rounded-xl border" style={{ borderColor: "var(--border)" }}>
      <table className="w-full text-xs">
        <thead>
          <tr style={{ background: "var(--surface)" }}>
            {headers.map(h => (
              <th key={h} className="px-4 py-3 text-left font-bold" style={{ color: "var(--text)" }}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} style={{ borderTop: "1px solid var(--border)" }}>
              {row.map((cell, j) => (
                <td key={j} className="px-4 py-3" style={{ color: "var(--text-muted)" }}>{cell}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
