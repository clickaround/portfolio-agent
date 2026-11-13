# reviewAgent Tool Guidance

<!-- Harness² C4 tool guidance (tool_descriptions/tool_guidance.md). Every call. When and how to use each existing tool. -->

- Order is fixed: `review-context` -> a fresh reviewer writes `review.json` from the bound frames -> `record-review` -> `finalize`.
- Run `review-context` again after any change to the attempt; old hashes no longer match.
- The reviewer gets Read access to the frames and the rubric only. It gets no write tools and no unblind key.
- Benchmarks and blind runs are run from `benchmarks/`, not through these tools.
