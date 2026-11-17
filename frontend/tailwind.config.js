/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f6f4fd',
          100: '#ede9fb',
          200: '#ddd6f8',
          300: '#c5b9f1',
          400: '#a696e8',
          500: '#8874da',
          600: '#6f58c7',
          700: '#5c46ab',
          800: '#4b398c',
          900: '#3f3073',
          950: '#271e49',
        }
      }
    },
  },
  plugins: [],
}
