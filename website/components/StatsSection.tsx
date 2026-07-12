"use client";
import { useEffect, useRef, useState } from "react";

const STATS = [
  { value: 10000, suffix: "+", label: "Applications Sent", sublabel: "This month alone", color: "#CCFF00" },
  { value: 18, suffix: "%", label: "Response Rate", sublabel: "vs 3% industry avg", color: "#00F0FF" },
  { value: 15, suffix: "hrs", label: "Saved Per Week", sublabel: "Per user, every week", color: "#FF00FF" },
];

function useCountUp(target: number, duration: number = 2000, start: boolean = false) {
  const [count, setCount] = useState(0);
  useEffect(() => {
    if (!start) return;
    const startTime = performance.now();
    const animate = (now: number) => {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // Ease out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setCount(Math.floor(eased * target));
      if (progress < 1) requestAnimationFrame(animate);
    };
    requestAnimationFrame(animate);
  }, [target, duration, start]);
  return count;
}

function StatCard({ stat, index, isVisible }: { stat: typeof STATS[0]; index: number; isVisible: boolean }) {
  const count = useCountUp(stat.value, 2000 + index * 300, isVisible);
  const [hovered, setHovered] = useState(false);

  return (
    <div
      className={`relative glass-panel rounded-3xl p-8 transition-all duration-500 cursor-default group`}
      style={{
        transform: isVisible
          ? `translateY(${hovered ? "-8px" : "0px"}) perspective(800px) rotateX(${hovered ? "-3deg" : "0deg"})`
          : "translateY(40px)",
        opacity: isVisible ? 1 : 0,
        transitionDelay: `${index * 150}ms`,
        border: `1px solid ${stat.color}22`,
        boxShadow: hovered
          ? `0 0 40px ${stat.color}33, 0 20px 60px rgba(0,0,0,0.5), inset 0 0 30px ${stat.color}08`
          : `0 0 20px ${stat.color}11, 0 10px 30px rgba(0,0,0,0.3)`,
      }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      {/* Iridescent top border */}
      <div className="absolute top-0 left-4 right-4 h-[1px] rounded-full"
        style={{ background: `linear-gradient(90deg, transparent, ${stat.color}, transparent)` }} />

      {/* Spike decorative */}
      <div className="absolute top-4 right-4 w-3 h-3 spike"
        style={{ background: stat.color, opacity: 0.6 }} />

      {/* Number */}
      <div className="mb-2">
        <span className="font-syne font-black text-7xl md:text-8xl"
          style={{
            color: stat.color,
            textShadow: `0 0 30px ${stat.color}80, 0 0 60px ${stat.color}30`,
          }}>
          {count.toLocaleString()}
        </span>
        <span className="font-syne font-black text-5xl" style={{ color: stat.color }}>
          {stat.suffix}
        </span>
      </div>

      {/* Label */}
      <h3 className="font-syne font-bold text-xl text-chrome mb-1 uppercase tracking-wide">
        {stat.label}
      </h3>
      <p className="text-sm font-grotesk text-chrome/40">{stat.sublabel}</p>

      {/* Chromatic aberration line */}
      <div className="absolute bottom-4 left-8 right-8 h-[1px] opacity-30"
        style={{ background: `linear-gradient(90deg, transparent, ${stat.color}, transparent)` }} />
    </div>
  );
}

export default function StatsSection() {
  const ref = useRef<HTMLDivElement>(null);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) setIsVisible(true); },
      { threshold: 0.3 }
    );
    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, []);

  return (
    <section ref={ref} className="relative bg-void py-24 px-6 overflow-hidden" id="stats">
      {/* Background acid glow */}
      <div className="absolute inset-0 bg-acid-glow opacity-30 pointer-events-none" />

      {/* Marquee top */}
      <div className="marquee-wrapper border-y border-acid/20 py-3 mb-20 text-acid/40 font-grotesk text-xs tracking-[0.3em] uppercase">
        <div className="marquee-content">
          {Array(6).fill("AUTOMATE YOUR CAREER · ATS OPTIMIZED · APPLY 200 JOBS/WEEK · GROQ AI POWERED · ").join("")}
        </div>
      </div>

      <div className="max-w-6xl mx-auto">
        <div className="mb-16 text-center">
          <p className="font-grotesk text-xs tracking-[0.4em] text-acid mb-4 uppercase">// Real Numbers</p>
          <h2 className="font-syne font-black text-6xl md:text-8xl uppercase chrome-text distort-heading">
            THE RESULTS
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {STATS.map((stat, i) => (
            <StatCard key={i} stat={stat} index={i} isVisible={isVisible} />
          ))}
        </div>
      </div>

      {/* Bottom marquee */}
      <div className="marquee-wrapper border-y border-white/5 py-3 mt-20 text-chrome/20 font-grotesk text-xs tracking-[0.3em] uppercase">
        <div className="marquee-content" style={{ animationDirection: "reverse" }}>
          {Array(6).fill("LINKEDIN · INDEED · WELLFOUND · GLASSDOOR · GITHUB JOBS · EMAIL APPLY · ").join("")}
        </div>
      </div>
    </section>
  );
}
