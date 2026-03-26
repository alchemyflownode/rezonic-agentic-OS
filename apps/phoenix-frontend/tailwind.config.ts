import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content:[
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans:["var(--font-sans)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "monospace"],
      },
      colors: {
        background: "var(--deep-bg)",
        foreground: "var(--text-primary)",
        primary: {
          DEFAULT: "var(--accent-cyan)",
          foreground: "#050507",
        },
        secondary: {
          DEFAULT: "var(--accent-amber)",
          foreground: "#050507",
        },
        cyan: {
          DEFAULT: "#00FFC2",
          dim: "#00CC9C",
        },
        amber: "#FFB800",
        deep: "#050507",
        surface: "#0A0A0C",
        elevated: "#121214",
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "scan": "scan 8s linear infinite",
        "float": "float 3s ease-in-out infinite",
        "ping-slow": "ping 2s cubic-bezier(0, 0, 0.2, 1) infinite",
      },
      keyframes: {
        scan: {
          "0%": { transform: "translateX(-100%)" },
          "100%": { transform: "translateX(100%)" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-5px)" },
        },
      },
      borderRadius: {
        sm: "2px",
        md: "4px",
        lg: "8px",
        xl: "12px",
        "2xl": "16px",
        "3xl": "20px",
      },
      boxShadow: {
        'glass': '0 8px 32px rgba(0, 0, 0, 0.5)',
        'glass-lg': '0 12px 48px rgba(0, 0, 0, 0.6)',
        'glow-cyan': '0 0 30px rgba(0, 255, 194, 0.2)',
        'glow-amber': '0 0 30px rgba(255, 184, 0, 0.15)',
      },
    },
  },
  plugins:[
    require("tailwindcss-animate"),
    require("@tailwindcss/typography") // <-- CRITICAL: Required for Markdown chat
  ],
};

export default config;