"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";

const PLANS = [
  {
    name: "STARTER",
    price: "FREE",
    period: "",
    tagline: "Dip your toe in",
    color: "#E0E0E0",
    features: [
      { text: "5 applications/day", included: true },
      { text: "Wellfound only", included: true },
      { text: "3 resume rewrites/month", included: true },
      { text: "Basic analytics", included: true },
      { text: "AI cover letters", included: false },
      { text: "LinkedIn Easy Apply", included: false },
      { text: "CAPTCHA solver", included: false },
      { text: "A/B testing", included: false },
    ],
    cta: "START FREE",
    elevated: false,
  },
  {
    name: "PRO",
    price: "$29",
    period: "/mo",
    tagline: "The full machine",
    color: "#CCFF00",
    features: [
      { text: "50 applications/day", included: true },
      { text: "LinkedIn + Indeed + Wellfound", included: true },
      { text: "Unlimited resume rewrites", included: true },
      { text: "Full funnel analytics", included: true },
      { text: "AI cover letters", included: true },
      { text: "CAPTCHA solver included", included: true },
      { text: "A/B testing", included: false },
      { text: "Priority processing", included: false },
    ],
    cta: "GO PRO",
    elevated: true,
  },
  {
    name: "ELITE",
    price: "$99",
    period: "/mo",
    tagline: "Unfair advantage",
    color: "#00F0FF",
    features: [
      { text: "200 applications/day", included: true },
      { text: "All platforms", included: true },
      { text: "Unlimited + priority rewrites", included: true },
      { text: "Full funnel + advisor AI", included: true },
      { text: "AI cover letters", included: true },
      { text: "Dedicated CAPTCHA solver", included: true },
      { text: "A/B testing", included: true },
      { text: "Priority 4hr support", included: true },
    ],
    cta: "GO ELITE",
    elevated: false,
  },
];

export default function PricingSection() {
  const router = useRouter();
  const [billing, setBilling] = useState<"monthly" | "annual">("monthly");

  return (
    <section className="relative bg-void py-24 px-6 overflow-hidden" id="pricing">
      {/* Background */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[600px] bg-magenta-glow opacity-20 pointer-events-none" />

      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <p className="font-grotesk text-xs tracking-[0.4em] text-acid mb-4 uppercase">// Pricing</p>
          <h2 className="font-syne font-black text-6xl md:text-8xl uppercase distort-heading">
            <span className="outline-chrome">CHOOSE YOUR</span>
          </h2>
          <h2 className="font-syne font-black text-6xl md:text-8xl uppercase acid-text distort-heading -mt-4">
            WEAPON
          </h2>
        </div>

        {/* Billing toggle */}
        <div className="flex items-center justify-center gap-4 mb-16">
          <button
            onClick={() => setBilling("monthly")}
            className={`font-grotesk text-sm px-6 py-2 rounded-full border transition-all duration-300 ${billing === "monthly" ? "border-acid text-acid bg-acid/10" : "border-white/10 text-chrome/40"}`}>
            Monthly
          </button>
          <button
            onClick={() => setBilling("annual")}
            className={`font-grotesk text-sm px-6 py-2 rounded-full border transition-all duration-300 ${billing === "annual" ? "border-acid text-acid bg-acid/10" : "border-white/10 text-chrome/40"}`}>
            Annual
            <span className="ml-2 text-xs text-acid">−20%</span>
          </button>
        </div>

        {/* Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-start">
          {PLANS.map((plan, i) => (
            <div
              key={plan.name}
              className={`relative glass-panel rounded-3xl p-8 transition-all duration-500 group hover:-translate-y-2 ${plan.elevated ? "md:-translate-y-6 md:scale-105" : ""}`}
              style={{
                border: `1px solid ${plan.color}22`,
                boxShadow: plan.elevated
                  ? `0 0 60px ${plan.color}33, 0 30px 80px rgba(0,0,0,0.6), inset 0 0 40px ${plan.color}08`
                  : `0 0 20px ${plan.color}11`,
              }}>
              {/* Glow ring for elevated plan */}
              {plan.elevated && (
                <div className="absolute -inset-[1px] rounded-3xl z-[-1] animate-pulse-acid"
                  style={{ background: `linear-gradient(135deg, ${plan.color}44, transparent, ${plan.color}22)` }} />
              )}

              {/* Plan badge */}
              {plan.elevated && (
                <div className="absolute -top-4 left-1/2 -translate-x-1/2 px-4 py-1 rounded-full font-grotesk text-xs font-bold tracking-widest uppercase text-void"
                  style={{ background: plan.color }}>
                  MOST POPULAR
                </div>
              )}

              {/* Top decoration */}
              <div className="absolute top-0 left-6 right-6 h-[1px]"
                style={{ background: `linear-gradient(90deg, transparent, ${plan.color}66, transparent)` }} />

              {/* Plan name */}
              <p className="font-grotesk text-xs tracking-[0.4em] mb-2" style={{ color: plan.color }}>
                {plan.name}
              </p>
              <p className="font-jakarta text-sm text-chrome/40 mb-4">{plan.tagline}</p>

              {/* Price */}
              <div className="flex items-end gap-1 mb-8">
                <span className="font-syne font-black text-6xl" style={{ color: plan.color, textShadow: `0 0 20px ${plan.color}60` }}>
                  {billing === "annual" && plan.price !== "FREE"
                    ? `$${Math.floor(parseInt(plan.price.slice(1)) * 0.8)}`
                    : plan.price}
                </span>
                <span className="font-grotesk text-chrome/40 mb-2">{plan.period}</span>
              </div>

              {/* Features */}
              <ul className="space-y-3 mb-8">
                {plan.features.map((feature, j) => (
                  <li key={j} className={`flex items-center gap-3 font-jakarta text-sm transition-all duration-200 ${feature.included ? "text-chrome" : "text-chrome/25"}`}>
                    <span className={`w-4 h-4 flex-shrink-0 flex items-center justify-center rounded-full text-xs`}
                      style={{
                        background: feature.included ? `${plan.color}22` : "transparent",
                        border: `1px solid ${feature.included ? plan.color : "rgba(255,255,255,0.1)"}`,
                        color: feature.included ? plan.color : "rgba(255,255,255,0.2)",
                      }}>
                      {feature.included ? "✓" : "×"}
                    </span>
                    {feature.text}
                  </li>
                ))}
              </ul>

              {/* CTA */}
              <button
                className={`w-full py-4 rounded-2xl font-grotesk font-bold text-sm tracking-widest uppercase transition-all duration-300 ${plan.elevated ? "text-void" : "text-void"}`}
                onClick={() => router.push("/dashboard")}
                style={{
                  background: plan.elevated
                    ? plan.color
                    : `linear-gradient(180deg, ${plan.color}33 0%, ${plan.color}11 100%)`,
                  border: `1px solid ${plan.color}44`,
                  color: plan.elevated ? "#000" : plan.color,
                  boxShadow: `0 0 20px ${plan.color}22`,
                }}
                onMouseEnter={(e) => {
                  (e.currentTarget as HTMLButtonElement).style.boxShadow = `0 0 40px ${plan.color}66, 0 0 80px ${plan.color}22`;
                  (e.currentTarget as HTMLButtonElement).style.transform = "scale(1.02)";
                }}
                onMouseLeave={(e) => {
                  (e.currentTarget as HTMLButtonElement).style.boxShadow = `0 0 20px ${plan.color}22`;
                  (e.currentTarget as HTMLButtonElement).style.transform = "scale(1)";
                }}>
                {plan.cta} →
              </button>
            </div>
          ))}
        </div>

        {/* Disclaimer */}
        <p className="text-center font-grotesk text-xs text-chrome/20 mt-12 max-w-xl mx-auto leading-relaxed">
          By using ApplyMind AI, you accept risk of account suspension on LinkedIn/Indeed.
          Review your first 20 applications manually before enabling full automation.
        </p>
      </div>
    </section>
  );
}
