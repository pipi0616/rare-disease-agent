---
title: "Multimedia Appendix 3. Use of generative AI in this work"
---

## Tool

Claude (Anthropic), used through the Claude Code command-line assistant, in sessions between October and November 2026. The models were Claude Opus and Claude Fable versions current at the time (recorded in each commit's trailer in the project repository).

## What it was used for

Under the authors' direction, the assistant:

1. wrote most of the software in the project repository — the agent, its tools, the data loaders, the evaluation harness, the masking and leak audit, the statistical scripts and the figure scripts;
2. ran the evaluations and the analyses, and recorded every run in MLflow;
3. drafted the evaluation plans (in Chinese), the manuscript, the supplementary material and the cover letter, and revised them;
4. checked the numbers in the manuscript against the per-case outcome files with scripts, and ran separate review passes of the manuscript by other instances of the assistant — methods and statistics, domain, editorial, presentation, results and claims, independent number audits, and final checks of the figures, the documents and the tables — whose corrections are recorded in the repository's commit history.

The agent evaluated in the paper also uses a language model (deepseek-flash); that use is part of the method and is described in the Methods section, not here.

## Human oversight

The authors set the research questions, approved each evaluation plan before its test, decided which results to report and how, reviewed the code, the results and the text, and take full responsibility for the content of the article. No AI tool is listed as an author.

## Records

Every change to code, plans and text is in the repository's commit history, each commit marked when it was co-written with the assistant. The assistant's session transcripts are kept by the authors. Because of their volume (several weeks of interactive sessions covering software, analyses and writing), they are not attached; they will be provided in full to the editors on request.
