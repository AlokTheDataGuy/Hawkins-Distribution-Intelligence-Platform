/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        hawkins: {
          red:    '#C8102E',
          dark:   '#1F2937',
          steel:  '#6B7280',
          light:  '#F3F4F6',
          accent: '#F59E0B',
          green:  '#10B981',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
