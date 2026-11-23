[Date]

To the Editor, Briefings in Bioinformatics

Dear Editor,

We submit for your consideration, as a Problem Solving Protocol, the manuscript **"Source-paper masking and prespecified external tests of a low-cost tool-using agent for rare-disease diagnosis"**.

Language-model agents are now reported to name a rare disease from a patient's phenotype with striking accuracy. Three things make such reports hard to read: the public test cases are case reports that phenotype knowledge bases were curated from; a model may have memorised a public benchmark; and published cases are not patients as a clinic or a laboratory records them. Our manuscript measures one such agent with these three in view, and reports what the measurement shows, with analyses that locate where the agent's lead comes from.

What we believe is useful to your readers:

1. **The size of the leak.** Hiding each test case's own source paper from the knowledge base halves the first-place accuracy of LIRICAL, a published and maintained tool, on 840 held-out published cases (63.2% to 30.1%; 62.4% to 35.2% on the cases that remain answerable). The paper-level mask is not an exact measure of the leak — it removes what a paper says about its other patients and misses annotations that cite no paper — and unmasked benchmarks of published cases inflate methods that read the annotations relative to those that do not.

2. **External tests catch what held-out tests miss.** The agent's first version passed its held-out test from the development source and then lost to its own model on a clinic's and a registry's patients; its traces showed a ranking blind to prevalence, which the held-out cases had hidden. Every prespecified test followed a plan committed to the project's repository before its first run; of twelve prespecified primary claims, nine held and three failed, and all are reported.

3. **Three prespecified tests of the revised agent on cases never used in its development.** Scored by identifier, on 146 MyGene2 patients the agent ranked the confirmed disease first in 52.1% against 7.5% for its own model asked directly; on 577 CADA cases, 23.6% against 14.7%; on 240 case reports published after the model's training cutoff, 19.6% against 8.8% — also when counted by disease, and ahead of its tools alone on each set. We show what the lead is made of: judged by disease name it holds on MyGene2 and on CADA as a whole; on the case reports roughly half to two thirds of it is retrieving the correct knowledge-base entry, and by name the lead there is not significant. We also report that the lead was not established for the 205 patients of CADA's collaborators' cohorts, and that GPT-6.1 asked directly was not significantly different from the agent on MyGene2.

The agent itself is deliberately plain — one inexpensive general-purpose model, a handful of tools over pinned public knowledge, about one US cent per case. All code, frozen case lists, plans with their commit history and the per-case outcomes will be public in the project repository on submission. Only public, de-identified data were used.

The manuscript has not been published and is not under consideration elsewhere. [Related preprints or earlier work by the authors: to be completed.] All authors have approved it and meet the criteria for authorship. [Competing interests: to be completed.] An AI assistant was used to write software, run analyses and draft text; this is declared in the Methods and in the supplementary material, and the authors take full responsibility for the content.

We suggest as reviewers researchers working on phenotype-driven diagnosis, on the evaluation of clinical language models, or on the Human Phenotype Ontology and its tools: [names to be completed].

Thank you for your consideration.

Yours sincerely,

[Corresponding author, affiliation, e-mail, ORCID]
