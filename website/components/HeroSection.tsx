"use client";
import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import dynamic from "next/dynamic";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

const HeroCanvas = dynamic(() => import("./HeroCanvas"), { ssr: false });

if (typeof window !== "undefined") {
  gsap.registerPlugin(ScrollTrigger);
}

export default function HeroSection() {
  const router = useRouter();
  const titleRef = useRef<HTMLDivElement>(null);
  const subtitleRef = useRef<HTMLParagraphElement>(null);
  const ctaRef = useRef<HTMLDivElement>(null);
  const scrollIndicatorRef = useRef<HTMLDivElement>(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    const ctx = gsap.context(() => {
      // Stagger headline entrance
      gsap.fromTo(
        ".hero-word",
        { y: 120, opacity: 0, skewY: 8 },
        {
          y: 0,
          opacity: 1,
          skewY: 0,
          duration: 1.2,
          stagger: 0.08,
          ease: "expo.out",
          delay: 0.3,
        }
      );

      // Subtitle
      gsap.fromTo(
        subtitleRef.current,
        { y: 30, opacity: 0 },
        { y: 0, opacity: 1, duration: 1, ease: "expo.out", delay: 0.9 }
      );

      // CTA
      gsap.fromTo(
        ctaRef.current,
        { y: 20, opacity: 0 },
        { y: 0, opacity: 1, duration: 1, ease: "expo.out", delay: 1.1 }
      );

      // Scroll indicator bounce
      gsap.to(scrollIndicatorRef.current, {
        y: 10,
        repeat: -1,
        yoyo: true,
        duration: 1.2,
        ease: "power2.inOut",
      });
    });
    return () => ctx.revert();
  }, []);

  const words = ["YOUR", "DREAM", "JOB."];
  const words2 = ["AUTOMATED."];

  return (
    <section className="relative min-h-screen bg-void overflow-hidden flex flex-col" id="hero">
      {/* Noise + gradient overlays */}
      <div className="absolute inset-0 bg-gradient-to-b from-void via-transparent to-void pointer-events-none z-10" />
      <div className="absolute bottom-0 left-0 right-0 h-64 bg-gradient-to-t from-void to-transparent z-10 pointer-events-none" />

      {/* Acid glow orbs */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 rounded-full bg-acid-glow animate-drift opacity-30 pointer-events-none blur-3xl" />
      <div className="absolute bottom-1/3 right-1/4 w-80 h-80 rounded-full bg-magenta-glow animate-drift pointer-events-none blur-3xl" style={{ animationDelay: "5s" }} />

      {/* 3D Canvas — full viewport */}
      <div className={`absolute inset-0 z-0${mounted ? " pointer-events-none" : ""}`}>
        <HeroCanvas />
      </div>

      {/* Marquee top bar */}
      <div className="relative z-20 marquee-wrapper border-b border-acid/10 py-2 bg-black/40 backdrop-blur-sm">
        <div className="marquee-content font-grotesk text-[10px] tracking-[0.4em] uppercase text-acid/40">
          {Array(8).fill("APPLYMIND AI · AUTOMATED JOB INTELLIGENCE · GROQ POWERED · 9-AGENT SYSTEM · ATS OPTIMIZED · ").join("")}
        </div>
      </div>

      {/* Navbar */}
      <nav className="relative z-20 flex items-center justify-between px-8 py-6">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-acid flex items-center justify-center">
            <span className="font-syne font-black text-void text-sm">AM</span>
          </div>
          <span className="font-syne font-bold text-chrome tracking-wider text-sm uppercase">ApplyMind AI</span>
        </div>
        <div className="hidden md:flex items-center gap-8">
          {["How It Works", "Dashboard", "Pricing"].map((item) => (
            <a key={item} href={item === "Dashboard" ? "/dashboard" : `#${item.toLowerCase().replace(/ /g, "-")}`}
              className="font-grotesk text-xs tracking-widest text-chrome/50 hover:text-acid uppercase transition-colors duration-300">
              {item}
            </a>
          ))}
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => router.push("/dashboard")}
            className="acid-btn px-6 py-2 rounded-full font-grotesk text-xs tracking-widest uppercase"
          >
            <span>Get Started</span>
          </button>
        </div>
      </nav>

      {/* Hero content */}
      <div className="relative z-20 flex-1 flex flex-col justify-center px-8 md:px-16 max-w-7xl mx-auto w-full pb-20">
        {/* Eyebrow */}
        <div className="flex items-center gap-3 mb-8">
          <div className="w-2 h-2 rounded-full bg-acid animate-pulse" />
          <span className="font-grotesk text-xs tracking-[0.4em] text-acid uppercase">9-Agent AI · Automated · ATS-Optimized</span>
        </div>

        {/* Main headline */}
        <div ref={titleRef} className="overflow-hidden">
          {/* Line 1 */}
          <div className="flex flex-wrap gap-x-6 mb-2">
            {words.map((word, i) => (
              <span
                key={i}
                className="hero-word font-syne font-black text-[clamp(4rem,12vw,11rem)] uppercase leading-none tracking-tight chrome-text glitch-text"
                data-text={word}
              >
                {word}
              </span>
            ))}
          </div>
          {/* Line 2 */}
          <div className="flex flex-wrap gap-x-6">
            {words2.map((word, i) => (
              <span
                key={i}
                className="hero-word font-syne font-black text-[clamp(4rem,12vw,11rem)] uppercase leading-none tracking-tight acid-text"
                data-text={word}
              >
                {word}
              </span>
            ))}
          </div>
        </div>

        {/* Subtitle */}
        <p ref={subtitleRef} className="font-jakarta text-lg md:text-xl text-chrome/50 mt-8 max-w-xl leading-relaxed">
          Apply to <span className="text-acid font-bold">200 jobs per week</span> with per-job ATS-optimized resumes.
          9 specialized AI agents working 24/7 so you don't have to.
        </p>

        {/* CTAs */}
        <div ref={ctaRef} className="flex flex-wrap items-center gap-4 mt-10">
          <button
            id="hero-cta-primary"
            onClick={() => router.push("/dashboard")}
            className="chrome-btn px-10 py-4 rounded-full font-grotesk font-bold text-sm tracking-widest uppercase shadow-chrome">
            START AUTOMATING →
          </button>
          <button
            id="hero-cta-secondary"
            className="acid-btn px-10 py-4 rounded-full font-grotesk font-bold text-sm tracking-widest uppercase">
            <span>WATCH DEMO</span>
          </button>
        </div>

        {/* Feature pills */}
        <div className="flex flex-wrap gap-3 mt-8">
          {[
            { label: "LinkedIn Easy Apply", color: "#CCFF00" },
            { label: "Indeed Auto-Submit", color: "#00F0FF" },
            { label: "ATS Score >80%", color: "#FF00FF" },
            { label: "Groq AI Powered", color: "#E0E0E0" },
          ].map((pill) => (
            <div key={pill.label}
              className="flex items-center gap-2 px-4 py-2 rounded-full border glass-panel"
              style={{ borderColor: `${pill.color}22` }}>
              <div className="w-1.5 h-1.5 rounded-full" style={{ background: pill.color }} />
              <span className="font-grotesk text-xs text-chrome/50">{pill.label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Scroll indicator */}
      <div ref={scrollIndicatorRef} className="relative z-20 flex flex-col items-center pb-8">
        <span className="font-grotesk text-[10px] tracking-[0.4em] text-chrome/30 uppercase mb-2">Scroll</span>
        <div className="w-[1px] h-12 bg-gradient-to-b from-acid to-transparent" />
      </div>

      {/* Bottom marquee */}
      <div className="relative z-20 marquee-wrapper border-t border-white/5 py-2 bg-black/40 backdrop-blur-sm">
        <div className="marquee-content font-grotesk text-[10px] tracking-[0.4em] uppercase text-chrome/20"
          style={{ animationDirection: "reverse" }}>
          {Array(8).fill("LINKEDIN · INDEED · WELLFOUND · GLASSDOOR · GITHUB JOBS · EMAIL APPLY · SELENIUM · PLAYWRIGHT · ").join("")}
        </div>
      </div>
    </section>
  );
}
