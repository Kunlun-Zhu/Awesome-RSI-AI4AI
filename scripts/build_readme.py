#!/usr/bin/env python3
"""Render README.md from data/papers.yaml and data/taxonomy.yaml.

    python scripts/build_readme.py            # writes README.md
    python scripts/build_readme.py --check    # exit 1 if README.md is stale
"""
import argparse
import collections
import datetime
import pathlib
import re
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

LOCUS = {
    "output": "Output",
    "context": "Context/Memory",
    "weights": "Weights",
    "scaffold": "Scaffold/Code",
    "artifact": "ML artifact",
    "pipeline": "Research pipeline",
}
SIGNAL = {
    "self": "Self-judgment",
    "model": "Model judge / RM",
    "execution": "Execution / tests",
    "ground-truth": "Ground truth / rules",
    "human": "Human",
    "benchmark": "Benchmark score",
    "mixed": "Mixed",
}
NEW_SINCE = "2026-07"  # entries first released on or after this month get a 🆕


def slug(text):
    s = re.sub(r"[^\w\- ]", "", text.lower()).strip()
    return re.sub(r"\s+", "-", s)


def load():
    taxonomy = yaml.safe_load((DATA / "taxonomy.yaml").read_text())
    papers = yaml.safe_load((DATA / "papers.yaml").read_text()) or []
    return taxonomy, papers


def validate(taxonomy, papers):
    leaves = {c["id"] for top in taxonomy for c in top.get("children", [])}
    errors, keys = [], collections.Counter(p["key"] for p in papers)
    for k, n in keys.items():
        if n > 1:
            errors.append(f"duplicate key: {k}")
    for p in papers:
        if p.get("section") not in leaves:
            errors.append(f"{p['key']}: unknown section {p.get('section')!r}")
        if p.get("locus", "na") not in LOCUS and p.get("locus", "na") != "na":
            errors.append(f"{p['key']}: unknown locus {p.get('locus')!r}")
        if p.get("signal", "na") not in SIGNAL and p.get("signal", "na") != "na":
            errors.append(f"{p['key']}: unknown signal {p.get('signal')!r}")
        for field in ("title", "url", "date"):
            if not p.get(field):
                errors.append(f"{p['key']}: missing {field}")
    return errors


def short_authors(authors):
    if not authors:
        return ""
    names = [a.strip() for a in authors.split(",") if a.strip()]
    if len(names) == 1 or names[0].endswith("et al."):
        return names[0]
    if len(names) == 2:
        return f"{names[0]} and {names[1]}"
    return f"{names[0]} et al."


def entry(p):
    new = " 🆕" if str(p.get("date", "")) >= NEW_SINCE else ""
    short = (p.get("short") or "").lstrip("? ").strip()
    name = f"**{short}**: " if short else ""
    who = short_authors(p.get("authors", ""))
    venue = p.get("venue", "")
    meta = ", ".join(x for x in (f"*{who}*" if who else "", venue) if x)
    scholarly = ("arxiv.org", "openreview.net", "aclanthology.org", "doi.org", "nature.com", "proceedings",
                 "pmlr", "neurips.cc", "iclr.cc", "icml.cc", "acm.org", "springer", "ieee", "preprints.org")
    label = "Paper" if p.get("arxiv") or any(d in p["url"] for d in scholarly) else "Link"
    links = f"[[{label}]]({p['url']})"
    if p.get("code"):
        links += f" [[Code]]({p['code']})"
    tags = []
    if p.get("locus") in LOCUS:
        tags.append(f"`{LOCUS[p['locus']]}`")
    if p.get("signal") in SIGNAL:
        tags.append(f"`{SIGNAL[p['signal']]}`")
    if p.get("recursive") in ("yes", True):
        tags.append("🔁")
    line = f"- {name}{p['title']}. {meta}. {links}{new}"
    if tags:
        line += " " + " ".join(tags)
    if p.get("note"):
        line += f"<br><sub>{p['note']}</sub>"
    return line


def render(taxonomy, papers):
    by_section = collections.defaultdict(list)
    for p in papers:
        by_section[p["section"]].append(p)
    for items in by_section.values():
        items.sort(key=lambda p: str(p.get("date", "")), reverse=True)

    out = [(ROOT / "templates" / "header.md").read_text().rstrip(), ""]

    recent = sorted((p for p in papers if str(p.get("date", "")) >= NEW_SINCE),
                    key=lambda p: str(p["date"]), reverse=True)
    if recent:
        out += ["## 🆕 Recently added (since " + NEW_SINCE + ")", ""]
        out += [entry(p) for p in recent[:15]]
        out += [""]

    out += ["## Contents", ""]
    for top in taxonomy:
        n = sum(len(by_section[c["id"]]) for c in top.get("children", []))
        if not n:
            continue
        out.append(f"- [{top['title']}](#{slug(top['title'])}) ({n})")
        for c in top.get("children", []):
            if by_section[c["id"]]:
                out.append(f"  - [{c['title']}](#{slug(c['title'])})")
    out.append("")

    for top in taxonomy:
        if not any(by_section[c["id"]] for c in top.get("children", [])):
            continue
        out += [f"## {top['title']}", ""]
        if top.get("blurb"):
            out += [f"*{top['blurb']}*", ""]
        for c in top.get("children", []):
            items = by_section[c["id"]]
            if not items:
                continue
            out += [f"### {c['title']}", ""]
            out += [entry(p) for p in items]
            out.append("")

    out.append((ROOT / "templates" / "footer.md").read_text().rstrip())
    total = len(papers)
    today = datetime.date.today().isoformat()
    text = "\n".join(out) + "\n"
    return text.replace("{{TOTAL}}", str(total)).replace("{{UPDATED}}", today)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    taxonomy, papers = load()
    errors = validate(taxonomy, papers)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        sys.exit(1)
    text = render(taxonomy, papers)
    readme = ROOT / "README.md"
    if args.check:
        old = readme.read_text() if readme.exists() else ""
        strip = lambda s: re.sub(r"\d{4}-\d{2}-\d{2}", "", s)
        sys.exit(0 if strip(old) == strip(text) else 1)
    readme.write_text(text)
    print(f"README.md: {len(papers)} papers")


if __name__ == "__main__":
    main()
