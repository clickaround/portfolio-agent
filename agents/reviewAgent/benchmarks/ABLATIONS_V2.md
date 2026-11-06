> **ARCHIVED V2; historical validation only.** Current v3 authoritative docs: GOALS.md, PLANS.md, architecture/ARCHITECTURE_MAP.md, formats/, research/repos.lock.json.

# Controlled experiments: never change two factors at once

All experiments per host separately; same project assets, page size, narrative intent, evaluation suite, max attempts and cost budget. Model/backend versions pinned; report cost and token/time variance.

| Arm | Knowledge | Retrieved cases | Backend | QA/repair | What changes |
|---|---|---|---|---|---|
| E0 | none | none | direct HTML | none | host bare capability |
| E1 | domain pack | none | direct HTML | none | value of domain rules |
| E2a | domain pack | none | **chosen same backend** | hard checks | non-case baseline on target tool |
| E2b | domain pack | 2–3 rights-cleared | **same as E2a** | same hard checks | reference effect only |
| E3a | domain pack | same as E2b | same | hard checks only | repair off |
| E3b | domain pack | same as E2b | same | hard checks + 2 repairs | repair effect only |

Separately run `Backend/OpenPencil vs GenOffice vs fallback` with exactly same content/style and QA, and `Claude vs Codex` with their model and harness differences disclosed. Do **not** infer the reference effect from E1 vs E2b because backend differs. Never tune on heldout.

Record model+version, prompts+SHA, input sources+hash, reference candidates+rights, backend command/version, judge model and rubric, human reviewer blinding, attempt count, reflow scope, PDF engine and fonts, wall time, tokens+USD, and all failure/invalid cases.

Primary gates: 0 critical source changes; 0 unapproved cropping; 0 clipped critical content; 0 fabricated project facts. Secondary: human paired preference and edits-to-completion. Small-N results remain exploratory, not product-level efficacy claims.
