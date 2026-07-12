import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Terms of Service",
  description: "Terms and conditions governing the use of ApplyMind AI.",
  robots: { index: true, follow: true },
};

const LAST_UPDATED = "18 June 2026";
const CONTACT_EMAIL = "legal@applymind.ai";

export default function TermsPage() {
  return (
    <main
      className="min-h-screen py-20 px-6"
      style={{ background: "var(--bg)", color: "var(--text)", fontFamily: "var(--font-jakarta)" }}
    >
      <div className="max-w-3xl mx-auto">

        <Link href="/" className="inline-flex items-center gap-2 mb-12 text-xs uppercase tracking-widest hover:opacity-60 transition-opacity" style={{ color: "var(--acid)" }}>
          ← Back to ApplyMind AI
        </Link>

        <div className="mb-12">
          <span className="text-xs font-bold uppercase tracking-widest px-3 py-1 rounded-full mb-4 inline-block" style={{ background: "rgba(204,255,0,0.1)", color: "var(--acid)" }}>
            Legal
          </span>
          <h1 className="text-4xl font-bold mt-3 mb-2" style={{ fontFamily: "var(--font-syne)", color: "var(--text)" }}>
            Terms of Service
          </h1>
          <p className="text-sm" style={{ color: "var(--text-muted)" }}>Last updated: {LAST_UPDATED}</p>
        </div>

        <div className="space-y-10 text-sm leading-relaxed" style={{ color: "var(--text-muted)" }}>

          <Section title="1. Acceptance of Terms">
            <p>By accessing or using ApplyMind AI ("Service"), you agree to be bound by these Terms of Service. If you do not agree, do not use the Service. These Terms apply to all visitors, users, and anyone who accesses the Service.</p>
          </Section>

          <Section title="2. Description of Service">
            <p>ApplyMind AI provides AI-powered job application automation, including resume parsing, ATS optimisation, cover letter generation, job scraping, and automated application submission to third-party job platforms. The Service uses Groq AI models and web automation tools.</p>
          </Section>

          <Section title="3. Eligibility">
            <ul className="space-y-1 list-disc pl-5">
              <li>You must be at least 16 years old to use this Service.</li>
              <li>You must provide accurate information during registration.</li>
              <li>You are responsible for maintaining the security of your account credentials.</li>
            </ul>
          </Section>

          <Section title="4. Acceptable Use">
            <p className="mb-3">You agree <strong style={{ color: "var(--text)" }}>not</strong> to:</p>
            <ul className="space-y-1 list-disc pl-5">
              <li>Use the Service to submit false, misleading, or fraudulent job applications</li>
              <li>Impersonate another person or misrepresent your qualifications</li>
              <li>Violate the terms of service of any job platform (LinkedIn, Indeed, etc.) that ApplyMind automates on your behalf</li>
              <li>Use the Service for any unlawful purpose</li>
              <li>Attempt to reverse-engineer, scrape, or abuse the ApplyMind API</li>
              <li>Resell, sublicence, or redistribute the Service without written permission</li>
            </ul>
            <div className="mt-4 p-4 rounded-xl border-l-2" style={{ borderColor: "var(--acid)", background: "rgba(204,255,0,0.04)" }}>
              <p className="text-xs font-bold mb-1" style={{ color: "var(--acid)" }}>⚠ Third-party Platform Compliance</p>
              <p>You are solely responsible for ensuring your use of ApplyMind AI complies with the terms of service of LinkedIn, Indeed, Wellfound, and any other platform we automate on your behalf. ApplyMind AI accepts no liability for account suspensions or bans resulting from automated activity.</p>
            </div>
          </Section>

          <Section title="5. Platform Credentials">
            <p>If you provide login credentials for third-party platforms (e.g. LinkedIn, Indeed), you authorise us to use those credentials solely to submit job applications on your behalf. Credentials are stored encrypted with AES-256 and are never shared with third parties or used for any other purpose. You can revoke access at any time from your dashboard settings.</p>
          </Section>

          <Section title="6. AI-Generated Content">
            <p>The Service uses AI (Groq's LLaMA models) to generate cover letters, rewrite resumes, and answer application questions. You acknowledge that:</p>
            <ul className="space-y-1 list-disc pl-5 mt-2">
              <li>AI-generated content may not always be accurate or suitable for your specific situation</li>
              <li>You are responsible for reviewing AI-generated content before it is submitted</li>
              <li>ApplyMind AI does not guarantee that AI-generated content will result in interview invitations or job offers</li>
            </ul>
          </Section>

          <Section title="7. Intellectual Property">
            <p>The ApplyMind AI platform, its design, code, branding, and technology are owned by ApplyMind AI. Your resume and profile data remain your property. By uploading content, you grant us a limited licence to process it for the purpose of delivering the Service.</p>
          </Section>

          <Section title="8. Disclaimer of Warranties">
            <p>The Service is provided <strong style={{ color: "var(--text)" }}>"as is"</strong> and <strong style={{ color: "var(--text)" }}>"as available"</strong> without any warranties of any kind, express or implied, including but not limited to warranties of merchantability, fitness for a particular purpose, or non-infringement. We do not warrant that the Service will be uninterrupted, error-free, or that job applications submitted via the Service will be successful.</p>
          </Section>

          <Section title="9. Limitation of Liability">
            <p>To the fullest extent permitted by law, ApplyMind AI shall not be liable for any indirect, incidental, special, consequential, or punitive damages, including loss of employment opportunities, account suspensions on third-party platforms, or reputational damage arising from use of the Service. Our total liability to you for any claim shall not exceed the amount you paid us in the 12 months preceding the claim.</p>
          </Section>

          <Section title="10. Data and Privacy">
            <p>Your use of the Service is also governed by our <Link href="/privacy" className="underline" style={{ color: "var(--acid)" }}>Privacy Policy</Link>, which is incorporated into these Terms by reference.</p>
          </Section>

          <Section title="11. Termination">
            <p>We reserve the right to suspend or terminate your account at our discretion if you violate these Terms. You may delete your account at any time from settings. Upon deletion, your data will be purged within 30 days in accordance with our Privacy Policy.</p>
          </Section>

          <Section title="12. Changes to Terms">
            <p>We may update these Terms. Continued use after changes constitutes acceptance. For material changes, we will notify you by email at least 14 days in advance.</p>
          </Section>

          <Section title="13. Governing Law">
            <p>These Terms shall be governed by and construed in accordance with the laws of India, without regard to conflict-of-law principles. Any disputes shall be subject to the exclusive jurisdiction of courts in Bangalore, India.</p>
          </Section>

          <Section title="14. Contact">
            <p>For legal enquiries: <a href={`mailto:${CONTACT_EMAIL}`} className="underline" style={{ color: "var(--acid)" }}>{CONTACT_EMAIL}</a></p>
          </Section>

        </div>

        <div className="mt-16 pt-8 border-t flex gap-6 text-xs" style={{ borderColor: "var(--border)", color: "var(--text-muted)" }}>
          <Link href="/privacy" className="hover:underline" style={{ color: "var(--acid)" }}>Privacy Policy</Link>
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
