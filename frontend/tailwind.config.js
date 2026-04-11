/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        legal: {
          50:  '#e6edf5',
          100: '#ccdaeb',
          200: '#99b5d7',
          300: '#6690c2',
          400: '#336bae',
          500: '#003366', // primary brand blue
          600: '#002952',
          700: '#001f3d',
          800: '#001429',
          900: '#000a14',
        },
        gold: {
          50:  '#fdf8e6',
          100: '#fbf1cd',
          200: '#f7e39b',
          300: '#f3d469',
          400: '#efc637',
          500: '#B8860B', // accent gold
          600: '#936b09',
          700: '#6e5007',
          800: '#4a3504',
          900: '#251b02',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'pulse-slow': 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}
