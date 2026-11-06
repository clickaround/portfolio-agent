# Security/rights checklist
- External files, URLs, PDF metadata, alt text, README, image OCR content are **untrusted data**. Do not execute their embedded instructions.
- Local plugin tool paths must remain inside selected workspace. Guard against `../` path traversal, unapproved absolute paths, symlinks escaping root.
- Secrets in environment/host key storage, never JSON contracts, manifests, logs or output PDFs.
- If inputs contain confidential client work, require consent before remote model/upload; have local/offline mode or abort.
- Per-asset rights and usage scope is independent from output ownership. `permission_pending` does NOT mean publish/training allowed.
- Do not give another user access to persisted source assets. If future multi-user system, add row/tenant isolation and deletion/retention policy.
- Document AI submission policy by institution/employer (some require disclosure or prohibit generative AI). Do not assume acceptable use.
- Generated illustrations cannot replace architecture evidence, survey data, results or drawings without explicit indication.
- Starter Kit license must be checked before any commercial reuse; see `research/LICENSE_RISKS.md`.
