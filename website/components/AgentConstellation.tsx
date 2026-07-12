"use client";
import { useRef, useState, useMemo, useEffect } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Html, OrbitControls } from "@react-three/drei";
import * as THREE from "three";

const AGENTS = [
  { id: 1, name: "Resume Intake", desc: "Parses master resume into structured JSON schema with skill taxonomy", color: "#CCFF00" },
  { id: 2, name: "Market Research", desc: "Scrapes job boards, salary bands, skill demand heatmaps weekly", color: "#00F0FF" },
  { id: 3, name: "Job Scraper", desc: "Scrapes LinkedIn, Indeed, Wellfound 24/7 with deduplication engine", color: "#FF00FF" },
  { id: 4, name: "Match & Score", desc: "Scores each job 0–100 via cosine similarity against your profile", color: "#CCFF00" },
  { id: 5, name: "ATS Rewriter", desc: "Rewrites resume per JD for >80% keyword match using Groq AI", color: "#00F0FF" },
  { id: 6, name: "Cover Letter", desc: "Generates 250-word tailored cover letters with A/B variants", color: "#FF00FF" },
  { id: 7, name: "Credential Mgr", desc: "AES-256 encrypted session management across all job platforms", color: "#E0E0E0" },
  { id: 8, name: "Auto Submitter", desc: "Applies via Selenium, GraphQL, SMTP with human-like delays", color: "#CCFF00" },
  { id: 9, name: "Analytics", desc: "Tracks funnel metrics, A/B tests resume variants, weekly reports", color: "#00F0FF" },
];

function AgentNode3D({
  index,
  agent,
  active,
  onHover,
  onLeave,
}: {
  index: number;
  agent: typeof AGENTS[number];
  active: boolean;
  onHover: () => void;
  onLeave: () => void;
}) {
  const orbRef = useRef<THREE.Mesh>(null!);
  const lineGeoRef = useRef<THREE.BufferGeometry>(null!);
  const center = [0, 0, 0];

  // Wide Spacing Concentric Orbits (Concentric rings to prevent overlaps)
  const radiusFactor = 1.8 + index * 0.65;
  const radiusX = radiusFactor;
  const radiusY = radiusFactor * 0.55;
  const radiusZ = radiusFactor * 0.25; // 3D Tilt depth
  
  // Locked orbital speed for all nodes to guarantee they never collide or overlap
  const speed = 0.08;

  // Base phase angle offset - distributed symmetrically around the center
  const orbitAngleOffset = (index / AGENTS.length) * Math.PI * 2;

  // Generate static points for the orbit ring path once
  const orbitPoints = useMemo(() => {
    const pts = [];
    const segments = 64;
    for (let j = 0; j <= segments; j++) {
      const theta = (j / segments) * Math.PI * 2;
      pts.push(new THREE.Vector3(
        Math.cos(theta) * radiusX,
        -Math.sin(theta) * radiusY,
        Math.sin(theta) * radiusZ
      ));
    }
    return pts;
  }, [radiusX, radiusY, radiusZ]);

  const orbitGeo = useMemo(() => new THREE.BufferGeometry().setFromPoints(orbitPoints), [orbitPoints]);

  useFrame((state) => {
    const time = state.clock.elapsedTime;
    const angle = orbitAngleOffset + time * speed;
    const x = Math.cos(angle) * radiusX;
    const y = -Math.sin(angle) * radiusY;
    const z = Math.sin(angle) * radiusZ;

    // Position mesh
    if (orbRef.current) {
      orbRef.current.position.set(x, y, z);
      orbRef.current.rotation.y = time * 0.5;

      // Scale pulse animation
      const scale = active ? 1.4 : 1 + Math.sin(time * 2) * 0.05;
      orbRef.current.scale.setScalar(scale);
    }

    // Position pointer line (connect center to orb)
    if (lineGeoRef.current) {
      const points = [new THREE.Vector3(...center), new THREE.Vector3(x, y, z)];
      lineGeoRef.current.setFromPoints(points);
      lineGeoRef.current.attributes.position.needsUpdate = true; // Tell WebGL to re-upload vertices
    }
  });

  const LineComponent = "line" as any;

  return (
    <group>
      {/* Orbit path ring - beautifully visible outline */}
      <LineComponent geometry={orbitGeo}>
        <lineBasicMaterial
          color={agent.color}
          transparent
          opacity={active ? 0.75 : 0.24}
          linewidth={1}
        />
      </LineComponent>

      {/* 3D Dynamic pointer line */}
      <LineComponent>
        <bufferGeometry ref={lineGeoRef} />
        <lineBasicMaterial
          color={active ? "#CCFF00" : "#222222"}
          transparent
          opacity={active ? 0.95 : 0.25}
        />
      </LineComponent>

      {/* 3D Orb */}
      <mesh ref={orbRef}>
        <sphereGeometry args={[0.3, 32, 32]} />
        <meshStandardMaterial
          color={agent.color}
          emissive={agent.color}
          emissiveIntensity={active ? 1.4 : 0.4}
          metalness={0.9}
          roughness={0.1}
        />
        
        {/* Floating HTML overlay button - pixel-perfect concentric alignment */}
        <Html center distanceFactor={10} zIndexRange={[10, 50]}>
          <button
            className="pointer-events-auto cursor-pointer group flex flex-col items-center justify-center relative select-none w-12 h-12"
            onMouseEnter={onHover}
            onMouseLeave={onLeave}
          >
            <div
              className="w-12 h-12 rounded-full flex items-center justify-center text-xs font-grotesk font-bold transition-all duration-300 group-hover:scale-150"
              style={{ 
                background: `radial-gradient(circle at 30% 30%, ${agent.color}33, #000)`,
                border: `1px solid ${agent.color}`,
                color: agent.color,
                boxShadow: active ? `0 0 25px ${agent.color}, 0 0 50px ${agent.color}44` : `0 0 10px ${agent.color}55`,
              }}
            >
              {String(agent.id).padStart(2, "0")}
            </div>
            {/* Tooltip card */}
            <div 
              className={`absolute z-50 w-52 glass-panel rounded-lg p-3 transition-all duration-300 ${active ? "opacity-100 scale-100 animate-fade-in" : "opacity-0 scale-95 pointer-events-none"}`}
              style={{
                left: "50%",
                top: "100%",
                transform: "translate(-50%, 12px)",
                background: "rgba(10, 10, 10, 0.95)",
                backdropFilter: "blur(12px)",
                border: "1px solid rgba(255, 255, 255, 0.08)",
              }}
            >
              <p className="font-grotesk font-bold text-xs uppercase tracking-wider mb-1" style={{ color: agent.color }}>
                {agent.name}
              </p>
              <p className="text-xs text-white/60 font-jakarta leading-relaxed">
                {agent.desc}
              </p>
            </div>
          </button>
        </Html>
      </mesh>
    </group>
  );
}

function ConstellationScene({
  activeAgent,
  setActiveAgent,
}: {
  activeAgent: number | null;
  setActiveAgent: (val: number | null) => void;
}) {
  const orchRef = useRef<THREE.Mesh>(null!);
  const pointsRef = useRef<THREE.Points>(null!);

  // Simple, highly aesthetic solar glow shader featuring a bright yellow-green core and white Fresnel halo
  const sunMaterial = useMemo(() => {
    return new THREE.ShaderMaterial({
      uniforms: {
        uTime: { value: 0 },
        uColor: { value: new THREE.Color("#CCFF00") }, // Acid green
      },
      vertexShader: `
        varying vec3 vNormal;
        varying vec3 vViewPosition;

        void main() {
          vNormal = normalize(normalMatrix * normal);
          vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
          vViewPosition = -mvPosition.xyz;
          gl_Position = projectionMatrix * mvPosition;
        }
      `,
      fragmentShader: `
        varying vec3 vNormal;
        varying vec3 vViewPosition;

        uniform vec3 uColor;
        uniform float uTime;

        void main() {
          vec3 normal = normalize(vNormal);
          vec3 viewDir = normalize(vViewPosition);

          // Calculate Fresnel atmospheric edge glow
          float fresnel = pow(1.0 - max(dot(normal, viewDir), 0.0), 2.2);

          // Acid green core, bright glowing white edge
          vec3 coreColor = uColor;
          vec3 glowColor = vec3(1.0, 1.0, 0.9);

          vec3 finalColor = mix(coreColor, glowColor, fresnel * 0.9);

          // Smooth intensity heartbeat pulse
          float pulse = 1.0 + sin(uTime * 2.8) * 0.05;

          gl_FragColor = vec4(finalColor * pulse, 1.0);
        }
      `
    });
  }, []);

  // Solar flare flame particles configuration
  const PARTICLE_COUNT = 40;

  const [initialPositions, initialSizes, initialOpacities] = useMemo(() => {
    const pos = new Float32Array(PARTICLE_COUNT * 3);
    const sz = new Float32Array(PARTICLE_COUNT);
    const op = new Float32Array(PARTICLE_COUNT);
    return [pos, sz, op];
  }, []);

  // Store individual particle states in a stable array
  const particleData = useMemo(() => {
    const data = [];
    for (let i = 0; i < PARTICLE_COUNT; i++) {
      data.push({
        position: new THREE.Vector3(),
        velocity: new THREE.Vector3(),
        life: 0,
        maxLife: 0,
        speed: 0,
        size: 0,
      });
    }
    return data;
  }, []);

  // Initialize/reset a single particle near the sun surface flowing outward
  const initParticle = (index: number) => {
    const p = particleData[index];
    const theta = Math.random() * Math.PI * 2;
    const phi = Math.acos(Math.random() * 2 - 1);
    const r = 0.48; // Start just inside the 0.55 sun sphere

    p.position.set(
      Math.sin(phi) * Math.cos(theta) * r,
      Math.sin(phi) * Math.sin(theta) * r,
      Math.cos(phi) * r
    );

    // Dynamic velocity vectors pointing outwards with organic turbulence
    p.velocity.copy(p.position).normalize();
    p.velocity.x += (Math.random() - 0.5) * 0.25;
    p.velocity.y += (Math.random() - 0.5) * 0.25;
    p.velocity.z += (Math.random() - 0.5) * 0.25;
    p.velocity.normalize();

    p.speed = 0.35 + Math.random() * 0.5; // slow outwards flow
    p.maxLife = 0.6 + Math.random() * 0.7; // life span in seconds
    p.life = 0;
    p.size = 0.09 + Math.random() * 0.05; // particle diameter
  };

  // Stagger particle entry initially
  useMemo(() => {
    for (let i = 0; i < PARTICLE_COUNT; i++) {
      initParticle(i);
      particleData[i].life = Math.random() * particleData[i].maxLife;
    }
  }, [particleData]);

  // Imperatively attach custom buffer attributes to points geometry to ensure TypeScript compile safety
  useEffect(() => {
    if (pointsRef.current) {
      const geo = pointsRef.current.geometry;
      geo.setAttribute("aSize", new THREE.BufferAttribute(initialSizes, 1));
      geo.setAttribute("aOpacity", new THREE.BufferAttribute(initialOpacities, 1));
    }
  }, [initialSizes, initialOpacities]);

  // Particle Material rendering soft glowing additive circles
  const particleMaterial = useMemo(() => {
    return new THREE.ShaderMaterial({
      uniforms: {
        uColor: { value: new THREE.Color("#CCFF00") },
      },
      vertexShader: `
        attribute float aSize;
        attribute float aOpacity;
        varying float vOpacity;

        void main() {
          vOpacity = aOpacity;
          vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
          gl_PointSize = aSize * (350.0 / -mvPosition.z);
          gl_Position = projectionMatrix * mvPosition;
        }
      `,
      fragmentShader: `
        varying float vOpacity;
        uniform vec3 uColor;

        void main() {
          float dist = length(gl_PointCoord - vec2(0.5));
          if (dist > 0.5) discard;
          // Soft radial falloff for organic flame glow
          float alpha = smoothstep(0.5, 0.15, dist) * vOpacity;
          gl_FragColor = vec4(uColor, alpha);
        }
      `,
      transparent: true,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
    });
  }, []);

  useFrame((state, delta) => {
    const time = state.clock.elapsedTime;
    

    // Slow self-rotation & heartbeat pulse for the core sun mesh
    if (orchRef.current) {
      orchRef.current.rotation.y = time * 0.2;
      const scale = 1.0 + Math.sin(time * 2.0) * 0.025;
      orchRef.current.scale.setScalar(scale);
    }

    if (sunMaterial) {
      sunMaterial.uniforms.uTime.value = time;
    }

    // Dynamic updates for the flame particles
    if (pointsRef.current) {
      const geo = pointsRef.current.geometry;
      const posAttr = geo.attributes.position;
      const sizeAttr = geo.attributes.aSize as THREE.BufferAttribute;
      const opacityAttr = geo.attributes.aOpacity as THREE.BufferAttribute;

      if (posAttr && sizeAttr && opacityAttr) {
        const positions = posAttr.array as Float32Array;
        const sizes = sizeAttr.array as Float32Array;
        const opacities = opacityAttr.array as Float32Array;

        for (let i = 0; i < PARTICLE_COUNT; i++) {
          const p = particleData[i];
          p.life += delta;

          if (p.life >= p.maxLife) {
            initParticle(i);
          } else {
            p.position.addScaledVector(p.velocity, p.speed * delta);
          }

          // Buffer coordinates update
          positions[i * 3] = p.position.x;
          positions[i * 3 + 1] = p.position.y;
          positions[i * 3 + 2] = p.position.z;

          const progress = p.life / p.maxLife;

          // Fade out and shrink as they move away from the sun core
          opacities[i] = (1.0 - progress) * 0.85;
          sizes[i] = p.size * (1.0 - progress * 0.6);
        }

        posAttr.needsUpdate = true;
        sizeAttr.needsUpdate = true;
        opacityAttr.needsUpdate = true;
      }
    }
  });

  return (
    <>
      <ambientLight intensity={0.2} />
      <pointLight position={[0, 0, 5]} intensity={1} color="#CCFF00" />
      <pointLight position={[0, 0, -5]} intensity={0.5} color="#FF00FF" />
      
      {/* Orchestrator Center Orb (Sun) */}
      <mesh ref={orchRef} position={[0, 0, 0]}>
        <sphereGeometry args={[0.55, 32, 32]} />
        <primitive object={sunMaterial} attach="material" />
        
        {/* Centered ORCH text label with drop shadow for legibility */}
        <Html center transform={false} zIndexRange={[100, 100]}>
          <div className="pointer-events-none w-16 h-16 flex items-center justify-center text-center">
            <p 
              className="font-syne text-[11px] font-black tracking-widest text-black uppercase m-0 leading-none select-none"
              style={{
                textShadow: "0 0 5px rgba(204, 255, 0, 0.85), 0 0 10px rgba(204, 255, 0, 0.5)",
              }}
            >
              ORCH
            </p>
          </div>
        </Html>
      </mesh>

      {/* Subtle Solar Flame Particles cloud */}
      <points ref={pointsRef}>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            args={[initialPositions, 3]}
          />
        </bufferGeometry>
        <primitive object={particleMaterial} attach="material" />
      </points>

      {/* Render 9 Orbiting Concentric Agent Nodes */}
      {AGENTS.map((agent, i) => (
        <AgentNode3D
          key={agent.id}
          index={i}
          agent={agent}
          active={activeAgent === i}
          onHover={() => setActiveAgent(i)}
          onLeave={() => setActiveAgent(null)}
        />
      ))}
    </>
  );
}

export default function AgentConstellation() {
  const [activeAgent, setActiveAgent] = useState<number | null>(null);

  return (
    <section className="relative min-h-screen bg-void py-24 overflow-hidden" id="how-it-works">
      {/* Section label */}
      <div className="text-center mb-16 px-4">
        <p className="font-grotesk text-xs tracking-[0.4em] text-acid mb-4 uppercase">// 9-Agent System</p>
        <h2 className="font-syne font-black text-6xl md:text-8xl uppercase text-chrome distort-heading">
          THE <span className="acid-text">INTELLIGENCE</span>
        </h2>
        <h2 className="font-syne font-black text-6xl md:text-8xl uppercase outline-chrome distort-heading">
          ARCHITECTURE
        </h2>
      </div>

      {/* 3D Interactive Canvas - Expanded container height to prevent orbit path clipping when rotated */}
      <div className="w-full h-[900px] md:h-[1050px] relative select-none">
        <Canvas camera={{ position: [0, 0, 10.5], fov: 60 }}>
          <ConstellationScene activeAgent={activeAgent} setActiveAgent={setActiveAgent} />
          
          {/* Interactive controls with rotation constraints */}
          <OrbitControls 
            enableZoom={false} 
            enablePan={false} 
            maxPolarAngle={Math.PI / 1.95} 
            minPolarAngle={Math.PI / 2.5} 
          />
        </Canvas>
      </div>

      {/* Grid list detailing all agents */}
      <div className="max-w-6xl mx-auto px-6 mt-36 md:mt-56 grid grid-cols-1 md:grid-cols-3 gap-4">
        {AGENTS.map((agent, i) => (
          <div 
            key={agent.id}
            className="glass-panel rounded-2xl p-5 border border-white/5 hover:border-acid/30 transition-all duration-300 cursor-default group"
            style={{
              borderColor: activeAgent === i ? "rgba(204, 255, 0, 0.3)" : "rgba(255, 255, 255, 0.05)",
              background: activeAgent === i ? "rgba(204, 255, 0, 0.02)" : "rgba(255, 255, 255, 0.02)"
            }}
            onMouseEnter={() => setActiveAgent(i)}
            onMouseLeave={() => setActiveAgent(null)}
          >
            <div className="flex items-center gap-3 mb-3">
              <span className="font-grotesk text-xs font-bold tracking-widest" style={{ color: agent.color }}>
                AGENT {String(agent.id).padStart(2, "0")}
              </span>
            </div>
            <h3 className="font-syne font-bold text-lg text-chrome mb-2">{agent.name}</h3>
            <p className="text-sm text-chrome/50 font-jakarta leading-relaxed">{agent.desc}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
