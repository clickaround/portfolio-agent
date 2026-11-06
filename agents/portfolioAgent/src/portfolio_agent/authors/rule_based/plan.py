"""BookPlan: assign every asset to a page role following the retrieved pattern, and give every page its editorial content
(section number/name, heading, body, short captions, statement, keywords). Never drops assets silently."""
import re

UNIFORM_HERO_MIN = 0.35  # same floor for every condition so ablations are comparable
CREDIT_SECTIONS = {"role", "roles", "credits", "credit", "team", "year", "collaborators", "contribution", "acknowledgements", "tools", "software", "status", "outcome"}
GENERIC_HEADINGS = {"split": "Concept", "hero": "Feature", "grid": "Studies", "pair": "Studies", "text": "Notes"}
CAP = {"cover": 1, "split": 1, "hero": 1, "grid": 3, "closing": 0}  # split = ONE image + text column (feature)


def first_sentence(text, max_chars=120):
    t = (text or "").strip()
    if not t:
        return ""
    m = re.match(r"(.+?[.!?。])(\s|$)", t)
    s = m.group(1) if m else t
    return s if len(s) <= max_chars else s[:max_chars].rsplit(" ", 1)[0] + "…"


def make_plan(brief, manifest, pattern, page_count=None, page_aspect=297 / 210):
    """Hero/cover pages get the photos whose aspect is closest to the page (they can fill it); the rest go to grids by size."""
    import math
    assets = sorted(manifest["assets"], key=lambda a: -a["width"] * a["height"] if a["role"] == "photo" else 0)
    photos = [a for a in assets if a["role"] == "photo"]
    draws = [a for a in assets if a["role"] == "drawing"]
    diagrams = [a for a in assets if a["role"] == "diagram"]
    pool = {a["id"]: a for a in assets}
    seq = [r for r in pattern["sequence"][:12]]
    fill = lambda a: abs(math.log(a["aspect"] / page_aspect))  # noqa: E731  0 = same shape as the page
    n_full = seq.count("cover") + (seq.count("hero") if not draws else 0)
    full = sorted(photos, key=fill)[:n_full]          # reserved for cover/hero, best page-fillers first
    photos = [a for a in photos if a not in full]
    pages = []
    rest = lambda: full + photos + draws  # noqa: E731
    for role in seq:
        if role == "cover":
            a = full.pop(0) if full else (photos.pop(0) if photos else (draws.pop(0) if draws else None))
            pages.append({"role": "cover", "assets": [a["id"]] if a else []})
        elif role == "closing":
            continue
        elif not rest():
            continue
        elif role == "hero":
            a = draws.pop(0) if draws else (full.pop(0) if full else photos.pop(0))
            pages.append({"role": "hero", "assets": [a["id"]]})
        else:
            n = CAP[role]
            take = [photos.pop(0) for _ in range(min(n, len(photos)))]
            if role == "grid" and len(take) < 2 and draws:
                take.append(draws.pop(0))
            if take:
                pages.append({"role": role, "assets": [a["id"] for a in take]})
    photos = full + photos
    for p in pages:   # a page-shaped photo on a hero page covers the page (real portfolios: full-bleed openers), never a drawing
        if p["role"] == "hero" and pool[p["assets"][0]]["role"] == "photo" and fill(pool[p["assets"][0]]) < 0.25 and not pool[p["assets"][0]].get("cutout"):
            p["bleed"] = "full"
    if diagrams:   # diagrams read as a sequence: one "process" page per 2-4 diagrams, placed right after the concept page
        at = 2 if len(pages) >= 2 else len(pages)
        for i in range(0, len(diagrams), 4):
            pages.insert(at, {"role": "grid", "assets": [a["id"] for a in diagrams[i:i + 4]], "_diagram_row": True})
            at += 1
    while rest():  # overflow assets -> extra grid pages, nothing dropped
        take = [(photos or draws).pop(0) for _ in range(min(3, len(rest())))]
        pages.append({"role": "grid", "assets": [a["id"] for a in take]})

    secs = {k: v for k, v in brief["sections"].items() if v}
    keywords = brief.get("keywords", [])
    # credits-like sections (role, team, year, tools...) are never page headings: they close the book
    tail = [n for n in secs if n.strip().lower() in CREDIT_SECTIONS or len(secs[n]) <= 40 and n.strip().lower().split()[0] in CREDIT_SECTIONS]
    names = [n for n in secs if n not in tail]
    statement = secs[tail[-1]] if tail else (first_sentence(secs[names[0]], 90) if names else "")
    if len(draws_all := [a for a in assets if a["role"] == "drawing"]) >= 4:   # index page: all drawings small, numbered (reader's map of the set)
        pages.append({"role": "grid", "assets": [a["id"] for a in draws_all], "_index": True, "allow_repeat": True})
    if statement or keywords:
        pages.append({"role": "closing", "assets": []})
    if page_count and len(pages) > page_count:
        raise ValueError(f"page_count={page_count} cannot hold {len(manifest['assets'])} assets (needs >= {len(pages)}); refusing silent asset drop")

    # editorial content: sections are walked in order; each content page gets the next section as its heading/body/caption
    sec_i, sec_no = 0, 0
    for i, p in enumerate(pages):
        p["page"] = i + 1
        p["keywords"] = keywords
        if p["role"] == "cover":
            p["title"] = brief["title"]
            p["section"] = ""
            dom, aud = brief.get("domain", ""), brief.get("audience", "")
            p["tagline"] = " · ".join(x for x in (dom.replace("-", " ").title() + " portfolio" if dom else "", aud) if x)
            continue
        if p["role"] == "closing":
            p["title"] = brief["title"]
            p["statement"] = statement
            p["section"] = tail[-1] if tail else "Close"
            p["text"] = " ".join(f"{k}: {v}" for k, v in secs.items() if k != p["section"] and k not in {pg.get("section") for pg in pages})
            p["section_no"] = sec_no + 1
            continue
        sec_no += 1
        p["section_no"] = sec_no
        if p.get("_diagram_row"):          # a diagram sequence is its own page: it never takes a section heading away from the drawings
            p["section"] = p["title"] = "Process"
            p["text"] = ""
            p["caption"] = ""
            p["captions"] = [pool[a].get("title") or f"Diagram {k + 1:02d}" for k, a in enumerate(p["assets"])]
            continue
        if p.get("_index"):                # index of sheets: every drawing as a thumbnail with its number
            p["section"] = p["title"] = "Index of sheets"
            p["text"] = ""
            p["caption"] = ""
            p["captions"] = [f"{k + 1:02d}  {pool[a]['id'].replace('_', ' ')}" for k, a in enumerate(p["assets"])]
            continue
        if sec_i < len(names):
            name, body = names[sec_i], secs[names[sec_i]]
        else:  # sections exhausted: asset-derived heading, numbered so pages never repeat the same word, no body text
            kinds = {pool[a]["role"] for a in p["assets"]}
            base = "Drawings" if kinds == {"drawing"} else ("Process" if kinds == {"diagram"} else GENERIC_HEADINGS.get(p["role"], "Studies"))
            seen = sum(1 for q in pages[:i] if q.get("title", "").startswith(base))
            name, body = (f"{base} {'I II III IV V VI'.split()[min(seen, 5)]}" if seen else base), ""
        sec_i += 1
        p["section"] = name
        p["title"] = name
        if p["role"] in ("split", "text"):
            p["text"] = body
            p["caption"] = ""
        else:
            p["text"] = ""
            a_ids = p["assets"]
            kind_name = {"drawing": "Drawing", "photo": "View", "diagram": "Diagram"}
            if p.get("_diagram_row"):   # a diagram sequence: the section text is the body, each diagram gets a short numbered caption
                p["text"] = body if len(body) <= 300 else first_sentence(body, 300)
                p["caption"] = ""
                p["captions"] = [f"Diagram {k + 1:02d}" for k in range(len(a_ids))]
            else:
                p["caption"] = body if len(body) <= 400 else first_sentence(body, 400)
                p["captions"] = [p["caption"] if (k == 0 and body) else f"{kind_name.get(pool[a]['role'], 'Image')} {k + 1:02d}" for k, a in enumerate(a_ids)]
    return {"doc_title": brief["title"], "pattern_id": pattern["id"], "tokens": pattern.get("tokens", {}), "pages": pages,
            "hero_min_ratio": max(pattern["hero_min_ratio"], UNIFORM_HERO_MIN), "asset_count": len(pool)}
