import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        sala: {
          primary: '#2563EB',
          'primary-dark': '#1E40AF',
          'primary-light': '#3B82F6',
          sky: '#0EA5E9',
          cyan: '#22D3EE',
          bg: '#0B0F1A',
          surface: '#111827',
          'surface-muted': '#0F172A',
          success: '#22C55E',
          warning: '#F59E0B',
          danger: '#EF4444',
        },
        dark: {
          900: '#0B0F1A',
          800: '#111827',
          700: '#1a1a24',
          600: '#22222e',
          500: '#2a2a38',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
      },
    },
  },
  plugins: [],
}

export default config
