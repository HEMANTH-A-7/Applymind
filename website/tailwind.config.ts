import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Acid Graphic Palette
        void: "#000000",
        onyx: "#0A0A0A",
        acid: "#CCFF00",
        magenta: "#FF00FF",
        cyan: "#00F0FF",
        chrome: "#E0E0E0",
        "chrome-dark": "#888888",
        "acid-dim": "#99BF00",
      },
      fontFamily: {
        syne: ["Syne", "sans-serif"],
        jakarta: ["Plus Jakarta Sans", "sans-serif"],
        grotesk: ["Space Grotesk", "monospace"],
      },
      backgroundImage: {
        "chrome-gradient": "linear-gradient(180deg, #FFFFFF 0%, #888888 50%, #E0E0E0 100%)",
        "acid-glow": "radial-gradient(circle, rgba(204,255,0,0.15) 0%, transparent 70%)",
        "magenta-glow": "radial-gradient(circle, rgba(255,0,255,0.15) 0%, transparent 70%)",
        "cyan-glow": "radial-gradient(circle, rgba(0,240,255,0.1) 0%, transparent 70%)",
        "iridescent": "linear-gradient(135deg, #CCFF00 0%, #00F0FF 33%, #FF00FF 66%, #CCFF00 100%)",
      },
      animation: {
        "marquee": "marquee 20s linear infinite",
        "marquee-reverse": "marquee-reverse 25s linear infinite",
        "float": "float 8s ease-in-out infinite",
        "float-delayed": "float 10s ease-in-out infinite 3s",
        "pulse-acid": "pulse-acid 2s cubic-bezier(0.4,0,0.6,1) infinite",
        "glitch": "glitch 3s steps(1) infinite",
        "spin-slow": "spin 20s linear infinite",
        "drift": "drift 20s ease-in-out infinite",
        "blob-morph": "blob-morph 12s ease-in-out infinite",
      },
      keyframes: {
        marquee: {
          "0%": { transform: "translateX(0%)" },
          "100%": { transform: "translateX(-50%)" },
        },
        "marquee-reverse": {
          "0%": { transform: "translateX(-50%)" },
          "100%": { transform: "translateX(0%)" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0px) rotate(0deg)" },
          "33%": { transform: "translateY(-20px) rotate(1deg)" },
          "66%": { transform: "translateY(-10px) rotate(-1deg)" },
        },
        "pulse-acid": {
          "0%, 100%": { boxShadow: "0 0 20px rgba(204,255,0,0.4), 0 0 60px rgba(204,255,0,0.1)" },
          "50%": { boxShadow: "0 0 40px rgba(204,255,0,0.8), 0 0 120px rgba(204,255,0,0.3)" },
        },
        glitch: {
          "0%, 90%, 100%": { transform: "translate(0)" },
          "92%": { transform: "translate(-2px, 1px)" },
          "94%": { transform: "translate(2px, -1px)" },
          "96%": { transform: "translate(-1px, 2px)" },
          "98%": { transform: "translate(1px, -2px)" },
        },
        drift: {
          "0%, 100%": { transform: "translate(0, 0) scale(1)" },
          "25%": { transform: "translate(30px, -20px) scale(1.05)" },
          "50%": { transform: "translate(-20px, 30px) scale(0.95)" },
          "75%": { transform: "translate(20px, 10px) scale(1.02)" },
        },
        "blob-morph": {
          "0%, 100%": { borderRadius: "60% 40% 30% 70% / 60% 30% 70% 40%" },
          "25%": { borderRadius: "30% 60% 70% 40% / 50% 60% 30% 60%" },
          "50%": { borderRadius: "50% 60% 30% 60% / 30% 40% 70% 60%" },
          "75%": { borderRadius: "40% 60% 50% 50% / 40% 60% 50% 50%" },
        },
      },
      boxShadow: {
        "acid": "0 0 30px rgba(204,255,0,0.5), 0 0 60px rgba(204,255,0,0.2)",
        "acid-sm": "0 0 15px rgba(204,255,0,0.4)",
        "magenta": "0 0 30px rgba(255,0,255,0.5), 0 0 60px rgba(255,0,255,0.2)",
        "cyan": "0 0 30px rgba(0,240,255,0.5), 0 0 60px rgba(0,240,255,0.2)",
        "chrome": "0 4px 30px rgba(255,255,255,0.15)",
        "inset-acid": "inset 0 0 30px rgba(204,255,0,0.1)",
      },
      dropShadow: {
        "acid": ["0 0 8px rgba(204,255,0,0.8)", "0 0 20px rgba(204,255,0,0.4)"],
        "chrome": ["0 0 8px rgba(255,255,255,0.6)", "1px 1px 0px rgba(255,0,255,0.3)", "-1px -1px 0px rgba(0,240,255,0.3)"],
      },
    },
  },
  plugins: [],
};

export default config;
