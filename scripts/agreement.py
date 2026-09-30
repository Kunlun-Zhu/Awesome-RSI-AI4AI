#!/usr/bin/env python3
"""Closure-coding agreement check: draw a stratified sample, then score a second coder against the stored codes.

    python scripts/agreement.py sample     # writes data/agreement/items.csv (no codes) and stored_codes.csv
    python scripts/agreement.py score      # compares data/agreement/coder2.csv with stored_codes.csv

The sample is stratified by the top-level part of data/taxonomy.yaml. Each part receives a share of the 60 items
proportional to the square root of its size (largest remainders), so that small parts such as RSI in agents are not
left with one or two items, and items are drawn within each part with a fixed seed. items.csv holds only what the
second coder may see: short name, title, venue, date, and note. stored_codes.csv keeps the codes as they stood when
the sample was drawn, so the comparison stays reproducible after corrections are applied to papers.yaml.

Codes are compared on the closure class (none, parametric, procedural, pipeline, na; a set with any procedural
member is procedural) and, as a stricter statistic, on the exact closure value.
"""
import argparse
import collections
import csv
import math
import pathlib
import random

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "agreement"
SEED = 20260930
SIZE = 60
CLASSES = ("none", "parametric", "procedural", "pipeline", "na")


def closure_class(value):
    value = str(value).strip()
    if value in ("none", "pipeline", "na"):
        return value
    if value.endswith("proc"):
        return "procedural"
    if value.endswith("param"):
        return "parametric"
    raise ValueError(f"unknown closure {value!r}")


def allocate(sizes, total):
    """Largest-remainder allocation of `total` proportional to sqrt(size)."""
    weights = {k: math.sqrt(n) for k, n in sizes.items()}
    scale = total / sum(weights.values())
    raw = {k: w * scale for k, w in weights.items()}
    alloc = {k: int(v) for k, v in raw.items()}
    for k in sorted(raw, key=lambda k: raw[k] - alloc[k], reverse=True)[: total - sum(alloc.values())]:
        alloc[k] += 1
    return alloc


def sample():
    taxonomy = yaml.safe_load((ROOT / "data" / "taxonomy.yaml").read_text())
    papers = yaml.safe_load((ROOT / "data" / "papers.yaml").read_text())
    part_of = {c["id"]: top["id"] for top in taxonomy for c in top.get("children", [])}
    by_part = collections.defaultdict(list)
    for p in papers:
        by_part[part_of[p["section"]]].append(p)
    alloc = allocate({k: len(v) for k, v in by_part.items()}, SIZE)
    rng = random.Random(SEED)
    chosen = []
    for top in taxonomy:  # fixed order, so the draw depends only on the seed and the data
        pool = sorted(by_part[top["id"]], key=lambda p: p["key"])
        chosen += [(top["id"], p) for p in rng.sample(pool, alloc[top["id"]])]
    rng.shuffle(chosen)  # present items in random order, not grouped by part
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "items.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["item", "short", "title", "venue", "date", "note"])
        for i, (_, p) in enumerate(chosen, 1):
            w.writerow([i, p.get("short", ""), p["title"], p.get("venue", ""), p.get("date", ""), p.get("note", "")])
    with open(OUT / "stored_codes.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["item", "key", "part", "section", "closure"])
        for i, (part, p) in enumerate(chosen, 1):
            w.writerow([i, p["key"], part, p["section"], p["closure"]])
    print("allocation:", alloc)
    print(f"wrote {OUT / 'items.csv'} and {OUT / 'stored_codes.csv'} ({len(chosen)} items, seed {SEED})")


def kappa(pairs, labels):
    n = len(pairs)
    po = sum(a == b for a, b in pairs) / n
    ca, cb = collections.Counter(a for a, _ in pairs), collections.Counter(b for _, b in pairs)
    pe = sum(ca[l] * cb[l] for l in labels) / n ** 2
    return po, (po - pe) / (1 - pe) if pe < 1 else float("nan")


def score():
    stored = {r["item"]: r for r in csv.DictReader(open(OUT / "stored_codes.csv"))}
    second = {r["item"]: r for r in csv.DictReader(open(OUT / "coder2.csv"))}
    items = {r["item"]: r for r in csv.DictReader(open(OUT / "items.csv"))}
    missing = set(stored) - set(second)
    if missing:
        raise SystemExit(f"coder2.csv lacks items {sorted(missing, key=int)}")
    pairs = [(closure_class(stored[i]["closure"]), closure_class(second[i]["closure"])) for i in stored]
    po, k = kappa(pairs, CLASSES)
    exact = sum(stored[i]["closure"].strip() == second[i]["closure"].strip() for i in stored)
    print(f"items: {len(pairs)}; class agreement {po:.3f}; Cohen's kappa {k:.3f}; exact closure agreement {exact}/{len(pairs)}")
    loops = [(a, b) for a, b in pairs if a != "na" and b != "na"]
    if loops:
        po2, k2 = kappa(loops, CLASSES[:4])
        print(f"items both coders treat as loops: {len(loops)}; agreement {po2:.3f}; kappa {k2:.3f}")
    recur = [(a != "none", b != "none") for a, b in loops]
    if recur:
        po3, k3 = kappa(recur, (True, False))
        print(f"recursive (nonempty) vs empty among those loops: agreement {po3:.3f}; kappa {k3:.3f}")
    print("confusion (rows: stored code, columns: second coder):")
    conf = collections.Counter(pairs)
    print("            " + " ".join(f"{c[:10]:>10}" for c in CLASSES))
    for a in CLASSES:
        print(f"{a:>11} " + " ".join(f"{conf[(a, b)]:>10}" for b in CLASSES))
    print("disagreements:")
    for i in sorted(stored, key=int):
        if stored[i]["closure"].strip() != second[i]["closure"].strip():
            print(f"  {i:>2} {stored[i]['key']}: stored {stored[i]['closure']!r}, second {second[i]['closure']!r}"
                  f" | {items[i]['short']} | {second[i].get('rationale', '')}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=("sample", "score"))
    args = ap.parse_args()
    sample() if args.step == "sample" else score()


if __name__ == "__main__":
    main()
