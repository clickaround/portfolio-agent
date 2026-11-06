import { reactRouter } from "@react-router/dev/vite";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";

// Tailwind v4: no tailwind.config.ts / postcss.config.js / autoprefixer. The Vite plugin + `@import "tailwindcss"` in app/app.css is all.
export default defineConfig({
  plugins: [tailwindcss(), reactRouter()],
  resolve: { tsconfigPaths: true }, // Vite 8 resolves tsconfig paths natively (no vite-tsconfig-paths plugin)
  server: { port: 5173 },
});
