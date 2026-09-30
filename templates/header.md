<h1 align="center">Awesome RSI → AI4AI</h1>

<p align="center">
  <a href="https://awesome.re"><img src="https://awesome.re/badge.svg" alt="Awesome"></a>
  <img src="https://img.shields.io/badge/papers-{{TOTAL}}-1F3A5F" alt="Papers">
  <img src="https://img.shields.io/badge/updated-{{UPDATED}}-2A9D8F" alt="Last update">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-CC0--1.0-lightgrey" alt="License: CC0-1.0"></a>
  <a href="CONTRIBUTING.md"><img src="https://img.shields.io/badge/PRs-welcome-E76F51" alt="PRs welcome"></a>
</p>

A curated and tagged reading list on **recursive self-improvement (RSI)**, **self-evolving AI and agents**, and **AI for AI research (AI4AI)**. It covers AI systems that improve their own outputs, memory, weights, and code, and AI systems that take over parts of the research that produces the next generation of AI.

The three terms name one idea at different scales. Self-evolving agents change their memory, prompts, or code as they work; self-improving models train on data and rewards they generate; AI4AI systems improve the pipeline that builds the next model. When the product of any of these loops becomes the improver in the next round, the loop is recursive.

This list accompanies our survey *From Recursive Self-Improvement to AI for AI: A Survey and Perspective on Verification-Bounded Self-Evolving AI* (preprint coming soon).

<p align="center"><img src="assets/overview.png" width="92%" alt="From RSI to AI4AI: the improvement loop"></p>

<p align="center"><img src="assets/timeline.png" width="88%" alt="Milestones from 1965 to 2026"></p>

## How the list is organized

We describe every self-improving system as an improvement loop. A proposer suggests a change to some artifact, a verifier decides whether the change is an improvement, and an update rule keeps or discards it. Sections are ordered by what the loop changes, from a single answer up to the AI research pipeline itself. Every entry carries two tags:

| Tag | Values |
|---|---|
| What improves (locus) | `Output` `Context/Memory` `Weights` `Scaffold/Code` `ML artifact` `Research pipeline` |
| What decides (signal) | `Self-judgment` `Model judge / RM` `Execution / tests` `Ground truth / rules` `Human` `Benchmark score` `Mixed` |
| 🔁 | Recursive: the change feeds back into the system's own ability to improve |
| 🆕 | First released in July 2026 or later |

Within each subsection, entries are sorted from newest to oldest.
