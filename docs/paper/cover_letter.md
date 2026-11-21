[Date]

To the Editor, Briefings in Bioinformatics

Dear Editor,

We submit for your consideration, as a Problem Solving Protocol, the manuscript **"A tool-using agent for phenotype-driven rare-disease diagnosis, evaluated with source-paper masking, prespecified external tests and case reports published after the model's cutoff"**.

Language-model agents are now reported to name a rare disease from a patient's phenotype with striking accuracy. Three things make such reports hard to read: the public test cases are case reports that phenotype knowledge bases were curated from; a model may have memorised a public benchmark; and published cases are not patients as a clinic or a laboratory records them. Our manuscript measures one such agent with these three in view, and reports what the measurement shows, including where the agent failed and where its lead is narrower than its headline figures.

What we believe is useful to your readers:

1. **The size of the leak.** Hiding each test case's own source paper from the knowledge base halves the first-place accuracy of LIRICAL, a published and maintained tool, on 840 held-out published cases (63.2% to 30.1%; 62.4% to 35.2% on the cases that remain answerable). Our paper-level mask bounds the leak from above, and unmasked benchmarks of published cases inflate methods that read the annotations relative to those that do not.

2. **A complete record under plans fixed beforehand, failures included.** Every test followed a plan committed to the project's repository before its first run. The agent's first version passed its held-out test and then lost to its own model on a clinic's and a registry's patients; we report the loss, what its traces showed, and the revision. Three prespecified claims failed and are reported as failures.

3. **Tests of the revised agent on sets no system had seen.** On 146 MyGene2 patients the agent ranked the confirmed disease first in 52.1% against 7.5% for its own model asked directly; on 577 CADA patients, 23.6% against 14.7%; on 240 case reports published after the model's training cutoff, 19.6% against 8.8%. We also report where the lead is not established: for CADA's clinic patients; on the case reports when answers are judged by disease name (21.7% against 18.3%), where most of the agent's advantage was finding the right identifier; and against GPT-6.1 asked directly on MyGene2, which was not significantly different from the agent.

The agent itself is deliberately plain — one inexpensive general-purpose model, a handful of tools over pinned public knowledge, about one US cent per case. All code, frozen case lists, plans with their commit history and the per-case outcome of every reported run are public. Only public, de-identified data were used.

The manuscript has not been published and is not under consideration elsewhere. [Related preprints or earlier work by the authors: to be completed.] All authors have approved it. [Competing interests: to be completed.] An AI assistant was used to write software, run analyses and draft text; this is declared in the Methods and in the supplementary material, and the authors take full responsibility for the content.

We suggest as reviewers researchers working on phenotype-driven diagnosis, on the evaluation of clinical language models, or on the Human Phenotype Ontology and its tools: [names to be completed].

Thank you for your consideration.

Yours sincerely,

[Corresponding author, affiliation, e-mail, ORCID]
