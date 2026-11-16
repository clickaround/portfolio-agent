# T1002 evidence — open layout / editing models and data (DOC_REPORTED, nothing run or downloaded)

Date 2026-11-15. Read through a page summariser; numbers are the sources' own claims.

| Item | Link | Licence | What it is | Limit for us |
|---|---|---|---|---|
| PosterCopilot | https://huggingface.co/void-2024/PosterCopilot , arXiv 2512.04082 (first 80 % read) | Apache-2.0 | Qwen2.5-VL-7B; layers + canvas in, box + order JSON out; 160K PSD posters; SFT then GRPO with rule rewards then an aesthetic reward | single poster; about 20 GB VRAM |
| LICA | https://github.com/purvanshi-lica/lica-dataset , arXiv 2603.16098 | README: CC BY 4.0 (LICENSE text not read) | 1.55M layered designs, per-element style JSON + PNG | mostly posts and presentations, no multi-page books; zip is 985 MB by HEAD request |
| OmniDocLayout | https://github.com/opendatalab/OmniDocLayout , https://huggingface.co/datasets/khr0516/OmniDocLayout-1M , arXiv 2510.26213 | none stated: read-only | Qwen2.5-0.5B; 1M pages incl. magazine; broad stage then a few hundred to 2,000 samples per domain | boxes and categories only; no weights linked |
| FLOORA | https://github.com/AutodeskAILab/floora , arXiv 2609.36064 (first half read) | Apache-2.0 | floor plans; small existing weights + DSL + preference reward model + rule rewards | a recipe, not a layout model for pages |
| Figma edit model | https://www.figma.com/blog/training-a-figma-fluent-editing-model/ | closed | own canvas-edit model; teacher-model edits filtered by validators and visual judges; 250K+ examples for the first version | shows the data route, not reusable |
| Small models for agents | arXiv 2506.02153 (position paper), arXiv 2512.15943 | — | log agent calls, 10k-100k examples, LoRA a small model | conversation and planning stay with a large model |

Findings
- No portfolio-specialist or multi-page layout model was found.
- MoE is an architecture chosen when a model is built; the reachable form is existing small weights + LoRA, one adapter per domain.
- Real portfolio layout data in hand on 2026-11-15: two private case PDFs under `C:/DK/real_sources/cases_private`; the other 16 PDFs there
  are our own engine output and would only teach a model our rules.
- This machine: RTX 5080 Laptop, 16 GB VRAM (`nvidia-smi`).

## Data search, 2026-11-15 night (search results and dataset cards, DOC_REPORTED; nothing downloaded except the LICA sample)

No dataset of portfolio layouts was found (searched: architecture / design portfolio, Issuu, Behance, multi-page design, magazine, deck).

| Data | Link | Size | Licence as stated | Use for us |
|---|---|---|---|---|
| LICA sample | https://huggingface.co/datasets/purvanshi/lica-data | 1,148 layouts (the zip we hold) | CC BY 4.0 | format check; full 1.55M set has no public download found |
| Crello | https://huggingface.co/datasets/cyberagent/crello | about 23K templates | CDLA-Permissive-2.0, plus VistaCreate terms for the template content | general layout sense; single pages |
| Zenodo10K (PPTAgent, arXiv 2501.03936) | https://huggingface.co/datasets/Forceless/Zenodo10K | about 10K decks | "other": each deck keeps its own licence | the only multi-page set; filter by per-file licence |
| DocLayNet | https://huggingface.co/datasets/docling-project/DocLayNet-v1.1 | 80,863 pages | CDLA-Permissive-1.0 | reports and manuals, not design; useful to train or check a box extractor |
| Magazine (Zheng 2019) | https://huggingface.co/datasets/creative-graphic-design/Magazine | 3,919 pages | unknown; loader says non-commercial research; pages are commercial magazines | closest in look, not usable for a paid product |
| OmniDocLayout-1M | https://huggingface.co/datasets/khr0516/OmniDocLayout-1M | 1M pages incl. magazine | none stated | read-only |
| BAM (Behance) | arXiv 1704.08614 | 65M images | not confirmed | images with style tags, no layouts |
| Issuu / Behance portfolios | — | very many | each owner's copyright | not without permission; no mass scraping |
| University thesis repositories (OAI-PMH) | — | unknown | per thesis, some Creative Commons | possible source of design thesis books with a licence; not searched by school yet |

Reading: the portfolio part has to be built by us. Routes that respect rights: (1) the owner's own portfolios and ones given with consent, (2) Creative Commons thesis / project books found one by one with the licence recorded, (3) decks from Zenodo10K filtered by licence as the multi-page stand-in, (4) later, pages made in the product by users who agree. A PDF -> boxes extractor (T1011) is needed for 1 and 2.

Order recommended to the owner: connect the editor and keep Claude for conversation and editing; collect portfolio layout records (T1011)
and general data (T1008); try existing weights as they are (T1009); fine-tune (T1013) and judge by rendered pages.
