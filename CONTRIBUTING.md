# Contributing

Thanks for helping keep this list accurate. The README is generated, so please edit [`data/papers.yaml`](data/papers.yaml) and regenerate it.

## Add a paper

1. Append an entry to `data/papers.yaml`:

   ```yaml
   - key: zelikman2024stop            # BibTeX key: firstauthorYEARword, unique
     short: STOP                      # optional short name
     title: "Self-Taught Optimizer (STOP): Recursively Self-Improving Code Generation"
     authors: "Eric Zelikman, Eliana Lorch, Lester Mackey, Adam Tauman Kalai"
     venue: COLM 2024                 # or "arXiv 2026" for preprints
     date: 2023-10                    # month of first public release (YYYY-MM)
     arxiv: "2310.02304"              # optional
     url: https://arxiv.org/abs/2310.02304
     code: https://github.com/microsoft/stop   # optional
     section: agents.self-referential # a leaf id from data/taxonomy.yaml
     locus: scaffold                  # see tagging guide below
     signal: execution
     recursive: yes                   # yes | partial | no
     note: One sentence on what the paper contributes.
   ```

2. Run the checks and rebuild:

   ```bash
   pip install pyyaml
   python scripts/verify.py          # compares the title with OpenAlex
   python scripts/build_readme.py
   ```

   `verify.py` must report `ok` for the new entry. If a blog post or report has no OpenAlex record, add `verify: skip`.

3. Open a pull request with both `data/` and `README.md` changes.

## Tagging guide

**locus**: what the improvement loop changes.

| Value | Use when the loop changes |
|---|---|
| `output` | a single answer or solution, with the model unchanged (self-refinement) |
| `context` | prompts, memory, retrieved experience, or skill libraries |
| `weights` | model parameters, via self-generated data, rewards, or curricula |
| `scaffold` | the agent's own code, tools, workflow, or search procedure |
| `artifact` | a component used to build AI systems: algorithms, objectives, architectures, kernels, data, environments, or benchmarks |
| `pipeline` | the research process as a whole (ideation to paper) |

**signal**: what decides whether a change is an improvement.

| Value | Meaning |
|---|---|
| `self` | the same model judges its own output (confidence, self-consistency, self-critique) |
| `model` | another model: a reward model or LLM judge |
| `execution` | running code, tests, compilers, simulators, or environments |
| `ground-truth` | labeled answers or rule-based checks |
| `benchmark` | a held-out benchmark score |
| `human` | human ratings, reviews, or preferences |
| `mixed` | several of the above with no single dominant signal |

**recursive**: `yes` if the improved artifact becomes part of the improver in the next round (for example, the updated agent rewrites itself again), `partial` if only some components feed back, `no` otherwise.

## Scope

In scope: work on AI systems that improve themselves or improve the process that builds AI systems, plus theory, benchmarks, safety analyses, and surveys on these topics. Out of scope: general AI-for-science systems that do not target AI research, unless they are a standard reference point (these may go in the relevant section with a note).
