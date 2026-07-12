"use client";
import dynamic from "next/dynamic";

import HeroSection from "@/components/HeroSection";
import AgentConstellation from "@/components/AgentConstellation";
import StatsSection from "@/components/StatsSection";
import PricingSection from "@/components/PricingSection";
import FooterCTA from "@/components/FooterCTA";

// Dashboard preview has heavy 3D; load client-side
const DashboardPreview = dynamic(() => import("@/components/DashboardPreview"), {
  ssr: false,
  loading: () => (
    <div className="min-h-screen bg-onyx flex items-center justify-center">
      <div className="w-2 h-2 rounded-full bg-acid animate-ping" />
    </div>
  ),
});

export default function Home() {
  return (
    <main className="bg-void min-h-screen">
      <HeroSection />
      <AgentConstellation />
      <StatsSection />
      <DashboardPreview />
      <PricingSection />
      <FooterCTA />
    </main>
  );
}
