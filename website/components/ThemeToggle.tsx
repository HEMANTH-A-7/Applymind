"use client";
import { useTheme } from "./ThemeProvider";

export default function ThemeToggle({ className = "" }: { className?: string }) {
  const { theme, toggle } = useTheme();
  const isDark = theme === "dark";

  return (
    <button
      onClick={toggle}
      aria-label={isDark ? "Switch to light theme" : "Switch to dark theme"}
      title={isDark ? "Light mode" : "Dark mode"}
      className={`group flex items-center gap-2 px-3 py-1.5 rounded-full border transition-all duration-300 cursor-pointer
        ${isDark
          ? "border-white/10 bg-white/5 hover:border-[#CCFF00]/40"
          : "border-black/10 bg-black/5 hover:border-[#7AB800]/40"
        } ${className}`}
    >
      {/* Sun / Moon icon */}
      <span className="text-sm leading-none select-none transition-transform duration-500 group-hover:rotate-12">
        {isDark ? "☀" : "◑"}
      </span>

      {/* Track */}
      <span
        className="relative w-9 h-5 rounded-full transition-colors duration-300 shrink-0"
        style={{ background: isDark ? "rgba(204,255,0,0.15)" : "rgba(122,184,0,0.2)" }}
      >
        {/* Knob */}
        <span
          className="absolute top-0.5 w-4 h-4 rounded-full transition-all duration-300 shadow-sm"
          style={{
            left: isDark ? "2px" : "calc(100% - 18px)",
            background: isDark ? "#CCFF00" : "#7AB800",
            boxShadow: isDark
              ? "0 0 8px rgba(204,255,0,0.6)"
              : "0 0 6px rgba(122,184,0,0.4)",
          }}
        />
      </span>

      {/* Label */}
      <span
        className="text-[10px] font-bold uppercase tracking-widest hidden sm:block"
        style={{ color: isDark ? "#CCFF00" : "#7AB800" }}
      >
        {isDark ? "Dark" : "Light"}
      </span>
    </button>
  );
}
