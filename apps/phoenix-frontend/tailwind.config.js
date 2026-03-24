/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        'bg-deep': '#1a1b26',
        'bg-surface': '#24283b',
        'bg-elevated': '#2a2f3f',
        'accent-cyber': '#7dcfff',
        'accent-purple': '#bb9af7',
        'accent-green': '#9ece6a',
        'accent-orange': '#ff9e64',
        'accent-red': '#f7768e',
        'accent-pink': '#ff0077',
        'text-primary': '#c0caf5',
        'text-secondary': '#565f89',
        'border-subtle': '#292e42',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'SF Mono', 'monospace'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'spin-slow': 'spin 3s linear infinite',
        'glow': 'glow 2s ease-in-out infinite',
      },
      keyframes: {
        glow: {
          '0%, 100%': { textShadow: '0 0 10px rgba(125, 207, 255, 0.3)' },
          '50%': { textShadow: '0 0 20px rgba(125, 207, 255, 0.6)' },
        },
      },
    },
  },
  plugins: [],
}
