#!/usr/bin/env python3
"""Export data/papers.yaml to BibTeX, using OpenAlex-verified author lists when available.

    python scripts/export_bib.py --out refs.bib
"""
import argparse
import json
import pathlib
import re

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent

CONFERENCES = {
    "ICLR": "International Conference on Learning Representations",
    "NeurIPS": "Advances in Neural Information Processing Systems",
    "ICML": "International Conference on Machine Learning",
    "ACL": "Proceedings of the Annual Meeting of the Association for Computational Linguistics",
    "EMNLP": "Proceedings of the Conference on Empirical Methods in Natural Language Processing",
    "NAACL": "Proceedings of the Conference of the North American Chapter of the Association for Computational Linguistics",
    "EACL": "Proceedings of the Conference of the European Chapter of the Association for Computational Linguistics",
    "COLING": "Proceedings of the International Conference on Computational Linguistics",
    "Findings of ACL": "Findings of the Association for Computational Linguistics: ACL",
    "Findings of EMNLP": "Findings of the Association for Computational Linguistics: EMNLP",
    "Findings of NAACL": "Findings of the Association for Computational Linguistics: NAACL",
    "COLM": "Conference on Language Modeling",
    "AAAI": "Proceedings of the AAAI Conference on Artificial Intelligence",
    "IJCAI": "Proceedings of the International Joint Conference on Artificial Intelligence",
    "CVPR": "Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition",
    "CoRL": "Conference on Robot Learning",
    "AISTATS": "International Conference on Artificial Intelligence and Statistics",
    "KDD": "Proceedings of the ACM SIGKDD Conference on Knowledge Discovery and Data Mining",
    "AGI": "Artificial General Intelligence (AGI Conference)",
    "GECCO": "Proceedings of the Genetic and Evolutionary Computation Conference",
    "STOC": "Proceedings of the ACM Symposium on Theory of Computing",
}
JOURNALS = {
    "TMLR": "Transactions on Machine Learning Research",
    "TACL": "Transactions of the Association for Computational Linguistics",
    "JMLR": "Journal of Machine Learning Research",
    "Nature": "Nature",
    "Science": "Science",
    "ACM Computing Surveys": "ACM Computing Surveys",
    "CSUR": "ACM Computing Surveys",
    "Nature Machine Intelligence": "Nature Machine Intelligence",
    "Frontiers of Computer Science": "Frontiers of Computer Science",
    "PNAS": "Proceedings of the National Academy of Sciences",
    "Frontiers in Psychology": "Frontiers in Psychology",
    "Nat. Mach. Intell.": "Nature Machine Intelligence",
    "PACM HCI": "Proceedings of the ACM on Human-Computer Interaction",
    "Advances in Computers": "Advances in Computers",
}
WORKSHOP_MARKS = ("workshop", "@", "blackboxnlp")

UNICODE_FIX = {"–": "--", "—": "---", "’": "'", "‘": "`", "“": "``", "”": "''", "×": "$\\times$",
               "→": "$\\rightarrow$", "≥": "$\\geq$", "≤": "$\\leq$", "∞": "$\\infty$", "…": "\\ldots{}",
               "≈": "$\\approx$", "²": "$^2$", "³": "$^3$", "ℜ": "$\\Re$", "×": "$\\times$", "⁴": "$^4$",
               "\u2010": "-", "\u2011": "-"}


def tex(s):
    s = re.sub(r"(?<!\\)([&%#_$])", r"\\\1", str(s))  # escape first, then add LaTeX for unicode
    for a, b in UNICODE_FIX.items():
        s = s.replace(a, b)
    return re.sub(r"[^\x00-\x7FÀ-ſ]", "", s)  # drop emoji and other glyphs pdflatex lacks


def split_venue(venue):
    """'ICLR 2025' -> ('ICLR', '2025'); 'Findings of ACL 2024' -> ('Findings of ACL', '2024')."""
    m = re.match(r"^(.*?)[\s,]*((?:19|20)\d\d)\b.*$", venue or "")
    return (m.group(1).strip(), m.group(2)) if m else ((venue or "").strip(), None)


def brace_hyphen(name):
    """Protect hyphenated given names such as 'Huan-ang' from BibTeX's von-part rule."""
    return " ".join("{" + t + "}" if "-" in t and re.search(r"-[a-z]", t) else t for t in name.split())


ORG_WORDS = ("Research", "DeepMind", "Google", "OpenAI", "Anthropic", "Meta", "NVIDIA", "Team", "team", "Institute",
             "Labs", "Project", "Fellows", "IDAIS", "Weco", "Fortune", "Epoch", "Sakana", "Intology", "METR", "Apollo",
             "Microsoft", "Amazon", "University", "Blog", "blog", "AI")


def is_org(name):
    return " " in name and any(w in name.split() for w in ORG_WORDS)


def clean_names(names):
    """Tidy arXiv author metadata: drop tokens without letters (the ':' in 'Nvidia, :'), and rejoin a given name and a
    family name that arXiv split into two single-word authors (e.g. 'Xue', 'Liu' from 'Xue (Steve) Liu')."""
    names = [n.strip() for n in names if re.search(r"[A-Za-z\u00C0-\u017F]", n)]
    out, i = [], 0
    while i < len(names):
        n = names[i]
        if n.lower() == "nvidia":
            out.append("NVIDIA")
        elif len(n.split()) == 1 and i + 1 < len(names) and len(names[i + 1].split()) == 1 and names[i + 1].lower() != "nvidia":
            out.append(n + " " + names[i + 1])
            i += 1
        else:
            out.append(n)
        i += 1
    return out


def authors_field(p, ver):
    # arXiv author lists are used for arXiv-verified entries. Entries with a DOI cite the version of record, whose author
    # order can differ from the preprint, and OpenAlex lists can add middle names, so the curated list wins there.
    use_ver = ver.get("status") == "ok" and ver.get("method") == "arxiv" and ver.get("authors") and not p.get("doi")
    names = clean_names(ver["authors"]) if use_ver else None
    if not names:
        raw = (p.get("authors") or "").strip()
        names = [a.strip().replace(" et al.", "") for a in raw.split(",") if a.strip()]
        names = [n for n in names if n and n != "et al."]
        if raw.endswith("et al."):
            names.append("others")
    if len(names) > 15:
        names = names[:15] + ["others"]
    if len(names) == 1 and is_org(names[0]):
        return "{" + tex(names[0]) + "}"
    return " and ".join(brace_hyphen(tex(n)) for n in names) or "Anonymous"


def url_tex(u):
    return u.replace("%", "\\%").replace("#", "\\#")


def to_bib(p, ver):
    full_venue = p.get("venue", "") or ""
    venue, vyear = split_venue(full_venue)
    year = vyear or str(p.get("date", ""))[:4] or str(ver.get("year", ""))
    fields = {"title": "{" + tex(p["title"]) + "}", "author": authors_field(p, ver), "year": year}
    if p.get("bibtype") == "book":
        kind = "book"
        fields["publisher"] = tex(p.get("publisher") or venue)
        if p.get("isbn"):
            fields["isbn"] = p["isbn"]
    elif p.get("bibtype") == "misc" or not venue or venue.lower().startswith(("arxiv", "preprint")):
        if p.get("arxiv"):
            kind = "article"
            fields["journal"] = f"arXiv preprint arXiv:{p['arxiv']}"
        else:
            kind = "misc"
            fields["howpublished"] = "\\url{" + url_tex(p["url"]) + "}"
            if p.get("org"):
                fields["note"] = tex(p["org"])
    elif any(m in full_venue.lower() for m in WORKSHOP_MARKS):
        kind = "inproceedings"
        fields["booktitle"] = tex(full_venue)
    elif venue in JOURNALS:
        kind = "article"
        fields["journal"] = JOURNALS[venue]
    elif venue in CONFERENCES or venue.split()[0] in CONFERENCES:
        kind = "inproceedings"
        fields["booktitle"] = CONFERENCES.get(venue) or CONFERENCES[venue.split()[0]]
        if "workshop" in venue.lower():
            fields["booktitle"] = tex(venue) + (f" ({vyear})" if vyear else "")
    elif "workshop" in venue.lower():
        kind = "inproceedings"
        fields["booktitle"] = tex(venue)
    elif p.get("arxiv") or re.search(r"Journal|Transactions|Review|Letters|Computing|Access|Intelligence Research|Minds and Machines|Studies", venue):
        kind = "article"
        fields["journal"] = tex(venue)
    else:  # reports, system cards, blog posts, and other web documents
        kind = "misc"
        fields["howpublished"] = "\\url{" + url_tex(p["url"]) + "}"
        fields["note"] = tex(venue + (f" ({vyear})" if vyear and vyear not in venue else ""))
    if p.get("arxiv") and "journal" not in fields:
        fields["eprint"] = p["arxiv"]
        fields["archivePrefix"] = "arXiv"
    for extra in ("volume", "pages"):
        if p.get(extra):
            fields[extra] = str(p[extra]).replace("-", "--")
    if p.get("doi"):
        fields["doi"] = p["doi"]
    fields["url"] = url_tex(p["url"])
    body = ",\n".join(f"  {k:<12} = {{{v}}}" if k != "title" else f"  {k:<12} = {v}" for k, v in fields.items())
    return f"@{kind}{{{p['key']},\n{body}\n}}\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "rsi-ai4ai.bib"))
    ap.add_argument("--verified-only", action="store_true")
    args = ap.parse_args()
    papers = yaml.safe_load((ROOT / "data" / "papers.yaml").read_text()) or []
    cache_path = ROOT / "data" / "verification.json"
    cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    out = []
    for p in sorted(papers, key=lambda p: p["key"]):
        ver = cache.get(p["key"], {})
        if args.verified_only and ver.get("status") not in ("ok", "manual"):
            continue
        out.append(to_bib(p, ver))
    pathlib.Path(args.out).write_text("\n".join(out))
    print(f"{args.out}: {len(out)} entries")


if __name__ == "__main__":
    main()
