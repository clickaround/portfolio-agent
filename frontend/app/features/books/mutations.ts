import { api, unwrap } from "~/lib/api/client";

export type ComposeInput = { width_mm: number; height_mm: number; margin_mm: number; bleed_mm: number; header: boolean; also?: string[] };

export async function generatePortfolio(projectId: string, input: { instructions: string; width_mm: number; height_mm: number }) {
  return unwrap(await api.POST("/projects/{pid}/book-plan/generate", {
    params: { path: { pid: projectId } },
    body: { instructions: input.instructions, compose: { width_mm: input.width_mm, height_mm: input.height_mm, also: ["designcraft"] } },
  }));
}

/** Composes a new attempt from the plan in a background job. */
export async function composeBook(projectId: string, input: ComposeInput) {
  return unwrap(await api.POST("/projects/{pid}/compose", { params: { path: { pid: projectId } }, body: input }));
}

export async function openDesignCraft(projectId: string, attempt: string) {
  return unwrap(await api.POST("/projects/{pid}/attempts/{nn}/open-designcraft", { params: { path: { pid: projectId, nn: attempt } }, body: {} }));
}

/** Import an edited native file as a new independently reviewed attempt. */
export async function importDesignCraft(projectId: string, attempt: string, file: File): Promise<{ job: string }> {
  const body = new FormData();
  body.append("file", file);
  return unwrap(await api.POST("/projects/{pid}/attempts/{nn}/import-designcraft", {
    params: { path: { pid: projectId, nn: attempt } },
    body: body as never,
    bodySerializer: (value) => value as never,
  }));
}

export async function recoverLedger(projectId: string, attempt: string) {
  return unwrap(await api.POST("/projects/{pid}/attempts/{nn}/recover-ledger", { params: { path: { pid: projectId, nn: attempt } } }));
}

export async function suggestDesignCraft(projectId: string, attempt: string, input: { instructions: string; source_kind: "synthetic" | "real" | "unknown" }) {
  return unwrap(await api.POST("/projects/{pid}/attempts/{nn}/suggestions", { params: { path: { pid: projectId, nn: attempt } }, body: input }));
}

export async function rewriteEditorText(projectId: string, text: string) {
  return unwrap(await api.POST("/projects/{pid}/editor-text", { params: { path: { pid: projectId } }, body: { text, instructions: "Improve clarity and concision without adding facts." } }));
}

export async function chatEditor(projectId: string, attempt: string, messages: { role: "user" | "assistant"; content: string }[], liveDocument?: string) {
  return unwrap(await api.POST("/projects/{pid}/attempts/{nn}/editor-chat", { params: { path: { pid: projectId, nn: attempt } }, body: { messages, ...(liveDocument === undefined ? {} : { live_document: liveDocument }) } }));
}
