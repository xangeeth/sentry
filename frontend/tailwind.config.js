/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#0f172a', // Deep slate/blue [cite: 65]
        surface: '#1e293b',    // Lighter slate for cards/modals [cite: 65]
        primary: '#3b82f6',    // Sentry Blue
      }
    },
  },
  plugins: [],
}