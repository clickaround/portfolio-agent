import type { Config } from "@react-router/dev/config";

// Framework mode as a SPA: the Pascal API (backend/api) is a separate service, so there is no server rendering and no server loaders.
// Pages fetch with `clientLoader` / `clientAction`; `react-router build` emits static files in build/client.
export default {
  ssr: false,
} satisfies Config;
