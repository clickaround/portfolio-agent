import { afterEach, expect, it, vi } from "vitest";
import { executeEditorCommand } from "./editor-command";

afterEach(() => vi.restoreAllMocks());

it("accepts only the matching same-origin editor response", async () => {
  const frame = document.createElement("iframe");
  document.body.appendChild(frame);
  const target = frame.contentWindow!;
  const post = vi.spyOn(target, "postMessage").mockImplementation(() => {});
  const request = executeEditorCommand(frame, "frame.create", { rect: [72, 72, 300, 150] });
  const payload = post.mock.calls[0]![0] as { id: string };
  window.dispatchEvent(new MessageEvent("message", { origin: "https://evil.example", source: target, data: { type: "pascal-editor-result", id: payload.id, ok: true, result: "bad" } }));
  window.dispatchEvent(new MessageEvent("message", { origin: window.location.origin, source: target, data: { type: "pascal-editor-result", id: payload.id, ok: true, result: "created" } }));
  await expect(request).resolves.toBe("created");
  frame.remove();
});
