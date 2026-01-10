/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Dark theme colors
        'bg-primary': '#0f0f0f',
        'bg-secondary': '#1a1a1a',
        'bg-tertiary': '#252525',
        'bg-hover': '#2a2a2a',
        // Text colors
        'text-primary': '#ffffff',
        'text-secondary': '#a3a3a3',
        'text-muted': '#666666',
        // Accent - Purple (Qwen branding)
        'accent': '#7c3aed',
        'accent-hover': '#8b5cf6',
        'accent-muted': '#4c1d95',
        // Semantic colors
        'success': '#22c55e',
        'warning': '#eab308',
        'error': '#ef4444',
        // Border
        'border': '#333333',
        'divider': '#262626',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      // Custom animations
      animation: {
        'float': 'float 3s ease-in-out infinite',
        'ping-slow': 'ping-slow 2s cubic-bezier(0, 0, 0.2, 1) infinite',
        'ping-slower': 'ping-slower 2.5s cubic-bezier(0, 0, 0.2, 1) infinite 0.5s',
        'shimmer': 'shimmer 1.5s ease-in-out infinite',
        'spin-slow': 'spin 3s linear infinite',
        'bounce-in': 'bounce-in 0.4s cubic-bezier(0.34, 1.56, 0.64, 1)',
        'scale-fade-in': 'scale-fade-in 0.3s ease-out',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-6px)' },
        },
        'ping-slow': {
          '0%': { transform: 'scale(1)', opacity: '0.5' },
          '75%, 100%': { transform: 'scale(1.5)', opacity: '0' },
        },
        'ping-slower': {
          '0%': { transform: 'scale(1)', opacity: '0.3' },
          '75%, 100%': { transform: 'scale(1.8)', opacity: '0' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        'bounce-in': {
          '0%': { transform: 'scale(0.8)', opacity: '0' },
          '50%': { transform: 'scale(1.05)' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
        'scale-fade-in': {
          '0%': { transform: 'scale(0.95)', opacity: '0' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
      },
      // Custom shadows
      boxShadow: {
        'glow-accent': '0 0 20px rgba(124, 58, 237, 0.3), 0 0 60px rgba(124, 58, 237, 0.1)',
        'glow-subtle': '0 4px 24px rgba(0, 0, 0, 0.3), 0 0 40px rgba(124, 58, 237, 0.05)',
        'glow-input': '0 0 0 4px rgba(124, 58, 237, 0.1), 0 0 20px rgba(124, 58, 237, 0.15)',
        'card-hover': '0 10px 30px -10px rgba(0, 0, 0, 0.5), 0 0 20px rgba(124, 58, 237, 0.1)',
      },
      // Custom transitions
      transitionTimingFunction: {
        'spring': 'cubic-bezier(0.34, 1.56, 0.64, 1)',
        'smooth': 'cubic-bezier(0.16, 1, 0.3, 1)',
      },
    },
  },
  plugins: [],
}
