"use client";
import { useRef, useMemo, useEffect } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { Points, PointMaterial, Text3D, Center } from "@react-three/drei";
import * as THREE from "three";
import { gsap } from "gsap";

// ─── Particle constellation (2000 points) ───
function ParticleField() {
  const ref = useRef<THREE.Points>(null!);
  const count = 2000;

  const positions = useMemo(() => {
    const pos = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);
      const r = 4 + Math.random() * 6;
      pos[i * 3] = r * Math.sin(phi) * Math.cos(theta);
      pos[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
      pos[i * 3 + 2] = r * Math.cos(phi);
    }
    return pos;
  }, []);

  useFrame((state) => {
    if (ref.current) {
      ref.current.rotation.y = state.clock.elapsedTime * 0.04;
      ref.current.rotation.x = Math.sin(state.clock.elapsedTime * 0.02) * 0.1;
    }
  });

  return (
    <Points ref={ref} positions={positions} stride={3} frustumCulled={false}>
      <PointMaterial
        transparent
        color="#CCFF00"
        size={0.025}
        sizeAttenuation={true}
        depthWrite={false}
        opacity={0.6}
      />
    </Points>
  );
}

// ─── Floating geometric resume document ───
function ResumeDocument() {
  const meshRef = useRef<THREE.Mesh>(null!);
  const lineRef = useRef<THREE.Group>(null!);

  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.rotation.y = Math.sin(state.clock.elapsedTime * 0.5) * 0.3;
      meshRef.current.rotation.x = Math.sin(state.clock.elapsedTime * 0.3) * 0.1;
      meshRef.current.position.y = Math.sin(state.clock.elapsedTime * 0.8) * 0.15;
    }
  });

  return (
    <group>
      {/* Main document body */}
      <mesh ref={meshRef} castShadow>
        <boxGeometry args={[1.4, 1.9, 0.04]} />
        <meshStandardMaterial
          color="#0A0A0A"
          metalness={0.9}
          roughness={0.1}
          emissive="#0A0F00"
        />
      </mesh>
      {/* Acid glow edge */}
      <mesh position={[0, 0, 0]}>
        <boxGeometry args={[1.42, 1.92, 0.035]} />
        <meshStandardMaterial
          color="#CCFF00"
          emissive="#CCFF00"
          emissiveIntensity={0.3}
          transparent
          opacity={0.15}
          wireframe
        />
      </mesh>
      {/* Document "lines" as thin boxes */}
      {[-0.5, -0.3, -0.1, 0.1, 0.3, 0.5, 0.65].map((y, i) => (
        <mesh key={i} position={[0, y, 0.03]}>
          <boxGeometry args={[i === 0 ? 0.7 : 1.0, 0.04, 0.001]} />
          <meshStandardMaterial
            color={i === 0 ? "#CCFF00" : "#333"}
            emissive={i === 0 ? "#CCFF00" : "#111"}
            emissiveIntensity={i === 0 ? 0.8 : 0.1}
          />
        </mesh>
      ))}
    </group>
  );
}

// ─── Ambient light setup ───
function Lighting() {
  return (
    <>
      <ambientLight intensity={0.1} />
      <pointLight position={[0, 0, 5]} intensity={0.5} color="#CCFF00" />
      <pointLight position={[-3, 2, 2]} intensity={0.3} color="#FF00FF" />
      <pointLight position={[3, -2, 2]} intensity={0.3} color="#00F0FF" />
    </>
  );
}

// ─── Mouse parallax camera ───
function CameraRig() {
  const { camera } = useThree();
  useFrame((state) => {
    camera.position.x += (state.mouse.x * 0.3 - camera.position.x) * 0.05;
    camera.position.y += (state.mouse.y * 0.2 - camera.position.y) * 0.05;
    camera.lookAt(0, 0, 0);
  });
  return null;
}

export default function HeroCanvas() {
  return (
    <Canvas
      camera={{ position: [0, 0, 5], fov: 60 }}
      style={{ background: "transparent" }}
      gl={{ antialias: true, alpha: true }}
    >
      <Lighting />
      <CameraRig />
      <ParticleField />
      <ResumeDocument />
    </Canvas>
  );
}
