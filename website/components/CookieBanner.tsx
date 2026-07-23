"use client";
import { useEffect, useState } from "react";

const COOKIE_KEY = "applymind-cookie-consent";

export default function CookieBanner() {
  const [visible, setVisible] = useState(false);
  const [details, setDetails] = useState(false);

  useEffect(() => {
    try {
      const saved = localStorage.getItem(COOKIE_KEY);
      if (!saved) setVisible(true);
    } catch {
      setVisible(true);
    }
  }, []);

  const accept = (all: boolean) => {
    try {
      localStorage.setItem(COOKIE_KEY, JSON.stringify({
        essential: true,
        analytics: all,
        marketing: all,
        timestamp: new Date().toISOString(),
      }));
    } catch {}
    setVisible(false);
  };

  if (!visible) return null;

  return (
    <div
      role="dialog"
      aria-label="Cookie consent"
      className="fixed bottom-0 left-0 right-0 z-[9998] p-4 md:p-6"
    >
      <div
        className="max-w-4xl mx-auto rounded-2xl border p-5 md:p-6 shadow-2xl"
        style={{
          background: "var(--bg-2)",
          borderColor: "var(--border)",
          boxShadow: "0 -4px 60px rgba(204,255,0,0.08)",
        }}
      >
        {!details ? (
          /* ── Compact view ── */
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
            <div className="flex items-start gap-3 flex-1">
              <span className="text-xl shrink-0 mt-0.5">🍪</span>
              <div>
                <p className="font-bold text-sm mb-0.5" style={{ color: "var(--text)" }}>
                  We use cookies
                </p>
                <p className="text-xs leading-relaxed" style={{ color: "var(--text-muted)" }}>
                  Essential cookies keep the app working. Analytics cookies help us improve.{" "}
                  <button
                    onClick={() => setDetails(true)}
                    className="underline underline-offset-2 hover:opacity-80 transition-opacity"
                    style={{ color: "var(--acid)" }}
                  >
                    See details
                  </button>
                  {" "}or read our{" "}
                  <a href="/privacy" className="underline underline-offset-2 hover:opacity-80" style={{ color: "var(--acid)" }}>
                    Privacy Policy
                  </a>
                  .
                </p>
              </div>
            </div>
            <div className="flex gap-2 shrink-0 w-full sm:w-auto">
              <button
                onClick={() => accept(false)}
                className="flex-1 sm:flex-none px-4 py-2 rounded-xl text-xs font-bold border transition-all hover:opacity-80"
                style={{ borderColor: "var(--border)", color: "var(--text-muted)" }}
              >
                Essential only
              </button>
              <button
                onClick={() => accept(true)}
                className="flex-1 sm:flex-none px-5 py-2 rounded-xl text-xs font-bold transition-all hover:scale-105"
                style={{ background: "var(--acid)", color: "#000" }}
              >
                Accept all
              </button>
            </div>
          </div>
        ) : (
          /* ── Detailed view ── */
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-sm" style={{ color: "var(--text)" }}>Cookie Preferences</h3>
              <button onClick={() => setDetails(false)} className="text-xs" style={{ color: "var(--text-muted)" }}>← Back</button>
            </div>
            <div className="space-y-3">
              {[
                {
                  name: "Essential",
                  desc: "Authentication, session management. Cannot be disabled.",
                  locked: true,
                },
                {
                  name: "Analytics",
                  desc: "Anonymous usage data to improve the product. No personal data shared.",
                  locked: false,
                },
                {
                  name: "Marketing",
                  desc: "Used to personalise content and measure campaign effectiveness.",
                  locked: false,
                },
              ].map((cookie) => (
                <div
                  key={cookie.name}
                  className="flex items-start justify-between gap-4 p-3 rounded-xl"
                  style={{ background: "var(--surface)", border: "1px solid var(--border)" }}
                >
                  <div>
                    <p className="text-xs font-bold mb-0.5" style={{ color: "var(--text)" }}>{cookie.name}</p>
                    <p className="text-[11px]" style={{ color: "var(--text-muted)" }}>{cookie.desc}</p>
                  </div>
                  <div
                    className="shrink-0 px-2 py-1 rounded-full text-[10px] font-bold"
                    style={cookie.locked
                      ? { background: "rgba(204,255,0,0.1)", color: "var(--acid)" }
                      : { background: "var(--bg-3)", color: "var(--text-muted)" }
                    }
                  >
                    {cookie.locked ? "Always on" : "Optional"}
                  </div>
                </div>
              ))}
            </div>
            <div className="flex gap-2 pt-1">
              <button
                onClick={() => accept(false)}
                className="flex-1 py-2.5 rounded-xl text-xs font-bold border transition-all hover:opacity-80"
                style={{ borderColor: "var(--border)", color: "var(--text-muted)" }}
              >
                Essential only
              </button>
              <button
                onClick={() => accept(true)}
                className="flex-1 py-2.5 rounded-xl text-xs font-bold transition-all hover:scale-105"
                style={{ background: "var(--acid)", color: "#000" }}
              >
                Accept all cookies
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
