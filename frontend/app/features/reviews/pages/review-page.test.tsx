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
});
