"use client";
import { useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { AreaChart, Area, ResponsiveContainer, Tooltip } from "recharts";

const chartData = [
  { week: "W1", apps: 50, responses: 4 },
  { week: "W2", apps: 78, responses: 9 },
  { week: "W3", apps: 120, responses: 18 },
  { week: "W4", apps: 145, responses: 24 },
  { week: "W5", apps: 180, responses: 31 },
  { week: "W6", apps: 200, responses: 38 },
];

const PLATFORMS = [
  { name: "LinkedIn", apps: 847, color: "#CCFF00" },
  { name: "Indeed", apps: 623, color: "#00F0FF" },
  { name: "Wellfound", apps: 412, color: "#FF00FF" },
  { name: "Email", apps: 189, color: "#E0E0E0" },
];

function TerrainMesh() {
  const meshRef = useRef<THREE.Mesh>(null!);
  const geometryRef = useRef<THREE.PlaneGeometry>(null!);

  useFrame((state) => {
    if (geometryRef.current) {
      const positions = geometryRef.current.attributes.position;
      const time = state.clock.elapsedTime;
      for (let i = 0; i < positions.count; i++) {
        const x = positions.getX(i);
        const y = positions.getY(i);
        const z = Math.sin(x * 0.5 + time * 0.5) * 0.3 +
          Math.cos(y * 0.4 + time * 0.3) * 0.2;
        positions.setZ(i, z);
      }
      positions.needsUpdate = true;
      geometryRef.current.computeVertexNormals();
    }
  });

  return (
    <mesh ref={meshRef} rotation={[-Math.PI / 2.5, 0, 0]} position={[0, -2, 0]}>
      <planeGeometry ref={geometryRef} args={[20, 20, 40, 40]} />
      <meshStandardMaterial
        color="#0A0A0A"
        wireframe
        emissive="#CCFF00"
        emissiveIntensity={0.1}
      />
    </mesh>
  );
}

export default function DashboardSection() {
  return (
    <section className="relative bg-onyx py-24 overflow-hidden" id="dashboard">
      {/* Terrain canvas background */}
      <div className="absolute inset-0 opacity-40">
        <Canvas camera={{ position: [0, 3, 8], fov: 60 }}>
          <ambientLight intensity={0.1} />
          <pointLight position={[0, 5, 5]} intensity={0.5} color="#CCFF00" />
          <TerrainMesh />
        </Canvas>
      </div>

      <div className="relative z-10 max-w-7xl mx-auto px-6">
        {/* Section header */}
        <div className="mb-16 text-center">
          <p className="font-grotesk text-xs tracking-[0.4em] text-acid mb-4 uppercase">// Live Dashboard</p>
          <h2 className="font-syne font-black text-6xl md:text-8xl uppercase chrome-text distort-heading">
            WATCH IT
          </h2>
          <h2 className="font-syne font-black text-6xl md:text-8xl uppercase outline-acid distort-heading -mt-4">
            WORK
          </h2>
        </div>

        {/* Dashboard mockup */}
        <div className="glass-panel rounded-3xl overflow-hidden iridescent-border transform perspective-1000 hover:rotate-y-1 transition-all duration-700"
          style={{ transform: "perspective(1000px) rotateX(3deg)" }}>
          {/* Dashboard header bar */}
          <div className="flex items-center gap-2 px-6 py-4 border-b border-white/5 bg-black/60">
            <div className="flex gap-2">
              <div className="w-3 h-3 rounded-full bg-red-500/60" />
              <div className="w-3 h-3 rounded-full bg-yellow-500/60" />
              <div className="w-3 h-3 rounded-full bg-acid/60" />
            </div>
            <span className="font-grotesk text-xs text-chrome/30 ml-4 tracking-widest">APPLYMIND.AI — COMMAND CENTER</span>
            <div className="ml-auto flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-acid animate-pulse" />
              <span className="font-grotesk text-xs text-acid">LIVE</span>
            </div>
          </div>

          {/* Dashboard content */}
          <div className="grid grid-cols-12 gap-0">
            {/* Left sidebar */}
            <div className="col-span-2 border-r border-white/5 p-4 bg-black/40 hidden md:block">
              {["Dashboard", "Applications", "Resume", "Analytics", "Settings"].map((item, i) => (
                <div key={item}
                  className={`py-3 px-3 rounded-xl mb-1 font-grotesk text-xs cursor-pointer transition-all ${i === 0 ? "bg-acid/10 text-acid border border-acid/20" : "text-chrome/30 hover:text-chrome/60"}`}>
                  {item}
                </div>
              ))}
            </div>

            {/* Main content */}
            <div className="col-span-12 md:col-span-10 p-6 bg-black/20">
              {/* Top stats row */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                {[
                  { label: "Applied Today", value: "47", color: "#CCFF00" },
                  { label: "Responses", value: "8", color: "#00F0FF" },
                  { label: "Interviews", value: "3", color: "#FF00FF" },
                  { label: "ATS Score Avg", value: "87%", color: "#E0E0E0" },
                ].map((s) => (
                  <div key={s.label} className="glass-panel rounded-2xl p-4 border border-white/5">
                    <p className="font-grotesk text-xs text-chrome/40 mb-1">{s.label}</p>
                    <p className="font-syne font-black text-3xl" style={{ color: s.color }}>{s.value}</p>
                  </div>
                ))}
              </div>

              {/* Chart + platform breakdown */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Applications chart */}
                <div className="md:col-span-2 glass-panel rounded-2xl p-4 border border-white/5">
                  <p className="font-grotesk text-xs text-chrome/40 mb-4 tracking-widest uppercase">Applications vs Responses</p>
                  <ResponsiveContainer width="100%" height={150}>
                    <AreaChart data={chartData}>
                      <defs>
                        <linearGradient id="apps" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#CCFF00" stopOpacity={0.3} />
                          <stop offset="95%" stopColor="#CCFF00" stopOpacity={0} />
                        </linearGradient>
                        <linearGradient id="responses" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#00F0FF" stopOpacity={0.3} />
                          <stop offset="95%" stopColor="#00F0FF" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <Area type="monotone" dataKey="apps" stroke="#CCFF00" fill="url(#apps)" strokeWidth={2} />
                      <Area type="monotone" dataKey="responses" stroke="#00F0FF" fill="url(#responses)" strokeWidth={2} />
                      <Tooltip
                        contentStyle={{ background: "#0A0A0A", border: "1px solid #CCFF0033", borderRadius: "8px" }}
                        labelStyle={{ color: "#CCFF00", fontSize: "10px" }}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>

                {/* Platform breakdown */}
                <div className="glass-panel rounded-2xl p-4 border border-white/5">
                  <p className="font-grotesk text-xs text-chrome/40 mb-4 tracking-widest uppercase">By Platform</p>
                  <div className="space-y-3">
                    {PLATFORMS.map((p) => (
                      <div key={p.name}>
                        <div className="flex justify-between font-grotesk text-xs mb-1">
                          <span style={{ color: p.color }}>{p.name}</span>
                          <span className="text-chrome/40">{p.apps}</span>
                        </div>
                        <div className="h-1 bg-white/5 rounded-full overflow-hidden">
                          <div className="h-full rounded-full transition-all duration-1000"
                            style={{
                              width: `${(p.apps / 847) * 100}%`,
                              background: `linear-gradient(90deg, ${p.color}, ${p.color}66)`,
                              boxShadow: `0 0 8px ${p.color}`,
                            }} />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
