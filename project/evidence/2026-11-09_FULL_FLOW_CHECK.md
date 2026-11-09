# Full flow check — 2026-11-09

Task: user-requested synthetic end-to-end audit and import completion feedback.

## REPRODUCED

- Isolated local frontend `127.0.0.1:15176` and API `127.0.0.1:18083`, separate `.cache/harness-e2e-20261109/data` project store. In the browser: create `flowcheck`, edit brief, upload six synthetic photos, submit generation, and open generated attempt 01 automatically.
- Generation and chat used deterministic fake LLM runners. The actual API, asynchronous jobs, portfolio pipeline, DesignCraft CLI and browser Rust/WASM editor were used. Chat included live document inspection and inserted `SYNTHETIC ROUNDTRIP TITLE` into the document.
- Browser Ctrl+S captured the edited native document; importing it created attempt 02 with a real five-page PDF. Extracting PDF text confirms the inserted title is absent from attempt 01 and present in attempt 02. SHA-256: attempt 01 `10f3855f98f9e94626954703954929c7d2b2bf200888d04942b956ceb214db7f`; attempt 02 `a71da28b31b8136e85b9d46937fe163c1484a3821cdf6bea2be7cb787261683b`.
- Import completion previously disappeared without identifying the new attempt. After the UI fix a second browser save/import created attempt 03, displayed the attempt number and linked to the review screen. The review screen bound five frames and displayed source checks and review controls.
- The review-context API succeeded for attempt 02; finalization without a fresh human review returned HTTP 422. No human review or final delivery was fabricated.
- At 1440x900 the editor workspace occupied the viewport; at 390x844 its outer document and inner editor had no horizontal overflow. The desktop divider responded to a keyboard adjustment (45 to 47). This is a bounded viewport check, not a full accessibility or device audit.
- `npm run typecheck`, `npm run lint`, `npm test` (36 tests), `npm run build`, and `uv run pytest backend/apps/api/tests -q` (58 tests): exit 0. An initial concurrent frontend test failed with Windows EPERM from two React Router type-generation processes; running the test alone passed.

## BLOCKED / NOT VERIFIED

- The live Claude quota was exhausted during this session; real model generation and chat were not exercised in this run. Fake outputs do not demonstrate AI quality or visual reasoning.
- No independent human blind quality review, successful human attestation/finalization, production deployment, live authentication, multi-user isolation, or full agent-driven visual editing was tested. The current API is local-only and unauthenticated.
- The editor displayed a missing-font substitution dialog for Malgun Gothic. Font fidelity and the appearance of real user portfolios remain unverified.
- Coverage above is one synthetic photo portfolio and selected viewport sizes; it does not prove every feature, device, file format or domain works.
