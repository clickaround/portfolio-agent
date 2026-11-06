# T210 evidence — third-party license gate (header-based; CODE_INSPECTED, not legal advice)

| repo | license | gate |
|---|---|---|
| harnessrouter | Apache-2.0 | ALLOW_EXEC_ISOLATED |
| harnessrouter-starter | MIT | ALLOW_EXEC_ISOLATED |
| designcraft | Apache-2.0 | ALLOW_EXEC_ISOLATED |
| photocraft | Apache-2.0 | ALLOW_EXEC_ISOLATED |
| vectorcraft | Apache-2.0 | ALLOW_EXEC_ISOLATED |
| figcraft | Apache-2.0 | ALLOW_EXEC_ISOLATED |
| pdfcraft | Apache-2.0 | ALLOW_EXEC_ISOLATED |
| deckcraft | Apache-2.0 | ALLOW_EXEC_ISOLATED |
| openpencil | MIT | ALLOW_EXEC_ISOLATED |
| genoffice | Apache-2.0 | ALLOW_EXEC_ISOLATED |
| diagram-design | MIT | ALLOW_EXEC_ISOLATED |
| autodesign | MIT | ALLOW_EXEC_ISOLATED |
| deepslides | MIT | ALLOW_EXEC_ISOLATED |
| paper2poster | NO_LICENSE_FILE | READ_ONLY; no code reuse or redistribution without grant |
| gdb | Apache-2.0 | ALLOW_EXEC_ISOLATED |
| slidesgen-bench | NO_LICENSE_FILE | READ_ONLY; no code reuse or redistribution without grant |
| deckbench | NO_LICENSE_FILE | READ_ONLY; no code reuse or redistribution without grant |
| editable-design | Apache-2.0 | ALLOW_EXEC_ISOLATED |
| frontend-slides-editable | MIT | ALLOW_EXEC_ISOLATED |
| html-to-editable-pptx | MIT | ALLOW_EXEC_ISOLATED |
| penpot | MPL-2.0 | ALLOW_EXEC_ISOLATED (file-level copyleft; no vendoring) |
| pagedjs | MIT | ALLOW_EXEC_ISOLATED |
| vivliostyle | AGPL-3.0 | READ_ONLY / separate-process only; never bundle or link |
| fabric | MIT | ALLOW_EXEC_ISOLATED |
| graphite | Apache-2.0 | ALLOW_EXEC_ISOLATED |
| scribus | GPL-2.0 | READ_ONLY / separate-process only; never bundle |
| anthropic-plugins | Apache-2.0 | ALLOW_EXEC_ISOLATED |

Rules: execution only inside .cache/vendor, no dependency install before the per-task safety review; no repo code or assets copied into the plugin unless gate=ALLOW and attribution recorded. Slides Starter Kit (harnessrouter-starter, MIT in repo) has separate commercial terms per AGENTS.md -> treat as MANUAL_REVIEW before any commercial use.
Negative check: audit_repos.py reports NO_LICENSE_FILE for paper2poster/slidesgen-bench/deckbench (verified present in table).
