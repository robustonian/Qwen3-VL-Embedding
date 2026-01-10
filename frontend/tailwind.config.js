/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Backgrounds - Cosmic depth with blue undertones
        'bg-primary': '#0a0a0b',
        'bg-secondary': '#12121a',
        'bg-tertiary': '#1a1a24',
        'bg-hover': '#222230',
        'bg-elevated': '#1e1e2a',

        // Text - Slightly cool white
        'text-primary': '#f0f0f5',
        'text-secondary': '#8b8b9e',
        'text-muted': '#4a4a5c',

        // Accent - Teal/Cyan (main)
        'accent': '#00d4aa',
        'accent-hover': '#00f5c4',
        'accent-muted': '#00a080',
        'accent-glow': 'rgba(0, 212, 170, 0.15)',

        // Secondary accent - Warm amber (complementary)
        'accent-warm': '#f5a623',
        'accent-warm-hover': '#ffb84d',

        // Semantic colors
        'success': '#00d68f',
        'warning': '#ffaa00',
        'error': '#ff5a5a',

        // Border
        'border': '#2a2a3a',
        'border-subtle': '#1f1f2a',
        'divider': '#1a1a24',
      },
      fontFamily: {
        sans: ['Plus Jakarta Sans', 'system-ui', 'sans-serif'],
        display: ['Outfit', 'system-ui', 'sans-serif'],
        mono: ['IBM Plex Mono', 'monospace'],
      },
      // Custom animations
      animation: {
        'float': 'float 3s ease-in-out infinite',
        'float-slow': 'float 4s ease-in-out infinite',
        'ping-slow': 'ping-slow 2s cubic-bezier(0, 0, 0.2, 1) infinite',
        'ping-slower': 'ping-slower 2.5s cubic-bezier(0, 0, 0.2, 1) infinite 0.5s',
        'shimmer': 'shimmer 1.5s ease-in-out infinite',
        'shimmer-fast': 'shimmer 1s ease-in-out infinite',
        'spin-slow': 'spin 3s linear infinite',
        'bounce-in': 'bounce-in 0.4s cubic-bezier(0.34, 1.56, 0.64, 1)',
        'scale-fade-in': 'scale-fade-in 0.3s ease-out',
        'slide-up': 'slide-up 0.5s cubic-bezier(0.16, 1, 0.3, 1)',
        'slide-down': 'slide-down 0.3s cubic-bezier(0.16, 1, 0.3, 1)',
        'slide-in-right': 'slide-in-right 0.4s cubic-bezier(0.16, 1, 0.3, 1)',
        'slide-out-right': 'slide-out-right 0.3s ease-in',
        'glow-pulse': 'glow-pulse 2s ease-in-out infinite',
        'border-glow': 'border-glow 2s ease-in-out infinite',
        'scale-in': 'scale-in 0.3s cubic-bezier(0.34, 1.56, 0.64, 1)',
        'fade-in': 'fade-in 0.2s ease-out',
        'orbit': 'orbit 8s linear infinite',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-8px)' },
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
        'slide-up': {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'slide-down': {
          '0%': { opacity: '0', transform: 'translateY(-10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'slide-in-right': {
          '0%': { opacity: '0', transform: 'translateX(100%)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        'slide-out-right': {
          '0%': { opacity: '1', transform: 'translateX(0)' },
          '100%': { opacity: '0', transform: 'translateX(100%)' },
        },
        'glow-pulse': {
          '0%, 100%': { boxShadow: '0 0 20px rgba(0, 212, 170, 0.2)' },
          '50%': { boxShadow: '0 0 40px rgba(0, 212, 170, 0.4)' },
        },
        'border-glow': {
          '0%, 100%': { borderColor: 'rgba(0, 212, 170, 0.3)' },
          '50%': { borderColor: 'rgba(0, 212, 170, 0.6)' },
        },
        'scale-in': {
          '0%': { opacity: '0', transform: 'scale(0.9)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
        'fade-in': {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        'orbit': {
          '0%': { transform: 'rotate(0deg) translateX(30px) rotate(0deg)' },
          '100%': { transform: 'rotate(360deg) translateX(30px) rotate(-360deg)' },
        },
      },
      // Custom shadows with teal glow
      boxShadow: {
        'glow-accent': '0 0 20px rgba(0, 212, 170, 0.3), 0 0 60px rgba(0, 212, 170, 0.1)',
        'glow-subtle': '0 4px 24px rgba(0, 0, 0, 0.4), 0 0 40px rgba(0, 212, 170, 0.05)',
        'glow-input': '0 0 0 4px rgba(0, 212, 170, 0.1), 0 0 20px rgba(0, 212, 170, 0.15)',
        'glow-strong': '0 0 30px rgba(0, 212, 170, 0.4), 0 0 80px rgba(0, 212, 170, 0.2)',
        'card-hover': '0 20px 40px -15px rgba(0, 0, 0, 0.5), 0 0 25px rgba(0, 212, 170, 0.1)',
        'card-elevated': '0 10px 30px -5px rgba(0, 0, 0, 0.4)',
        'inner-glow': 'inset 0 0 30px rgba(0, 212, 170, 0.1)',
      },
      // Custom transitions
      transitionTimingFunction: {
        'spring': 'cubic-bezier(0.34, 1.56, 0.64, 1)',
        'smooth': 'cubic-bezier(0.16, 1, 0.3, 1)',
        'bounce': 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
      },
      // Backdrop blur
      backdropBlur: {
        'xs': '2px',
        '2xl': '40px',
        '3xl': '64px',
      },
      // Border radius
      borderRadius: {
        '4xl': '2rem',
      },
    },
  },
  plugins: [],
}
