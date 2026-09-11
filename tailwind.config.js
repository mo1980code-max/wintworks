/**
 * Tailwind build config for the CV Builder page.
 *
 * The page used to load the Tailwind Play CDN (`cdn.tailwindcss.com`), which
 * ships ~400 KB of JavaScript, compiles the utilities **in the visitor's
 * browser** after paint, and is explicitly not recommended for production.
 * This config is used by `npm run build:css` to emit the small static
 * `css/tailwind.min.css` that cv-builder.html loads instead.
 *
 *   npm run build:css      # rebuild after editing cv-builder.html classes
 */
module.exports = {
  content: ["./cv-builder.html", "./js/cv-builder.js"],
  darkMode: "class",
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      colors: {
        brand: {
          50: "#eff6ff",
          100: "#dbeafe",
          200: "#bfdbfe",
          300: "#93c5fd",
          400: "#60a5fa",
          500: "#3b82f6",
          600: "#2563eb",
          700: "#1d4ed8",
          800: "#1e40af",
          900: "#14357f",
        },
      },
    },
  },
  plugins: [],
};
