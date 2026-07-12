"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";

export default function ForgotPasswordPage() {
  const { resetPassword } = useAuth();
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [busy, setBusy] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    setBusy(true);

    if (!email.trim()) {
      setError("Email is required");
      setBusy(false);
      return;
    }

    try {
      await resetPassword(email);
      setSuccess("A password reset link has been sent to your email.");
      setEmail("");
    } catch (err: any) {
      const code = err?.code ?? "";
      if (code === "auth/user-not-found") {
        setError("No account found with this email");
      } else if (code === "auth/invalid-email") {
        setError("Invalid email address");
      } else {
        setError(err?.message ?? "Failed to send reset link");
      }
    } finally {
      setBusy(false);
    }
  };

  return (
    <main
      className="min-h-screen flex items-center justify-center px-4 relative overflow-hidden"
      style={{ background: "var(--bg)", fontFamily: "var(--font-jakarta)" }}
    >
      {/* Background glow */}
      <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 rounded-full pointer-events-none blur-3xl opacity-20"
        style={{ background: "radial-gradient(circle, var(--acid) 0%, transparent 70%)" }} />

      <div className="relative z-10 w-full max-w-md">
        {/* Logo */}
        <a href="/" className="flex items-center gap-2 mb-8 group w-fit">
          <div className="w-8 h-8 rounded-lg flex items-center justify-center font-bold text-sm transition-transform group-hover:scale-110"
            style={{ background: "var(--acid)", color: "#000" }}>AM</div>
          <span className="font-bold text-sm tracking-wider uppercase" style={{ color: "var(--text)", fontFamily: "var(--font-syne)" }}>
            ApplyMind AI
          </span>
        </a>

        {/* Card */}
        <div className="rounded-2xl p-8 border" style={{ background: "var(--bg-2)", borderColor: "var(--border)" }}>
          <h2 className="text-xl font-bold mb-2" style={{ color: "var(--text)", fontFamily: "var(--font-syne)" }}>Reset Password</h2>
          <p className="text-xs mb-6" style={{ color: "var(--text-muted)" }}>
            Enter your email address and we'll send you a link to reset your password.
          </p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="email" className="block text-xs font-bold mb-1.5 uppercase tracking-widest"
                style={{ color: "var(--text-muted)" }}>Email</label>
              <input
                id="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="w-full px-4 py-3 rounded-xl text-sm border focus:outline-none transition-all duration-200"
                style={{
                  background: "var(--bg-3)",
                  borderColor: "var(--border)",
                  color: "var(--text)",
                }}
                onFocus={(e) => {
                  e.target.style.borderColor = "var(--acid)";
                  e.target.style.boxShadow = "0 0 8px rgba(0, 255, 102, 0.15)";
                }}
                onBlur={(e) => {
                  e.target.style.borderColor = "var(--border)";
                  e.target.style.boxShadow = "none";
                }}
              />
            </div>

            {/* Error */}
            {error && (
              <p className="text-xs py-2 px-3 rounded-lg border"
                style={{ color: "#FF4757", background: "rgba(255,71,87,0.08)", borderColor: "rgba(255,71,87,0.2)" }}>
                {error}
              </p>
            )}

            {/* Success */}
            {success && (
              <p className="text-xs py-2 px-3 rounded-lg border"
                style={{ color: "var(--acid)", background: "rgba(0,255,102,0.08)", borderColor: "rgba(0,255,102,0.2)" }}>
                {success}
              </p>
            )}

            <button
              type="submit"
              disabled={busy}
              className="w-full py-3 rounded-xl font-bold text-sm transition-all duration-200 hover:scale-[1.02] disabled:opacity-50 disabled:cursor-not-allowed"
              style={{ background: "var(--acid)", color: "#000" }}
            >
              {busy ? "Sending…" : "Send Reset Link →"}
            </button>
          </form>

          <p className="text-center mt-6 text-xs" style={{ color: "var(--text-muted)" }}>
            Remember your password?{" "}
            <a href="/login" className="underline underline-offset-2 hover:opacity-80 font-bold" style={{ color: "var(--acid)" }}>
              Sign In
            </a>
          </p>
        </div>
      </div>
    </main>
  );
}
