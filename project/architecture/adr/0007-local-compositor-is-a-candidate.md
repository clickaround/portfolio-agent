# ADR-0007 — Local compositor (`runtime/portfolio_agent`) is candidate D, not the chosen architecture

Status: PROPOSED (not frozen; P04 spikes and the P05 freeze are pending). Date: 2026-11-04.

## Context
`ARCHITECTURE.md` lists A (agent HTML/CSS), B (OpenPencil native), C (GenOffice/PPTX), D (source-PDF compositing). A deterministic local compositor was built first (PyMuPDF; PDF assets stay vector; PPTX export; scene JSON as editable source; hard gates; local-edit proof). It deviates from the planned order (P04 before P06) and from "DesignDirector emits tokens, not pixel coordinates".

## Decision
Keep it as the verified fallback/baseline backend (`LayoutAdapter` = local) and as the deterministic gate/edit harness. Do NOT claim it as the winner. The DesignDirector (the host agent) should drive it with style tokens and composition constraints, generate at least 3 candidates, then an independent critic (`knowledge/editorial/critic-rubric.md`) ranks them.

## Open items
- Compare with OpenPencil / GenOffice / DesignCraft / agent-HTML under T206, T207, T212, T404.
- PyMuPDF is AGPL-3.0: user-installed dependency only; replace before redistributing a bundle.
- Layout search adapted in idea from Paper2Poster (MIT) `tree_split_layout.py`; independent re-implementation, no learned regression, no training.

## Consequences
All benchmark numbers so far compare only this backend's ablations on synthetic fixtures.
