#!/usr/bin/env python3
"""Check every entry in data/papers.yaml against arXiv (for arXiv papers) or OpenAlex (others).

arXiv entries are fetched in batches of 100 from the arXiv API. Other entries are looked up on
OpenAlex by DOI or title search. Titles are compared, and results are cached in
data/verification.json so reruns only query new or changed entries. Lookups that fail because of
rate limits are recorded as "pending" and retried on the next run.

    python scripts/verify.py            # verify new or pending entries
    python scripts/verify.py --all      # re-verify everything
    python scripts/verify.py --report   # print entries that are not status=ok
    python scripts/verify.py --pages    # also fetch the page of every `verify: skip` entry and look for its title

Entries marked `verify: skip` (blog posts, reports, system cards, news) have no database record; their status is
"manual". With --pages, the cache also records whether the URL resolved and whether the page text contains the title.
"""
import argparse
import difflib
import json
import pathlib
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
CACHE = ROOT / "data" / "verification.json"
OPENALEX = "https://api.openalex.org"
ARXIV = "https://export.arxiv.org/api/query"
ATOM = {"a": "http://www.w3.org/2005/Atom"}


class RateLimited(Exception):
    pass


def norm(title):
    return re.sub(r"[^a-z0-9]+", " ", (title or "").lower()).strip()


def similarity(a, b):
    return difflib.SequenceMatcher(None, norm(a), norm(b)).ratio()


def status_for(sim):
    return "ok" if sim >= 0.9 else ("check" if sim >= 0.7 else "mismatch")


def http_get(url, retries=3):
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=30) as resp:
                return resp.read()
        except urllib.error.HTTPError as err:
            if err.code == 404:
                return None
            if err.code in (429, 503):
                if attempt == retries - 1:
                    raise RateLimited(url)
                time.sleep(5 * (attempt + 1))
                continue
            time.sleep(2 ** attempt)
        except (urllib.error.URLError, TimeoutError):
            time.sleep(2 ** attempt)
    return None


def arxiv_batch(ids):
    """Return {arxiv_id: {title, authors, date}} for up to 100 IDs per request."""
    out = {}
    ids = sorted(set(ids))
    for i in range(0, len(ids), 100):
        chunk = ids[i:i + 100]
        url = f"{ARXIV}?id_list={','.join(chunk)}&max_results={len(chunk)}"
        body = http_get(url)
        if body:
            root = ET.fromstring(body)
            for e in root.findall("a:entry", ATOM):
                eid = e.find("a:id", ATOM).text.rsplit("/abs/", 1)[-1]
                eid = re.sub(r"v\d+$", "", eid)
                title = e.find("a:title", ATOM)
                if title is None or not title.text:
                    continue
                out[eid] = {
                    "title": " ".join(title.text.split()),
                    "authors": [a.find("a:name", ATOM).text for a in e.findall("a:author", ATOM)],
                    "date": e.find("a:published", ATOM).text[:10],
                }
        time.sleep(3)  # arXiv asks for at least 3 s between API calls
    return out


def openalex_lookup(title, doi=None, search=True):
    candidates = []
    if doi:
        body = http_get(f"{OPENALEX}/works/doi:{doi}")
        if body:
            candidates.append(("doi", json.loads(body)))
    if not candidates and not search:
        raise RateLimited(title)
    if not candidates:
        q = urllib.parse.quote(title[:250])
        body = http_get(f"{OPENALEX}/works?search={q}&per-page=5")
        for w in (json.loads(body) if body else {}).get("results", []):
            candidates.append(("search", w))
    best, best_sim, how = None, 0.0, None
    for method, w in candidates:
        s = similarity(title, w.get("title"))
        if s > best_sim:
            best, best_sim, how = w, s, method
    if best is None:
        return {"status": "not-found"}
    return {
        "status": status_for(best_sim), "similarity": round(best_sim, 3), "method": how,
        "title": best.get("title"), "year": best.get("publication_year"), "date": best.get("publication_date"),
        "authors": [a["author"]["display_name"] for a in best.get("authorships", [])],
        "openalex": best.get("id"), "doi": best.get("doi"),
    }


_OPENALEX_DOWN = False  # circuit breaker: after one rate limit, stop calling OpenAlex this run


def lookup(p, arxiv_meta=None):
    """Verify one entry. `arxiv_meta` is a prefetched arxiv_batch() result."""
    if p.get("arxiv"):
        meta = (arxiv_meta or {}).get(p["arxiv"])
        if meta is None and arxiv_meta is None:
            meta = arxiv_batch([p["arxiv"]]).get(p["arxiv"])
        if meta is None:
            return {"status": "not-found", "method": "arxiv"}
        sim = similarity(p["title"], meta["title"])
        return {"status": status_for(sim), "similarity": round(sim, 3), "method": "arxiv", **meta}
    global _OPENALEX_DOWN
    try:
        if _OPENALEX_DOWN:  # DOI lookups use a separate endpoint and are still worth trying
            return openalex_lookup(p["title"], p["doi"], search=False) if p.get("doi") else {"status": "pending"}
        return openalex_lookup(p["title"], p.get("doi"))
    except RateLimited:
        _OPENALEX_DOWN = True
        return {"status": "pending"}


def page_check(p):
    """Fetch the entry's URL and report whether it resolves and mentions the title (first eight title words)."""
    req = urllib.request.Request(p["url"], headers={"User-Agent": "Mozilla/5.0 (Macintosh) AppleWebKit/537.36 Chrome/126"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            ctype, body = resp.headers.get("Content-Type", ""), resp.read(3_000_000)
    except urllib.error.HTTPError as err:
        return {"page": f"http-{err.code}"}
    except (urllib.error.URLError, TimeoutError, ValueError) as err:
        return {"page": f"error: {type(err).__name__}"}
    if "pdf" in ctype or body[:5] == b"%PDF-":
        return {"page": "pdf"}
    text = norm(re.sub(r"<[^>]+>", " ", body.decode("utf-8", "ignore")))
    words = norm(re.sub(r"\(.*?\)", "", p["title"])).split()[:8]
    return {"page": "title-found" if " ".join(words) in text else "title-not-found"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--pages", action="store_true")
    args = ap.parse_args()

    papers = yaml.safe_load((ROOT / "data" / "papers.yaml").read_text()) or []
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}

    def stale(p):
        c = cache.get(p["key"])
        return (args.all or c is None or c.get("status") == "pending"
                or c.get("query_title") != p["title"] or c.get("query_arxiv") != p.get("arxiv")
                or c.get("query_doi") != p.get("doi") or ("query_url" in c and c["query_url"] != p["url"])
                or (args.pages and p.get("verify") == "skip" and "page" not in c))

    if not args.report:
        todo = [p for p in papers if stale(p)]
        meta = arxiv_batch([p["arxiv"] for p in todo if p.get("arxiv")])
        for i, p in enumerate(todo, 1):
            if p.get("verify") == "skip":
                r = {"status": "manual", **(page_check(p) if args.pages else {})}
            else:
                r = lookup(p, meta)
                if not p.get("arxiv"):
                    time.sleep(0.2)
            r.update(query_title=p["title"], query_arxiv=p.get("arxiv"), query_doi=p.get("doi"), query_url=p["url"])
            cache[p["key"]] = r
            if r["status"] != "ok":
                print(f"[{i}/{len(todo)}] {r['status']:9s} {p['key']}")
        CACHE.write_text(json.dumps(cache, indent=1, ensure_ascii=False, sort_keys=True))

    counts = {}
    for p in papers:
        s = cache.get(p["key"], {}).get("status", "unverified")
        counts[s] = counts.get(s, 0) + 1
        if args.report and s not in ("ok", "manual"):
            r = cache.get(p["key"], {})
            print(f"{s:9s} {p['key']}: ours={p['title']!r} found={r.get('title')!r} sim={r.get('similarity')}")
    print("summary:", counts)


if __name__ == "__main__":
    main()
