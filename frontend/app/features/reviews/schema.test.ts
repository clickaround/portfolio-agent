import { describe, expect, it } from "vitest";
import { buildReview, DIMENSIONS, pageNumber } from "./schema";

describe("buildReview", () => {
  it("copies the bound hashes and frames verbatim", () => {
    const ctx = { attempt: "01", frames: { "page-01.png": "aa", "page-02.png": "bb" }, review_context_sha256: "cc" };
    const scores = Object.fromEntries(DIMENSIONS.map((d) => [d, 0.8]));
    const r = buildReview(ctx, { mode: "human", scores, blockers: [], issues: ["x"], reviewedFrames: ["page-01.png"] });
    expect(r.review_context_sha256).toBe("cc");
    expect(r.frame_hashes).toEqual(ctx.frames);
    expect(r.reviewed_frames).toEqual(["page-01.png"]);
    expect(Object.keys(r.dimension_scores)).toHaveLength(8);
  });
  it("reads the page number from a frame name", () => expect(pageNumber("page-07.png")).toBe(7));
});
