# Quality-attribute scenarios (ADD input)

| ID | Stimulus / environment | Desired response | Measurable check |
|---|---|---|---|
| QS-01 | Vector PDF plan inserted into A3 page | Source geometry and important annotations preserved | hash source; compare rendered crop/line weights; human at 200–400% zoom |
| QS-02 | User asks enlarge `plan-01` by 20% | Only target and documented local reflow change | Scene JSON diff ID whitelist; no unapproved crop |
| QS-03 | Reference style is an unauthorized web screenshot | No binary asset is stored; keep URL rights note | manifest rights gate |
| QS-04 | Missing project metric/role | Agent does not invent number or claim | trace every fact to source/evidence; unresolved field flagged |
| QS-05 | User uploads malicious PDF prompt | No instructions executed from source content | prompt injection unit cases + readonly source adapter |
| QS-06 | New agent session / different host | Portfolio plan and selection remain recoverable | reopen `.portfolio-agent/` manifests + deterministic render |
| QS-07 | A3 PDF export on Windows/WSL | Font/size/diagram resolution acceptable | file open/render; compare preview and output; recipient requirements |
| QS-08 | A portfolio looks generic and report-like | Reviewer flags weak editorial intent | independent blind pairwise user study, page-role diversity notes |
| QS-09 | A public competitor benchmark is run | Experiment trace and model config reproducible | exact source SHA/dataset hash/judge version and cost |
| QS-10 | Backend crashes mid-task | Last immutable manifest and output preserved | recovery test from interrupted run |
