[Date]

To the Editor, [Journal]

Dear Editor,

We submit for your consideration the manuscript **"A tool-using agent for rare-disease diagnosis, tested where its knowledge cannot leak: held-out reports, patients from clinics and diagnostic laboratories, and reports published after the model's cutoff"**.

Language-model agents are now reported to name a rare disease from a patient's phenotype with striking accuracy. Three things make such reports hard to trust, and each applies to most of the published evaluations: the public test cases are case reports that the phenotype knowledge bases were themselves curated from; a model may have memorised a public benchmark; and published cases are not patients as a clinic or a laboratory records them. Our manuscript is an attempt to measure one such agent with all three in view, and to report what the measurement shows, including where the agent failed.

What we believe is new and useful to your readers:

1. **The size of the leak.** Hiding each test case's own source paper from the knowledge base cuts the first-place accuracy of LIRICAL, a published and maintained tool, from 63.2% to 30.1% on 840 held-out published cases. For three quarters of those cases, the disease's annotation cites the patient's own paper. An unmasked benchmark of published cases is about half leakage, and it rewards the methods that lean hardest on the annotations.

2. **A complete, pre-registered record, failures included.** Every test followed a plan committed to a public repository before its first run, and each system ran once. The agent's first version passed its held-out test with a wide margin and then lost to its own model on a clinic's and a registry's patients. We report the loss, the cause we found in the traces (tools that score how well a disease fits and ignore how common it is), and the revision.

3. **Tests of the revised agent on patients it was not developed on, and on reports its model cannot have read.** On 146 patients shared by families and clinicians (MyGene2) the revised agent ranked the confirmed disease first in 52.1%, against 7.5% for the same model asked directly (cases only one solved, 69 : 4); on 577 patients of diagnostic laboratories and clinics (the CADA test set), in 23.6% against 14.7% (73 : 22). On 240 case reports that entered PubMed after the model's training data ends, each cut before the sentence that gives its diagnosis away, a second revision that also reads Orphanet ranked the confirmed disease first in 19.6% against 8.8% (30 : 4). We also report where the lead is not established: on the 205 patients of CADA's collaborating clinics the difference is four points and not significant; and on the case reports, judged by name rather than by identifier, the agent's lead narrows to 21.7% against 18.3% and is not significant, because the model asked directly often names an Orphanet-only disease without its identifier.

The agent itself is deliberately plain — one inexpensive general-purpose model, six tools over pinned public knowledge, under one US cent per patient — which we think makes the result more, not less, relevant: on held-out cases it is ahead of three frontier models asked directly, and on one set of patients the one frontier model we could run was its equal.

All code, the frozen lists of cases, the plans with their commit history and the per-case outcome of every reported run are public. Only public, de-identified data were used.

The manuscript has not been published and is not under consideration elsewhere. All authors have approved it. [Competing interests: to be completed.] An AI assistant was used to write software, run analyses and draft text; this is declared in the manuscript, and the authors take full responsibility for its content.

We suggest as reviewers researchers working on phenotype-driven diagnosis, on the evaluation of clinical language models, or on the Human Phenotype Ontology and its tools: [names to be completed].

Thank you for your consideration.

Yours sincerely,

[Corresponding author, affiliation, e-mail]
