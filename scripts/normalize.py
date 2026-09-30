#!/usr/bin/env python3
"""Clean data/papers.yaml using verification results.

1. Where verification found the same paper under its official title (status check or mismatch,
   but the official title is contained in ours or matches after removing our annotations),
   adopt the official title and author list.
2. Re-key entries whose key starts with "anon" using the verified first author.
3. Merge duplicates that share an arXiv ID or a normalized official title.

    python scripts/normalize.py [--dry-run]
Run scripts/verify.py afterwards; changed titles are re-verified automatically.
"""
import argparse
import json
import pathlib
import re
import unicodedata

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAPERS = ROOT / "data" / "papers.yaml"
CACHE = ROOT / "data" / "verification.json"
STOP = {"a", "an", "the", "on", "of", "for", "to", "in", "and", "with", "via", "is", "are", "do", "does",
        "can", "towards", "toward", "from", "at", "by", "we", "what", "when", "how", "why", "your", "our"}


def fold(s):
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()


def norm(t):
    return re.sub(r"[^a-z0-9]+", " ", fold(t).lower()).strip()


def strip_annotations(t):
    t = re.sub(r"\s*\((?:originally|earlier title|arXiv|arXiv version|retitled|follow-up|PhD thesis|[A-Z][a-z]+ et al\.)[^)]*\)", "", t)
    return t.split(" / ")[0].split("; ")[0].strip(' "')


def same_paper(ours, found):
    a, b = norm(strip_annotations(ours)), norm(found)
    if not a or not b:
        return False
    expand = lambda s: s.replace("llms", "large language models").replace("llm", "large language model").replace(
        " rl ", " reinforcement learning ").replace("asi", "artificial super intelligence")
    return a in b or b in a or expand(a) == expand(b) or expand(a) in expand(b) or norm(ours).startswith(b)


def key_for(p, authors):
    last = re.sub(r"[^a-z]", "", fold(authors[0].split()[-1]).lower()) if authors else "anon"
    year = re.search(r"(?:19|20)\d\d", p.get("venue", "") or "") or re.search(r"(?:19|20)\d\d", str(p.get("date", "")))
    word = next((w.lower() for w in re.findall(r"[A-Za-z0-9]+", fold(p["title"])) if w.lower() not in STOP), "paper")
    return f"{last}{year.group(0) if year else '0000'}{word}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    papers = yaml.safe_load(PAPERS.read_text())
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    keys = {p["key"] for p in papers}
    renamed = {}

    for p in papers:
        v = cache.get(p["key"], {})
        if v.get("status") in ("check", "mismatch") and v.get("title") and same_paper(p["title"], v["title"]):
            print(f"title  {p['key']}: {p['title'][:60]!r} -> {v['title'][:60]!r}")
            p["title"] = v["title"]
            if v.get("authors"):
                p["authors"] = ", ".join(v["authors"])
        if p["key"].startswith("anon") and v.get("authors"):
            new = key_for(p, v["authors"])
            base, n = new, 0
            while new in keys:
                n += 1
                new = f"{base}{chr(ord('a') + n - 1)}"
            print(f"rekey  {p['key']} -> {new}")
            keys.discard(p["key"])
            keys.add(new)
            renamed[p["key"]] = new
            p["key"] = new

    merged, seen = [], {}
    for p in papers:
        ids = [("arxiv", p["arxiv"])] if p.get("arxiv") else []
        ids.append(("title", norm(p["title"])))
        hit = next((seen[i] for i in ids if i in seen), None)
        if hit is not None:
            keep = merged[hit]
            print(f"merge  {p['key']} into {keep['key']}")
            for field in ("code", "arxiv", "venue", "note", "short"):
                if not keep.get(field) and p.get(field):
                    keep[field] = p[field]
            renamed[p["key"]] = keep["key"]
            continue
        for i in ids:
            seen[i] = len(merged)
        merged.append(p)

    print(f"{len(papers)} -> {len(merged)} entries; {len(renamed)} keys renamed or merged")
    if not args.dry_run:
        PAPERS.write_text(yaml.safe_dump(merged, sort_keys=False, allow_unicode=True, width=120))
        (ROOT / "data" / "key_renames.json").write_text(json.dumps(renamed, indent=1))


if __name__ == "__main__":
    main()
