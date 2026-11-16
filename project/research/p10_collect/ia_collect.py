"""Collect portfolio PDFs from the Internet Archive through its public search and metadata APIs, licence recorded per item.

  ia_collect.py list OUT_DIR             search -> OUT_DIR/manifest.jsonl (identifier, title, creator, licence, pdf name, bytes, use)
  ia_collect.py fetch OUT_DIR [MAX_MB]   download the PDFs whose licence allows commercial reuse (use == "train"), one at a time

Only items that carry a Creative Commons / public-domain licence URL are listed. `use`:
  train     CC BY, CC BY-SA, CC0, public domain mark: may go into a training set, attribution kept in the manifest
  look      NC and / or ND licences: listed, not downloaded
Nothing is taken from sites that block automated access. One request per second.
"""
import hashlib
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

UA = {"User-Agent": "research-collector/0.1 (licence-recorded; 1 req/s)"}
QUERY = ('mediatype:texts AND licenseurl:*creativecommons* AND (title:portfolio OR subject:portfolio) AND '
         '(architecture OR architectural OR design OR designer OR graphic OR interior OR landscape OR illustration OR photography OR art OR ux OR urban)')


def get(url, binary=False):
    time.sleep(1)
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
        data = r.read()
    return data if binary else json.loads(data)


def use_of(lic):
    lic = (lic or "").lower()
    if "/by-nc" in lic or "-nd" in lic or "/nc" in lic:
        return "look"
    if "/licenses/by/" in lic or "/licenses/by-sa/" in lic or "publicdomain" in lic:
        return "train"
    return "look"


def listing(out):
    out.mkdir(parents=True, exist_ok=True)
    rows, page = [], 1
    while True:
        q = urllib.parse.urlencode({"q": QUERY, "fl[]": ["identifier", "title", "creator", "licenseurl", "year"], "rows": 100, "page": page, "output": "json"}, doseq=True)
        docs = get("https://archive.org/advancedsearch.php?" + q)["response"]["docs"]
        if not docs:
            break
        rows += docs
        page += 1
    with open(out / "manifest.jsonl", "w", encoding="utf-8") as f:
        for d in rows:
            files = get("https://archive.org/metadata/" + urllib.parse.quote(d["identifier"])).get("files", [])
            pdfs = [x for x in files if x.get("name", "").lower().endswith(".pdf") and x.get("source") == "original"] or \
                   [x for x in files if x.get("name", "").lower().endswith(".pdf")]
            pdf = max(pdfs, key=lambda x: int(x.get("size", 0)), default=None)
            row = {"source": "archive.org", "identifier": d["identifier"], "title": d.get("title"), "creator": d.get("creator"), "year": d.get("year"),
                   "licence": d.get("licenseurl"), "use": use_of(d.get("licenseurl")), "pdf": pdf and pdf["name"], "bytes": pdf and int(pdf.get("size", 0)),
                   "url": pdf and f"https://archive.org/download/{d['identifier']}/{urllib.parse.quote(pdf['name'])}"}
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            f.flush()
    print("listed", len(rows))


def fetch(out, max_mb):
    rows = [json.loads(x) for x in (out / "manifest.jsonl").read_text(encoding="utf-8").splitlines()]
    (out / "pdf").mkdir(exist_ok=True)
    done = 0
    with open(out / "fetched.jsonl", "a", encoding="utf-8") as log:
        for r in rows:
            if r["use"] != "train" or not r["url"] or r["bytes"] > max_mb * 2**20:
                continue
            dst = out / "pdf" / (r["identifier"] + ".pdf")
            if not dst.is_file():
                try:
                    dst.write_bytes(get(r["url"], binary=True))
                except Exception as ex:   # one missing file must not stop the run
                    print("FAILED", r["identifier"], ex)
                    continue
                log.write(json.dumps({**r, "sha256": hashlib.sha256(dst.read_bytes()).hexdigest()}, ensure_ascii=False) + "\n")
                log.flush()
            done += 1
    print("have", done)


if __name__ == "__main__":
    o = Path(sys.argv[2])
    listing(o) if sys.argv[1] == "list" else fetch(o, float(sys.argv[3]) if len(sys.argv) > 3 else 150)
