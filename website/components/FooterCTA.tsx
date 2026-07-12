"use client";
import { useRef, useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Canvas, useFrame } from "@react-three/fiber";
import * as THREE from "three";

function TerrainFooter() {
  const geo = useRef<THREE.PlaneGeometry>(null!);
  useFrame((state) => {
    if (geo.current) {
      const pos = geo.current.attributes.position;
      const t = state.clock.elapsedTime;
      for (let i = 0; i < pos.count; i++) {
        const x = pos.getX(i);
        const y = pos.getY(i);
        pos.setZ(i, Math.sin(x * 0.8 + t * 0.6) * 0.4 + Math.cos(y * 0.6 + t * 0.4) * 0.25);
      }
      pos.needsUpdate = true;
      geo.current.computeVertexNormals();
    }
  });
  return (
    <mesh rotation={[-Math.PI / 2.2, 0, 0]} position={[0, -1.5, 0]}>
      <planeGeometry ref={geo} args={[25, 25, 50, 50]} />
      <meshStandardMaterial color="#050505" wireframe emissive="#CCFF00" emissiveIntensity={0.08} />
    </mesh>
  );
}

export default function FooterCTA() {
  const [hovered, setHovered] = useState(false);
  const [particles, setParticles] = useState<{ id: number; x: number; y: number; color: string }[]>([]);
  const router = useRouter();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const triggerParticles = () => {
    const colors = ["#CCFF00", "#FF00FF", "#00F0FF", "#FFFFFF"];
    const newParticles = Array.from({ length: 30 }, (_, i) => ({
      id: Date.now() + i,
      x: 50 + (Math.random() - 0.5) * 40,
      y: 50 + (Math.random() - 0.5) * 40,
      color: colors[Math.floor(Math.random() * colors.length)],
    }));
    setParticles(newParticles);
    setTimeout(() => setParticles([]), 1200);
  };

  return (
    <section className="relative min-h-screen bg-void overflow-hidden flex flex-col" id="footer">
      {/* Terrain canvas */}
      <div className={`absolute inset-0${mounted ? " pointer-events-none" : ""}`}>
        <Canvas camera={{ position: [0, 3, 10], fov: 65 }}>
          <ambientLight intensity={0.05} />
          <pointLight position={[0, 5, 5]} intensity={0.8} color="#CCFF00" />
          <pointLight position={[-5, 3, 3]} intensity={0.3} color="#FF00FF" />
          <TerrainFooter />
        </Canvas>
      </div>

      {/* Gradient overlay */}
      <div className="absolute inset-0 bg-gradient-to-b from-void via-void/60 to-void pointer-events-none" />

      {/* Content */}
      <div className="relative z-10 flex-1 flex flex-col items-center justify-center text-center px-8 py-24">
        {/* Tag */}
        <div className="flex items-center gap-2 mb-10">
          <div className="h-[1px] w-16 bg-acid/40" />
          <span className="font-grotesk text-xs tracking-[0.4em] text-acid uppercase">// Start Today</span>
          <div className="h-[1px] w-16 bg-acid/40" />
        </div>

        {/* Big headline */}
        <h2 className="font-syne font-black text-[clamp(3rem,10vw,9rem)] uppercase leading-none mb-4">
          <span className="chrome-text glitch-text" data-text="STOP">STOP</span>
        </h2>
        <h2 className="font-syne font-black text-[clamp(3rem,10vw,9rem)] uppercase leading-none mb-4">
          <span className="outline-acid">APPLYING</span>
        </h2>
        <h2 className="font-syne font-black text-[clamp(3rem,10vw,9rem)] uppercase leading-none mb-12">
          <span className="acid-text">MANUALLY.</span>
        </h2>

        <p className="font-jakarta text-lg text-chrome/40 max-w-lg mb-12 leading-relaxed">
          Join thousands who've reclaimed their time.
          Let 9 AI agents handle the grind while you prepare for interviews.
        </p>

        {/* Particle burst CTA */}
        <div className="relative">
          {/* Burst particles */}
          {particles.map((p) => (
            <div
              key={p.id}
              className="absolute w-2 h-2 rounded-full pointer-events-none animate-ping"
              style={{
                left: `${p.x}%`,
                top: `${p.y}%`,
                background: p.color,
                boxShadow: `0 0 8px ${p.color}`,
                transform: `translate(-50%, -50%)`,
                animationDuration: "0.8s",
              }}
            />
          ))}

          <button
            id="footer-cta-btn"
            className="relative chrome-btn px-16 py-6 rounded-full font-syne font-black text-lg tracking-widest uppercase shadow-chrome"
            onMouseEnter={() => setHovered(true)}
            onMouseLeave={() => setHovered(false)}
            onClick={() => { triggerParticles(); setTimeout(() => router.push("/dashboard"), 400); }}
          >
            GET STARTED FREE
            <span className="ml-3 text-acid">→</span>
          </button>
        </div>

        {/* Social proof */}
        <div className="flex items-center gap-6 mt-12 text-chrome/20 font-grotesk text-xs">
          <span>No credit card required</span>
          <span className="w-1 h-1 rounded-full bg-chrome/20" />
          <span>Cancel anytime</span>
          <span className="w-1 h-1 rounded-full bg-chrome/20" />
          <span>GDPR compliant</span>
        </div>
      </div>

      {/* Footer links */}
      <div className="relative z-10 border-t border-white/5 px-8 py-8">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-6 h-6 rounded bg-acid flex items-center justify-center">
              <span className="font-syne font-black text-void text-xs">AM</span>
            </div>
            <span className="font-syne font-bold text-chrome/60 text-sm">ApplyMind AI</span>
          </div>
          <div className="flex items-center gap-8">
            <a href="/privacy" className="font-grotesk text-xs text-chrome/30 hover:text-acid transition-colors duration-300 tracking-widest uppercase">Privacy</a>
            <a href="/terms" className="font-grotesk text-xs text-chrome/30 hover:text-acid transition-colors duration-300 tracking-widest uppercase">Terms</a>
            <a href="https://github.com/HEMANTH-A-7" target="_blank" rel="noopener noreferrer" className="font-grotesk text-xs text-chrome/30 hover:text-acid transition-colors duration-300 tracking-widest uppercase">GitHub</a>
          </div>
          <p className="font-grotesk text-xs text-chrome/20">
            Built by <a href="https://github.com/HEMANTH-A-7" className="text-acid hover:underline">Hemanth Kumar</a> · 2026
          </p>
        </div>
      </div>
    </section>
  );
}
