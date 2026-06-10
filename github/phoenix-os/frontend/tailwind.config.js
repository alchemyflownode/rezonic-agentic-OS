// tailwind.config.ts
import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './app/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        phoenix: {
          bg:      '#0a0a0c',
          bgSoft:  '#050505',
          bgGlass: 'rgba(0,0,0,0.3)',
          primary: '#7dcfff',
          accent:  '#9B72CB',
          text:    '#c0caf5',
          muted:   '#565f89',
          success: '#9ece6a',
          error:   '#f7768e',
          warning: '#e0af68',
          border:  'rgba(125,207,255,0.1)',
        },
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      animation: {
        'drift-scroll': 'drift-scroll 20s linear infinite',
        'cursor-blink': 'cursor-blink 1s step-end infinite',
        'scan-line':    'scan-line 4s linear infinite',
      },
      keyframes: {
        'drift-scroll': {
          '0%':   { transform: 'translateY(0)' },
          '100%': { transform: 'translateY(-50%)' },
        },
        'cursor-blink': {
          '0%, 100%': { opacity: '1' },
          '50%':      { opacity: '0' },
        },
        'scan-line': {
          '0%':   { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100vh)' },
        },
      },
    },
  },
  plugins: [],
};

export default config;