import { describe, expect, it, vi } from "vitest";
import { clientAction } from "./review-page";

vi.mock("../mutations", () => ({ bindReviewContext: vi.fn(), finalizeBook: vi.fn(), recordReview: vi.fn().mockResolvedValue({}) }));
import { recordReview } from "../mutations";

describe("record review", () => {
  const ctx = { attempt: "01", frames: { "page-01.png": "aa", "page-02.png": "bb" }, review_context_sha256: "cc" };
  function request(checked: string[]) {
    const data = new FormData();
    data.set("intent", "record");
    data.set("context", JSON.stringify(ctx));
    for (const frame of checked) data.append("reviewed_frame", frame);
    return new Request("http://localhost/review", { method: "POST", body: data });
  }
  it("rejects recording until every frame is explicitly checked", async () => {
    vi.mocked(recordReview).mockClear();
    const out = await clientAction({ request: request(["page-01.png"]), params: { projectId: "demo" } } as never);
    expect(out.error).toMatch(/every page/i);
    expect(recordReview).not.toHaveBeenCalled();
  });
  it("records explicitly checked frames", async () => {
    vi.mocked(recordReview).mockClear();
    await clientAction({ request: request(Object.keys(ctx.frames)), params: { projectId: "demo" } } as never);
    expect(recordReview).toHaveBeenCalledWith("demo", expect.objectContaining({ reviewed_frames: Object.keys(ctx.frames) }));
  });
  it("requires a human to confirm native edit fidelity and geometry", async () => {
    vi.mocked(recordReview).mockClear();
    const form = new FormData();
    form.set("intent", "record");
    form.set("context", JSON.stringify({ ...ctx, native_edit: { pages: 2 } }));
    form.set("mode", "human");
    for (const frame of Object.keys(ctx.frames)) form.append("reviewed_frame", frame);
    const out = await clientAction({ request: { formData: async () => form }, params: { projectId: "demo" } } as never);
    expect(out.error).toBeTruthy();
    expect(recordReview).not.toHaveBeenCalled();
    for (const key of ["reviewed_exported_pages", "content_and_source_fidelity_confirmed", "page_geometry_and_clipping_confirmed"]) form.set(key, "on");
    await clientAction({ request: { formData: async () => form }, params: { projectId: "demo" } } as never);
    expect(recordReview).toHaveBeenCalledWith("demo", expect.objectContaining({ native_edit_confirmation: expect.objectContaining({ content_and_source_fidelity_confirmed: true }) }));
  });
});
