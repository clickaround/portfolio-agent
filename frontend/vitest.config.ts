import { defineConfig } from "vitest/config";

// Tests do not load the react-router plugin: pages are rendered through `createRoutesStub`.
export default defineConfig({
  resolve: { tsconfigPaths: true, dedupe: ["react", "react-dom"] },
  test: { environment: "jsdom", setupFiles: ["./test/setup.ts"], globals: true, css: false, include: ["app/**/*.test.{ts,tsx}"] },
});
