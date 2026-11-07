// URLs of binary/static API resources (images, page previews, PDF). Used in <img src> / <a href>, so they are not fetch calls.
export const API_URL: string = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

export const assetUrl = (projectId: string, relativePath: string) => `${API_URL}/projects/${projectId}/files/${relativePath.split("/").map(encodeURIComponent).join("/")}`;
export const pageUrl = (projectId: string, attempt: string, page: number) => `${API_URL}/projects/${projectId}/attempts/${attempt}/pages/${page}.png`;
export const bookUrl = (projectId: string, attempt: string, ext: "pdf" | "pptx" | "designcraft") => `${API_URL}/projects/${projectId}/attempts/${attempt}/book.${ext}`;
