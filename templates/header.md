<h1 align="center">Awesome RSI → AI4AI</h1>

<p align="center">
  <a href="https://awesome.re"><img src="https://awesome.re/badge.svg" alt="Awesome"></a>
  <img src="https://img.shields.io/badge/papers-{{TOTAL}}-1F3A5F" alt="Papers">
  <img src="https://img.shields.io/badge/updated-{{UPDATED}}-2A9D8F" alt="Last update">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-CC0--1.0-lightgrey" alt="License: CC0-1.0"></a>
  <a href="CONTRIBUTING.md"><img src="https://img.shields.io/badge/PRs-welcome-E76F51" alt="PRs welcome"></a>
</p>

A curated and tagged reading list on **recursive self-improvement (RSI)** and **AI for AI (AI4AI)**: AI systems whose improvements feed back into their own ability to improve, and AI systems that do the research and engineering that builds the next generation of AI. Self-evolving agents and self-improving models are included when their loop is recursive, or when they are the standard baseline that a recursive loop is compared against.

**What is in scope.** Every entry does one of the following.

- **RSI**: builds or analyzes a loop in which the improved artifact becomes part of what does the improving. Examples: the trained model generates the next round's training signal, or the agent edits the code that edits it. Theory and limits of such loops also count.
- **AI4AI**: uses AI to produce or improve what AI is built, trained, or evaluated with. Examples: ML engineering, algorithms and objectives, architectures, kernels, training data and environments, alignment and evaluation research, and AI scientists working on ML.
- **Support**: measures, forecasts, governs, or surveys RSI and AI4AI.

A short **Background and Adjacent Precursors** section keeps canonical baselines whose improvement procedure stays fixed, such as self-refinement and prompt and memory optimization, and adjacent training methods that the survey cites as precursors. Background is an editorial role, not a closure class. Generic LLM or agent surveys, AI for the natural sciences, and domain applications are out of scope. Entries removed in the September 2026 re-scoping are listed with reasons in [`data/excluded.yaml`](data/excluded.yaml).

This list accompanies our survey *From Recursive Self-Improvement to AI for AI: A Survey and Perspective on Verification-Bounded Self-Evolving AI* (preprint coming soon).

<p align="center"><img src="assets/overview.png" width="92%" alt="Three routes from RSI to AI4AI: weights, agent code, and the AI research pipeline"></p>

<p align="center"><img src="assets/timeline.png" width="88%" alt="Milestones from 1965 to 2026"></p>

## How the list is organized

We describe every system as an improvement loop. A proposer suggests a change to some artifact, a verifier decides whether the change is an improvement, and an update rule keeps or discards it. Sections follow the three routes by which AI improves AI:

1. **Weights**: the model trains on a signal it generates.
2. **Agent code**: the system rewrites its own improver.
3. **The AI research pipeline**: AI improves the artifacts from which the next model is built.

These are followed by the systems where the routes meet (**Closing the Loop**), then measurement, safety, and governance, and finally the background and adjacent precursors. Entries carry these tags once they have been coded; a missing tag means not yet coded, and a tag that does not apply is left out:

| Tag | Values |
|---|---|
| What improves (locus) | `Output` `Context/Memory` `Weights` `Scaffold/Code` `ML artifact` `Research pipeline` |
| What decides (signal) | `Self-judgment` `Model judge / RM` `Execution / tests` `Ground truth / rules` `Human` `Benchmark score` `Mixed` |
| 🔁 | Recursive: the change feeds back into the system's own ability to improve |
| 🆕 | First released in July 2026 or later |

Within each subsection, entries are sorted from newest to oldest. Each work appears once; a blog post or report section that accompanies a listed paper is kept only when the survey cites it separately, and its note starts with "Companion to". Duplicates removed from the list are recorded in [`data/excluded.yaml`](data/excluded.yaml).
