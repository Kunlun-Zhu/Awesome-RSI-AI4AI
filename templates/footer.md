## Contributing

Additions and corrections are welcome. Please edit [`data/papers.yaml`](data/papers.yaml) rather than the README, then run:

```bash
pip install pyyaml
python scripts/verify.py          # checks the entry against arXiv, or OpenAlex by DOI or title
python scripts/build_readme.py    # regenerates README.md
python scripts/export_bib.py      # regenerates rsi-ai4ai.bib (BibTeX for every entry)
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the entry format and tagging guide.

## Citation

If this list helps your work, please cite the accompanying survey (BibTeX will be added with the preprint).

## License

[CC0 1.0](LICENSE). To the extent possible under law, the authors have waived all copyright and related rights to this list.
