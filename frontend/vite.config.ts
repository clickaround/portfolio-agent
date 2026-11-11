import { reactRouter } from "@react-router/dev/vite";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";

// Tailwind v4: no tailwind.config.ts / postcss.config.js / autoprefixer. The Vite plugin + `@import "tailwindcss"` in app/app.css is all.
export default defineConfig({
  plugins: [tailwindcss(), reactRouter()],
  resolve: { tsconfigPaths: true, dedupe: ["react", "react-dom"] }, // Share the consuming app's React with DUI.
  server: { port: 5173 },
});
