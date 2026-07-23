import type { Metadata } from "next";
import { Syne, Plus_Jakarta_Sans, Space_Grotesk } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/lib/auth";
import CookieBanner from "@/components/CookieBanner";

const syne = Syne({
  subsets: ["latin"],
  weight: ["400", "600", "700", "800"],
  variable: "--font-syne",
  display: "swap",
});

const jakarta = Plus_Jakarta_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-jakarta",
  display: "swap",
});

const grotesk = Space_Grotesk({
  subsets: ["latin"],
  weight: ["300", "400", "500", "700"],
  variable: "--font-grotesk",
  display: "swap",
});

const BASE_URL = "https://applymind.ai";

export const metadata: Metadata = {
  metadataBase: new URL(BASE_URL),
  title: {
    default: "ApplyMind AI — Automated Job Application Intelligence",
    template: "%s | ApplyMind AI",
  },
  description:
    "Apply to 200 jobs per week automatically. Per-JD ATS-optimized resumes, Groq-powered cover letters, and 9-agent AI automation. Land your dream job on autopilot.",
  keywords: [
    "job application automation",
    "ATS resume optimization",
    "AI job search",
    "automated job applications",
    "resume rewriter AI",
    "Groq AI jobs",
    "job hunting automation",
    "cover letter generator",
    "job scraper",
  ],
  authors: [{ name: "ApplyMind AI" }],
  creator: "ApplyMind AI",
  publisher: "ApplyMind AI",
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
  openGraph: {
    type: "website",
    locale: "en_US",
    url: BASE_URL,
    siteName: "ApplyMind AI",
    title: "ApplyMind AI — Your Dream Job. Automated.",
    description:
      "Apply to 200 jobs/week automatically. ATS-optimized resumes, Groq AI cover letters, 9-agent automation system.",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "ApplyMind AI — Automated Job Application Intelligence",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "ApplyMind AI — Your Dream Job. Automated.",
    description:
      "Apply to 200 jobs/week automatically. ATS-optimized resumes, Groq AI cover letters.",
    images: ["/og-image.png"],
    creator: "@applymindai",
  },
  icons: {
    icon: [
      { url: "/favicon.ico" },
      { url: "/icon-16.png", sizes: "16x16", type: "image/png" },
      { url: "/icon-32.png", sizes: "32x32", type: "image/png" },
    ],
    apple: [{ url: "/apple-touch-icon.png", sizes: "180x180" }],
  },
  manifest: "/manifest.json",
  alternates: {
    canonical: BASE_URL,
  },
  verification: {
    // Add these once you have them:
    // google: "your-google-search-console-token",
    // yandex: "your-yandex-token",
    // bing: "your-bing-webmaster-token",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${syne.variable} ${jakarta.variable} ${grotesk.variable}`}>
      <head>
        {/* IndexNow key — replace with real key after submitting */}
        <meta name="indexnow-key" content="REPLACE_WITH_INDEXNOW_KEY" />
      </head>
      <body className="font-jakarta antialiased overflow-x-hidden">
        <AuthProvider>
          {children}
          <CookieBanner />
        </AuthProvider>
      </body>
    </html>
  );
}
