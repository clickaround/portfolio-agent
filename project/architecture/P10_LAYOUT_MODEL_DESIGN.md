# Portfolio layout model — design (draft 2, 2026-11-16)

Status: design only. Nothing below has been trained. Evidence labels as in `project/AGENTS.md`.
Owner's decisions this rests on: start from the poster-trained weights (option B), train on a rented pod, output a DSL instead of JSON,
fill the data with synthetic pages, and finish the design before any run.

Draft 2 replaces draft 1 after both source papers were read to the end, appendices included (draft 1 was written from the first half of
FLOORA and about 80 % of PosterCopilot). What changed is marked **[new]**.

## 0. What was read (DOC_REPORTED, 2026-11-16)
- FLOORA, arXiv 2609.36064: sections 1-9 and appendices A-I. Numbers below come from the text and tables; the figures (7, 8, 35) were
  not seen, so results that exist only as plots are not quoted.
- PosterCopilot, arXiv 2512.04082: sections 1-14. Section 14 (dataset) is mostly one example file, not a description of the rules.
- Both were read through a page-to-text fetch in four passes, not from the PDF. A number here should be checked against the PDF before
  it is used as a setting.

## 1. Problem
Input: the content of one page (pictures, drawings, text blocks with their real type) and the page size.
Output: where each element goes. Later: the whole book (which content on which page, in what order).
The model proposes; the gates decide. It is one part beside the conversation agent, never the thing the user talks to.

Success is judged on rendered pages, side by side with (a) today's rule layout and (b) a Claude layout, on books the model never saw.

## 2. What we measured before designing (REPRODUCED 2026-11-15)
- PosterCopilot (Qwen2.5-VL-7B) runs on the laptop in 8-bit (8.8 GiB) and reproduces its own examples.
- On our pages it composes posters: one picture stretched over the page, text layers scaled out of shape, captions detached
  (`evidence/P10-postercopilot-proposer.md`). So its sense of balance is reusable; its idea of a page is not.
- Consequence: its own output must not be used as synthetic portfolio data. It would teach posters back.

## 3. What the two papers actually did **[new]**
| | FLOORA | PosterCopilot |
|---|---|---|
| Model | Qwen3 0.6B / 1.7B, text only, all weights updated | Qwen2.5-VL-7B; the paper does not say adapters or full |
| Before fine-tuning | pre-trained on 4.1M synthetic layouts (82M after rotation, 17.6B tokens), up to 200k steps | 160K real PSD posters, 3 epochs |
| Tokenizer | own DSL vocabulary of 1,367 tokens; sequence 54 % shorter; +6.5 to 7.2 points pass@5 against the stock tokenizer | stock |
| SFT data | 10.4k layouts that architects corrected by hand (135k after rotation) | the same 160K, with perturbed-box loss terms (sigma 2.5, n 5) |
| Preference data | 4 candidates per prompt, ranked and rated by 10 architects: 90.6k pairs | none; a general image-quality model scores 1K rendered posters |
| Rule reward | geometry (containment, overlap, coverage; geometric mean), function (counts, 95 % of units over 30 m2), length penalty; each in [0,1] with a smooth step | DIoU against the ground-truth layout + size (0.6) + aspect ratio (0.4) + valid JSON; needs a ground truth |
| RL | GRPO, 8 completions per prompt, temperature 1.0, top-p 0.95, KL 0, 5k steps, batch 256 | GRPO, group 8, lr 1e-6, batch 96, 1 epoch on 20K; then group 4, lr 5e-7 on 1K |
| Compute | H100s; 8 GPUs for 55 h for one pre-training run | 8 GPUs |
| Result | 0.6B: 23.8 -> 37.4 (SFT) -> 79.3 (RL) pass@1 on real sites; Claude Opus 4.8 scores 24.7 | aspect distortion 0.699 after SFT, 0.061 after rule RL |

What this means for us:
1. FLOORA is not "small weights + a little fine-tuning". Its base came from millions of synthetic layouts; SFT alone reached 37 %.
   Most of the gain is the RL stage with rule rewards. Our gates are that reward, so T1016 is the centre of the plan, not a side task.
2. SFT on the small real set made the synthetic score fall (90.2 -> 48.7). Every stage must be scored on both the real and the
   synthetic held-out set.
3. Without squashing, the preference reward swamped the rules (geometry 0.85 -> 0.38). Preference reward goes through tanh(r / 3).
4. With little preference data, rules alone were better for the smallest model. We start with rules only.
5. PosterCopilot fixed distorted aspect ratios only in its RL stage. Our DSL removes that failure by construction (section 4).
6. PosterCopilot's RL reward compares with a ground-truth layout. Ours cannot: a portfolio page has many good layouts. We follow
   FLOORA here (rules that need no ground truth).
7. Both used 8 GPUs. One 48 GB card can do SFT on a few thousand pages; RL on a 7B picture model with 8 rollouts per page on one card
   is an open cost question. This is the main reason for the second arm in section 6.

## 4. Output format: page DSL
v1 (exists, `research/p10_train/scene_to_sample.py`):
```
page 297 210
4 label 12 19 64 4
5 title 12 25 134 11
0 image 12 44 99 148
2 caption 12 193 99 5
```
v2 **[new, to build before any data is generated]**:
- units are grid steps, not mm: columns across, baseline rows down (FLOORA quantises to a 10 cm grid and caps coordinates at 1,024);
- pictures and drawings: `x y w` only; h follows from the source aspect ratio;
- text: `x y w` and a type step; h comes from our text measurer;
- fixed line order (reading order) so one layout has one spelling; normalised, then hashed (FLOORA: BLAKE2b) to drop duplicates and
  to keep any layout from sitting on both sides of the split;
- a start and an end marker; output that does not parse scores 0 instead of being dropped.
Tokenizer: stock for the picture model. For the small text model, a DSL vocabulary is only worth it with pre-training at scale; decide
after the first comparison.

## 5. Data
| Set | Source | Role | State |
|---|---|---|---|
| A. real portfolio pages | consented PDFs, licensed books (`research/p10_collect/`) | the taste we want | 2 PDFs; extractor T1011 not built |
| B. skeleton swap | layouts of A with other pictures and text of the same kind and aspect | volume | T1015, needs A |
| C. teacher layouts | Claude writes the DSL for our source sets; kept only if gates pass and a fresh judge scores 4 or more | volume now | not built |
| D. general design | LICA sample (1,148), Crello (not downloaded) | keeps the base model's balance sense | sample only |
| E. corrected pages **[new]** | a page the owner or a user fixed in the editor, saved as the final layout | SFT gold, as FLOORA's architect-edited layouts | needs T1003-T1005 |
| F. ranked candidates **[new]** | 4 layouts of the same content, ranked by the owner; 6 pairs per page | preference reward | not built |
Never in the training set: pages laid out by our rule engine (label `source: engine` in `meta.json`).
Held out before anything is generated: whole books, by project, per domain; split by book and by hash.
Augmentation **[new]**: left-right mirror, and the same layout re-fitted to another page format; both go through the gates again.
Sizes: FLOORA used 4.1M / 10.4k / 90.6k. We will be far below that; targets for the first run are 2,000 pages of C per domain, 200
held-out pages, and as many of E and F as the owner will do (FLOORA saw the first clear gain at 3,000 hand-made samples). HYPOTHESIS.

## 6. Model: two arms **[new]**
Arm 1 (owner's choice, primary): PosterCopilot checkpoint. It sees the layer images. No adapters (owner, 2026-11-16: not LoRA):
the weights of the language model themselves are updated, as in FLOORA ("all parameters are updated"); the vision tower stays frozen.
Memory for that on a 7B model is about 16 GB weights + 16 GB gradients + 32 GB optimizer state in 16-bit, before activations
(HYPOTHESIS, arithmetic only), so one 48 GB card is not enough: an 80 GB card with a memory-saving optimizer, or two cards.
The system prompt and output format are replaced by ours in SFT.
Arm 2 (comparison, cheap): Qwen3 0.6B, text only, all weights updated, as FLOORA. Input is a DSL line per element (kind, aspect
ratio, text length, importance) instead of images. It fits the laptop for SFT, makes 8-rollout RL affordable, and answers in well
under a second.
Both arms train on the same data and are scored on the same held-out pages. The arm that looks better to the owner continues; the
other stops. If arm 1 only wins because it sees the pictures, the picture content goes into arm 2's input as tags from a captioner.

## 7. Training stages
1. SFT on C + D (+ A, B, E when they exist). Loss on the output only. Arm 1 adds the perturbed-box terms (sigma 2.5, n 5).
2. RL with rule rewards (GRPO, 8 completions, temperature 1.0, top-p 0.95). Reward T1016: each gate as a number in [0,1] with a
   smooth step exp(-(e - tau) / tau) past its tolerance; hard gates (inside margins, no unintended overlap, text fits, every source
   used once) combined by geometric mean so one failure pulls the whole score down; soft terms (caption beside its picture, alignment
   to the grid, empty band) added; length penalty; unparseable = 0.
3. RL with preference added: a reward model started from the SFT checkpoint, trained on F with the pairwise loss
   -log sigmoid(r_win - r_lose), frozen, squashed by tanh(r / 3), weight 1 beside the rules. Only when F is large enough; the judge
   record in `engine/live.py` history (accept, undo) is extra pairs, not a replacement.
Stages 1 and 2 can match the teacher; stage 3 is the one that can pass it.

## 8. Evaluation
- pass@1 / 3 / 5: a page passes only if every hard gate passes (FLOORA's measure); on the real and on the synthetic held-out set.
- Pairwise judge on rendered pages, each pair in both orders, disagreement = tie. Before it is trusted, its agreement with the
  owner's own choices is measured on 100 pairs (FLOORA's judge agreed with architects 77.5 %).
- Side-by-side sheets: rule | Claude | arm 1 | arm 2, same content, blind order, looked at by the owner.
- Negative fixtures: one picture and almost no text; eleven captions; a drawing that may not be cropped.
- Seconds per page on the pod and on the laptop.
A run is a failure if the pages look worse than the rule layout to the owner, whatever the numbers say.

## 9. Compute (RunPod list prices read 2026-11-16, availability LOW on most; no pod exists)
| Card | VRAM | $/h community | $/h secure |
|---|---|---|---|
| RTX 5090 | 32 GB | 0.69 | 1.39 |
| L40S | 48 GB | 0.79 | 1.09 |
| A100 80GB | 80 GB | 1.19-1.39 | 2.09-2.19 |
| H100 | 80 GB | 2.59-2.69 | 3.19-4.39 |
First pod run: arm 1 SFT on one A100 80 GB, capped at 8 hours (about 10 to 18 USD) plus storage, pod deleted afterwards. The cap is a
budget, not an estimate. Arm 2 SFT runs on the laptop first. RL for arm 1 is priced only after the SFT run shows seconds per rollout.
No pod is created before the owner sees the price and says yes.

## 10. Order of work
1. DSL v2 + normaliser + hash (section 4). 2. T1016 reward from the gates, checked on known good and known bad pages.
3. Set C generator (Claude -> DSL -> gates -> judge), 100 samples looked at by eye. 4. T1011 extractor, set A from what we have.
5. Held-out split, evaluation sheet, judge agreement check. 6. Arm 2 SFT on the laptop. 7. Arm 1 SFT on a pod. 8. RL stages.

## 11. Risks
- Scale: both papers had 100 to 1,000 times our data. The plan may only reach "as good as Claude with gates" until A, E and F grow.
- The DSL change throws away part of what the poster weights learned about their output; if SFT does not recover it, arm 2 carries on.
- SFT on a small set can make the model worse elsewhere (seen in FLOORA); scored on two held-out sets for that reason.
- Set C is only as good as Claude with gates.
- Few real portfolios (2 today). Mass scraping of sites that block it is out.
- Not known from the papers: PosterCopilot's adapter or full fine-tuning choice, its training hours, its filtering rules.
