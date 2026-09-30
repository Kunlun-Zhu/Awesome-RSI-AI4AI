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
     section: rsi.self-referential    # a leaf id from data/taxonomy.yaml
     scope: core-rsi                  # core-rsi | core-ai4ai | support | background
     locus: scaffold                  # see tagging guide below
     signal: execution
     recursive: yes                   # yes | partial | no | na (follows from closure)
     closure: P proc                  # see tagging guide below
     note: One sentence on what the paper contributes.
   ```

   Optional fields:

   | Field | Use |
   |---|---|
   | `doi` | DOI of the version of record, without `https://doi.org/`. Give it for every journal or proceedings paper that has one; `verify.py` then checks the entry by DOI, and `export_bib.py` takes the author list from `authors` (the version of record) instead of arXiv. For a work with no arXiv version, set `url` to `https://doi.org/<doi>`. |
   | `bibtype` | `book` (with `publisher` and optional `isbn`) or `misc` (web documents and preprints hosted outside arXiv). Otherwise the BibTeX type is inferred from `venue`. |
   | `volume`, `pages` | Volume and page range for journal articles and book chapters, when known. |
   | `provenance` | `secondary` if the primary page could not be read and the entry is known only from news or other secondary reports. Omit it otherwise. |
   | `subgroup` | For a section whose leaf in `data/taxonomy.yaml` declares `subgroups`, the id of the subgroup the entry belongs to. Entries without it go to the first subgroup. Use it to separate comparison systems with an empty closure set from recursive systems in the same section. |
   | `verify` | `skip` for documents with no arXiv identifier, DOI, or database record (blog posts, reports, system cards, news). |

   Write `authors` as a comma-separated list of full names in "First Last" order ("Jane Doe, John Smith"), never "Doe, Jane", and end it with `et al.` only when the list is truncated. For an organization, give its name alone ("Anthropic").

2. Run the checks and rebuild:

   ```bash
   pip install pyyaml
   python scripts/verify.py          # compares the title with OpenAlex
   python scripts/build_readme.py
   ```

   `verify.py` must report `ok` for the new entry. If a blog post or report has no OpenAlex record, add `verify: skip`; `python scripts/verify.py --pages` then records whether its URL resolves and shows the title.

   Before adding, search `papers.yaml` for the same arXiv identifier, DOI, URL, and title. One work gets one entry. A blog post or report section that accompanies a listed paper gets its own entry only if the survey cites it separately; its note must start with `Companion to <key>.` When you find a duplicate, keep the key the survey cites, merge the notes, and move the other entry to `data/excluded.yaml` with `excluded_reason: duplicate of <key>`. `build_readme.py` rejects entries that share an arXiv identifier, DOI, or URL unless one is marked as a companion of the other.

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
| `self` | the same model judges its own output (confidence, self-consistency, self-critique), or outputs are kept by the model's own construction or by novelty and format heuristics with no external check of correctness |
| `model` | another model: a reward model or LLM judge |
| `execution` | running code, tests, compilers, simulators, or environments |
| `ground-truth` | gold labels, fixed reference outputs, or fixed rules (game outcomes, proof checkers) |
| `benchmark` | a held-out benchmark score |
| `human` | human ratings, reviews, or preferences |
| `mixed` | several of the above with no single dominant signal |

**closure**: which of the proposer `P`, verifier `V`, and update rule `U` change in the reported runs and take part in producing later updates. The coding manual in the survey's supplement gives the full decision procedure and worked boundary cases; in short:

- The analyzed boundary is one loop: the computations that propose, score, and apply candidates, fixed or not. A frozen base model or a fixed benchmark is inside the boundary but outside the set of components that can change. Code only the components that actually change in the reported runs and are used in later iterations.
- Decide by the functional role of a changed artifact, not by its storage form. It counts when it proposes or selects candidate changes (the trained model that samples the next candidates, a mutation prompt, a meta-skill, a search strategy, the improver's own code), scores them (a judge, reward model, test suite, rubric), or configures updates (hyperparameters set from the loop's state, update directives). It does not count when it is the object being improved (a task prompt, a task skill, an agent edited by a separate fixed agent), history read by a fixed procedure (archives, memories, meta-prompt trajectories, search statistics), or a component changed only by another loop.
- A model trained on samples it generates is at least `P param`; if it also labels or scores them, including by majority vote over its own samples, add `V`. Training once on another fixed model's data is `none`.
- List the members, then write `param` if only weights or parameters change (`P param`, `P,V param`, `P,U param`, `U param`) or `proc` if code, algorithm, or defining instructions change (`P proc`, `V proc`, `P,V proc`). Schedules fixed in advance do not count.
- Use `none` when the improved artifact is only read or used by a fixed procedure (Self-Refine; OPRO, GEPA, and other prompt and memory optimizers; ADAS and AFlow, whose meta-optimizer is fixed; a fixed agent that trains another model, such as RSI-Master). Use `pipeline` when the artifact returns only through building a new model (the AlphaEvolve kernel in Gemini training; Nemotron-4, DeepSeek-R1), and only when the source states that return path; a company-wide share of AI-written code is `na`. Use `na` for works that are not loops (surveys, positions, frameworks, benchmarks, forecasts, safety documents, announcements of a research program).
- Code nested loops separately and tag the loop the work is about: SEAL's outer loop is `P param` and its inner loop `P,U param` (tagged `P,U param`); VeLO is `none` in both loops.

**recursive** follows from `closure`: `yes` for any `proc` closure or `pipeline`, `partial` for `param` closures, `no` for `none`, and `na` for `na`.

Leave a tag out if it has not been coded yet; the paper's supplement prints a missing tag as "n.c." (not coded). Use `na` for `locus`, `signal`, or `closure` only when the tag does not apply, for example the locus of a theorem about evaluation or the signal of a loop that keeps every sample unchecked (model collapse); `na` is printed as "--".

## Scope

Every entry needs a `scope` value. Ask one question first: does the improved artifact become part of the improver (RSI), or is it something AI systems are built, trained, or evaluated with (AI4AI)? If the answer is neither, the paper probably belongs elsewhere.

| `scope` | Use when the work | Examples |
|---|---|---|
| `core-rsi` | builds or analyzes a loop in which the improved artifact becomes part of the improver, or studies the theory and limits of such loops | Self-Rewarding LMs, Absolute Zero, SEAL, STOP, Darwin Gödel Machine, model-collapse theory |
| `core-ai4ai` | uses AI to produce or improve artifacts for building, training, or evaluating AI, or to do ML research | AlphaEvolve, AIDE, DiscoPOP, ASI-Arch, KernelBench agents, The AI Scientist, automated alignment researchers |
| `support` | measures, forecasts, governs, or surveys RSI and AI4AI | MLE-bench, RE-Bench, METR time horizons, frontier safety frameworks, surveys of self-evolving AI |
| `background` | is a canonical baseline whose improvement procedure stays fixed, or an adjacent training precursor that the survey cites without making it its focus (background is an editorial role, not a closure class) | Self-Refine, Reflexion, OPRO, DSPy, Voyager; ExIt, Constitutional AI, RLAIF, SCoRe, TTRL |

Out of scope: generic LLM, agent, LLM-as-judge, synthetic-data, or RL-for-reasoning surveys; AI for the natural sciences; domain applications such as translation or medicine; benchmarks that do not measure AI research ability. Put a self-evolving agent under `core-rsi` only if it changes its own improvement procedure or trains on a signal it generates over several rounds; otherwise it is `background` at most.

Sections (`section`) are leaves of [`data/taxonomy.yaml`](data/taxonomy.yaml): the three routes (`rsi.*` for weights and agents, `ai4ai.*` for the research pipeline), `closing.*` for systems where the routes meet, then `evaluation.*`, `safety.*`, `surveys.*`, `foundations.*`, and `background.*`.
