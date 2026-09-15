/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        gov: {
          navy: '#0B3D6E',
          darkNavy: '#0A2540',
          bg: '#F4F6F8',
          card: '#FFFFFF',
          border: '#D1D5DB',
        },
        vault: {
          darkest: '#07090E',
          dark: '#0D111A',
          card: '#131926',
          cardHover: '#1A2234',
          border: '#232E45',
          borderLight: '#334155',
          muted: '#8E9BAE',
          text: '#F1F5F9',
        },
        accent: {
          purple: '#8B5CF6',
          indigo: '#6366F1',
          cyan: '#06B6D4',
          amber: '#F59E0B',
          rose: '#F43F5E',
          emerald: '#10B981',
        },
      },
      fontFamily: {
        sans: ['"Noto Sans"', 'system-ui', 'sans-serif'],
        serif: ['"Merriweather"', 'Georgia', 'serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },

      boxShadow: {
        'glow-purple': '0 0 25px -5px rgba(139, 92, 246, 0.3)',
        'glow-cyan': '0 0 25px -5px rgba(6, 182, 212, 0.3)',
        'glow-amber': '0 0 25px -5px rgba(245, 158, 11, 0.3)',
        'glass': '0 8px 32px 0 rgba(0, 0, 0, 0.37)',
      },
      backdropBlur: {
        'xs': '2px',
      },
      animation: {
        'pulse-subtle': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'float': 'float 6s ease-in-out infinite',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-6px)' },
        }
      }
    },
  },
  plugins: [],
}
