# Agent workspace generation — synthetic end-to-end

Date: 2026-11-09. Status: **REPRODUCED with a fake plan runner**, not a real Claude model or design-quality validation.

## Setup and scope

- Separate local API on `127.0.0.1:18083` with isolated data under `.cache/harness-e2e-20261109/data`; browser frontend on `127.0.0.1:15176`.
- Six bundled synthetic `photo_01` images uploaded through the new workspace. A deterministic fake runner wrote the plan; the existing actual portfolio pipeline, local exporter, DesignCraft CLI and browser WASM editor executed normally.
- The live Claude account reported weekly quota exhaustion earlier. No real-model answer or aesthetic advantage is asserted here.

## Results

1. With an empty editor, the DesignCraft iframe was visible before generation. Browser uploaded six files and submitted the request. Job completed; the exact `01` attempt contained `book.designcraft`; the workspace navigated to its editor and retained the request in the visible chat.
2. The live editor's `document.inspect` reported five pages. Desktop viewport 1440×900: sidebar 240 px, editor iframe x=616, y=0, width=824, height=900; no outer 12 px gap. Mobile viewport 390×844: after choosing 편집기, iframe and canvas were 390 px wide and filled the available height below navigation.
3. With a separately opened synthetic document containing an unsaved text edit, generation completed without replacing the document. Cancelling the result-open confirmation retained the dirty document and the synthetic text. Accepting the confirmation opened the new result and its five pages.
4. The empty-document bridge error includes the command name and ends in `no document open`. Previous exact-string matching misclassified it; regression test covers the real error message.
5. A failed model runner that wrote a temporary file no longer promotes that file as a successful plan; a quota failure stops after one attempt and reports the limit.

## Artifacts

- `demo4/out/attempts/01/book.designcraft`: SHA-256 `8afe71e2fcfa2700a19a1aeabc22b7b4b5a8b238f8c7e0631cda9d164b2bd925`
- `demo4/out/attempts/01/book.pdf`: SHA-256 `7a605b2420db812a691298079c9113528e3ef72676b4a959d2d61ccad114ae1b`
- `.cache/harness-e2e-20261109/final-editor.png`: SHA-256 `67491554704cfbe794c33682f1050c32fab098c8b3f56e0b869176cb8f881499`

## Remaining

Actual Claude plan generation was not re-run because its weekly quota was exhausted. The agent cannot yet see rendered images, autonomously edit existing objects, verify visual changes or provide a full multi-agent harness. Login does not authorize or isolate the local API. The DesignCraft export remains unverified until a person reviews the actual output.
