// The manifest comes back as a free-form object in OpenAPI; this is the part the UI reads (see portfolio_agent.core.sources).
export type ManifestAsset = {
  id: string;
  relative_path: string;
  kind: string;
  role?: string;
  rights?: string;
  width?: number;
  height?: number;
  aspect?: number;
  crop_allowed?: boolean;
  sha256: string;
};
export type Manifest = { assets: ManifestAsset[] };
export type AssetKind = "images" | "drawings" | "diagrams";
export const ASSET_KINDS: AssetKind[] = ["images", "drawings", "diagrams"];
