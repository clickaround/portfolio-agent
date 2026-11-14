# reviewAgent Tool Guidance

<!-- Harness² C4 tool guidance (tool_descriptions/tool_guidance.md). Every call. When and how to use each existing tool. -->

- Order is fixed: `review-context` -> a fresh reviewer writes `review.json` from the bound frames -> `record-review` -> `finalize`.
- Run `review-context` again after any change, including an edit (an edit creates a new attempt); old hashes no longer match.
- The verdict follows from the scores: `pass` needs no blocker and a mean of at least 0.75; a blocker or a mean below 0.5 is `fail`; the rest is `revise`. `record-review` rejects any other verdict.
- The reviewer gets Read access to the frames and the rubric only. It gets no write tools and no unblind key.
- Benchmarks and blind runs are run from `benchmarks/`, not through these tools.
