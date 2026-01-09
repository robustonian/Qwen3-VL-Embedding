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
    },
  },
  plugins: [],
}
