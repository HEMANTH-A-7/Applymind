"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import type { Metadata } from "next";

export default function LoginPage() {
  const { user, loading, signIn, signUp, signInWithGoogle } = useAuth();
  const router = useRouter();

  const [mode, setMode]         = useState<"login" | "signup">("login");
  const [name, setName]         = useState("");
  const [email, setEmail]       = useState("");
  const [password, setPassword] = useState("");
  const [error, setError]       = useState("");
  const [busy, setBusy]         = useState(false);

  // Redirect if already logged in
  useEffect(() => {
    if (!loading && user) router.push("/dashboard");
  }, [user, loading, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      if (mode === "login") {
        await signIn(email, password);
      } else {
        if (!name.trim()) { setError("Name is required"); setBusy(false); return; }
        if (password.length < 8) { setError("Password must be 8+ characters"); setBusy(false); return; }
        await signUp(email, password, name);
      }
      router.push("/dashboard");
    } catch (err: any) {
      const code = err?.code ?? "";
      if (code === "auth/user-not-found" || code === "auth/wrong-password") {
        setError("Invalid email or password");
      } else if (code === "auth/email-already-in-use") {
        setError("Account already exists — sign in instead");
      } else if (code === "auth/weak-password") {
        setError("Password must be at least 8 characters");
      } else if (code === "auth/invalid-email") {
        setError("Invalid email address");
      } else if (code === "auth/too-many-requests") {
        setError("Too many attempts — try again in a few minutes");
      } else {
        setError(err?.message ?? "Authentication failed");
      }
    } finally {
      setBusy(false);
    }
  };

  const handleGoogle = async () => {
    setError("");
    setBusy(true);
    try {
      await signInWithGoogle();
      router.push("/dashboard");
    } catch (err: any) {
      setError(err?.message ?? "Google sign-in failed");
    } finally {
      setBusy(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: "var(--bg)" }}>
        <div className="w-3 h-3 rounded-full animate-ping" style={{ background: "var(--acid)" }} />
      </div>
    );
  }

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
          {/* Tabs */}
          <div className="flex rounded-xl p-1 mb-8" style={{ background: "var(--bg-3)" }}>
            {(["login", "signup"] as const).map((m) => (
              <button
                key={m}
                onClick={() => { setMode(m); setError(""); }}
                className="flex-1 py-2.5 rounded-lg text-sm font-bold transition-all duration-200"
                style={mode === m
                  ? { background: "var(--acid)", color: "#000" }
                  : { color: "var(--text-muted)" }
                }
              >
                {m === "login" ? "Sign In" : "Create Account"}
              </button>
            ))}
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {mode === "signup" && (
              <Field label="Full Name" id="name" type="text" value={name}
                onChange={setName} placeholder="Hemanth Kumar" autoComplete="name" />
            )}
            <Field label="Email" id="email" type="email" value={email}
              onChange={setEmail} placeholder="you@example.com" autoComplete="email" />
            <Field label="Password" id="password" type="password" value={password}
              onChange={setPassword} placeholder="••••••••"
              autoComplete={mode === "login" ? "current-password" : "new-password"} />

            {/* Error */}
            {error && (
              <p className="text-xs py-2 px-3 rounded-lg border"
                style={{ color: "#FF4757", background: "rgba(255,71,87,0.08)", borderColor: "rgba(255,71,87,0.2)" }}>
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={busy}
              id={mode === "login" ? "login-btn" : "signup-btn"}
              className="w-full py-3 rounded-xl font-bold text-sm transition-all duration-200 hover:scale-[1.02] disabled:opacity-50 disabled:cursor-not-allowed"
              style={{ background: "var(--acid)", color: "#000" }}
            >
              {busy ? "Please wait…" : mode === "login" ? "Sign In →" : "Create Account →"}
            </button>
          </form>

          {/* Divider */}
          <div className="flex items-center gap-3 my-5">
            <div className="flex-1 h-px" style={{ background: "var(--border)" }} />
            <span className="text-xs" style={{ color: "var(--text-muted)" }}>or</span>
            <div className="flex-1 h-px" style={{ background: "var(--border)" }} />
          </div>

          {/* Google */}
          <button
            onClick={handleGoogle}
            disabled={busy}
            id="google-signin-btn"
            className="w-full py-3 rounded-xl font-bold text-sm border flex items-center justify-center gap-2 transition-all duration-200 hover:scale-[1.02] disabled:opacity-50"
            style={{ borderColor: "var(--border)", color: "var(--text)", background: "var(--surface)" }}
          >
            <svg className="w-4 h-4" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            Continue with Google
          </button>

          {mode === "login" && (
            <p className="text-center mt-4 text-xs" style={{ color: "var(--text-muted)" }}>
              <a href="/forgot-password" className="underline underline-offset-2 hover:opacity-80" style={{ color: "var(--acid)" }}>
                Forgot password?
              </a>
            </p>
          )}
        </div>

        {/* Legal */}
        <p className="text-center text-[11px] mt-4" style={{ color: "var(--text-muted)" }}>
          By continuing, you agree to our{" "}
          <a href="/terms" className="underline" style={{ color: "var(--acid)" }}>Terms</a>
          {" "}and{" "}
          <a href="/privacy" className="underline" style={{ color: "var(--acid)" }}>Privacy Policy</a>.
        </p>
      </div>
    </main>
  );
}

function Field({
  label, id, type, value, onChange, placeholder, autoComplete,
}: {
  label: string; id: string; type: string; value: string;
  onChange: (v: string) => void; placeholder: string; autoComplete?: string;
}) {
  return (
    <div>
      <label htmlFor={id} className="block text-xs font-bold mb-1.5 uppercase tracking-widest"
        style={{ color: "var(--text-muted)" }}>{label}</label>
      <input
        id={id}
        type={type}
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        autoComplete={autoComplete}
        required
        className="w-full px-4 py-3 rounded-xl text-sm outline-none transition-all duration-200"
        style={{
          background: "var(--bg-3)",
          border: "1px solid var(--border)",
          color: "var(--text)",
        }}
        onFocus={e => (e.target.style.borderColor = "var(--acid)")}
        onBlur={e => (e.target.style.borderColor = "var(--border)")}
      />
    </div>
  );
}
