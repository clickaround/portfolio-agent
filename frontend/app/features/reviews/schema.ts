// Mirrors portfolio_agent review.py (reviewAgent): the 8 rubric dimensions and the context the reviewer's verdict must be bound to.
export const DIMENSIONS = ["hierarchy", "composition_balance", "whitespace_intent", "typography", "sequence_narrative", "asset_fidelity", "domain_fit", "anti_template"] as const;
export const REVIEWER_MODES = ["human", "fresh_session", "fresh_subagent"] as const;

export type ReviewContext = {
  attempt: string;
  frames: Record<string, string>; // "page-01.png" -> sha256
  review_context_sha256: string;
};

/** The review JSON the backend validates; hashes are copied verbatim from the bound context. */
export function buildReview(ctx: ReviewContext, input: { mode: string; scores: Record<string, number>; blockers: string[]; issues: string[]; reviewedFrames: string[] }) {
  return {
    review_context_sha256: ctx.review_context_sha256,
    frame_hashes: ctx.frames,
    reviewed_frames: input.reviewedFrames,
    reviewer_mode: input.mode,
    dimension_scores: input.scores,
    blockers: input.blockers,
    issues: input.issues,
  };
}

export const pageNumber = (frame: string) => Number(/page-(\d+)/.exec(frame)?.[1] ?? 0);
