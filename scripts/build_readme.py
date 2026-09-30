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
SCOPES = ("core-rsi", "core-ai4ai", "support", "background")
NEW_SINCE = "2026-07"  # entries first released on or after this month get a 🆕


def slug(text):
    s = re.sub(r"[^\w\- ]", "", text.lower()).strip()
    return re.sub(r"\s+", "-", s)


def load():
    taxonomy = yaml.safe_load((DATA / "taxonomy.yaml").read_text())
    papers = yaml.safe_load((DATA / "papers.yaml").read_text()) or []
    return taxonomy, papers


def subgroups(leaf):
    """Ordered subgroup ids of a taxonomy leaf; entries without a `subgroup` field belong to the first."""
    return [g["id"] for g in leaf.get("subgroups", [])]


def validate(taxonomy, papers):
    leaves = {c["id"]: c for top in taxonomy for c in top.get("children", [])}
    errors, keys = [], collections.Counter(p["key"] for p in papers)
    for k, n in keys.items():
        if n > 1:
            errors.append(f"duplicate key: {k}")
    for p in papers:
        if p.get("section") not in leaves:
            errors.append(f"{p['key']}: unknown section {p.get('section')!r}")
        elif p.get("subgroup") and p["subgroup"] not in subgroups(leaves[p["section"]]):
            errors.append(f"{p['key']}: subgroup {p['subgroup']!r} is not declared for section {p['section']!r}")
        if p.get("locus", "na") not in LOCUS and p.get("locus", "na") != "na":
            errors.append(f"{p['key']}: unknown locus {p.get('locus')!r}")
        if p.get("signal", "na") not in SIGNAL and p.get("signal", "na") != "na":
            errors.append(f"{p['key']}: unknown signal {p.get('signal')!r}")
        if p.get("scope") not in SCOPES:
            errors.append(f"{p['key']}: missing or unknown scope {p.get('scope')!r}")
        if p.get("recursive", "na") not in ("yes", "partial", "no", "na", True, False):
            errors.append(f"{p['key']}: unknown recursive {p.get('recursive')!r}")
        if p.get("provenance", "primary") not in ("primary", "secondary"):
            errors.append(f"{p['key']}: unknown provenance {p.get('provenance')!r}")
        if p.get("bibtype", "misc") not in ("misc", "book"):
            errors.append(f"{p['key']}: unknown bibtype {p.get('bibtype')!r}")
        for field in ("title", "url", "date"):
            if not p.get(field):
                errors.append(f"{p['key']}: missing {field}")
    # one work, one entry: identifiers may repeat only between a work and its declared companion
    companion = {p["key"]: m.group(1) for p in papers
                 if (m := re.match(r"Companion to (\w+)", str(p.get("note", ""))))}
    seen = {}
    for p in papers:
        url = re.sub(r"^https?://(www\.)?", "", p["url"].rstrip("/")).lower()
        for ident in (("arxiv", p.get("arxiv")), ("doi", str(p.get("doi", "")).lower() or None), ("url", url)):
            if not ident[1]:
                continue
            other = seen.setdefault(ident, p["key"])
            if other != p["key"] and companion.get(p["key"]) != other and companion.get(other) != p["key"]:
                errors.append(f"{p['key']}: same {ident[0]} as {other}; merge them or mark one as a companion")
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
            groups = c.get("subgroups") or [{"id": None, "title": None}]
            for g in groups:
                members = [p for p in items if (p.get("subgroup") or groups[0]["id"]) == g["id"]]
                if not members:
                    continue
                if g["title"]:
                    out += [f"#### {g['title']}", ""]
                out += [entry(p) for p in members]
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
