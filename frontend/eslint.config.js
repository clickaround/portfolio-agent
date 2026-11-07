import js from "@eslint/js";
import globals from "globals";
import tseslint from "typescript-eslint";
import reactHooks from "eslint-plugin-react-hooks";
import importX from "eslint-plugin-import-x";

// Unidirectional architecture: shared (common, lib, hooks) -> features -> routes.ts (the app).
//   a feature never imports another feature; shared folders never import features.
const features = ["projects", "sources", "plans", "books", "reviews"]; // add a feature folder here when you add app/features/<name>
const shared = ["common", "lib", "hooks", "types"];

export default tseslint.config(
  { ignores: ["build", ".react-router", "frontend", "node_modules", "app/types/api.d.ts"] },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    files: ["**/*.{ts,tsx}"],
    languageOptions: { globals: globals.browser },
    plugins: { "react-hooks": reactHooks, "import-x": importX },
    rules: {
      ...reactHooks.configs.recommended.rules,
      "import-x/no-restricted-paths": ["error", {
        zones: [
          ...features.map((f) => ({ target: `./app/features/${f}`, from: "./app/features", except: [`./${f}`], message: "features must not import other features; compose them in routes.ts or common/" })),
          ...shared.map((s) => ({ target: `./app/${s}`, from: "./app/features", message: "shared code must not import features" })),
        ],
      }],
    },
  },
);
