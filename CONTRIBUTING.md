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

Every entry needs a `scope` value. Ask one question first: does the improved artifact become part of the improver (RSI), or is it something AI systems are built, trained, or evaluated with (AI4AI)? If the answer is neither, the paper probably belongs elsewhere.

| `scope` | Use when the work | Examples |
|---|---|---|
| `core-rsi` | builds or analyzes a loop in which the improved artifact becomes part of the improver, or studies the theory and limits of such loops | Self-Rewarding LMs, Absolute Zero, SEAL, STOP, Darwin Gödel Machine, model-collapse theory |
| `core-ai4ai` | uses AI to produce or improve artifacts for building, training, or evaluating AI, or to do ML research | AlphaEvolve, AIDE, DiscoPOP, ASI-Arch, KernelBench agents, The AI Scientist, automated alignment researchers |
| `support` | measures, forecasts, governs, or surveys RSI and AI4AI | MLE-bench, RE-Bench, METR time horizons, frontier safety frameworks, surveys of self-evolving AI |
| `background` | is a canonical non-recursive baseline (the procedure that improves stays fixed) | Self-Refine, Reflexion, OPRO, DSPy, Voyager |

Out of scope: generic LLM, agent, LLM-as-judge, synthetic-data, or RL-for-reasoning surveys; AI for the natural sciences; domain applications such as translation or medicine; benchmarks that do not measure AI research ability. Put a self-evolving agent under `core-rsi` only if it changes its own improvement procedure or trains on a signal it generates over several rounds; otherwise it is `background` at most.

Sections (`section`) are leaves of [`data/taxonomy.yaml`](data/taxonomy.yaml): the three routes (`rsi.*` for weights and agents, `ai4ai.*` for the research pipeline), `closing.*` for systems where the routes meet, then `evaluation.*`, `safety.*`, `surveys.*`, `foundations.*`, and `background.*`.
