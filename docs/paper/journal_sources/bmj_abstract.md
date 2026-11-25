**Objectives** To evaluate a low-cost tool-using agent for phenotype-driven rare disease diagnosis attending to benchmark leakage, memorisation and the gap between published cases and patients.

**Methods** An agent on one inexpensive language model used tools over public phenotype knowledge; each case's known source paper was masked from the tools, and each test followed a plan committed beforehand. The primary outcome was ranking the confirmed disease's identifier first, compared, for the revised agent, with the same model asked directly.

**Results** Masking halved a published tool's first-place accuracy on 840 held-out cases (63.2% to 30.1%). The first version led on these cases but lost to its own model on two external patient sets. In three prespecified tests on cases never used in development, two revisions of the agent ranked the confirmed disease first more often than their model: 52.1% vs 7.5% on 146 MyGene2 patients, 23.6% vs 14.7% on 577 CADA patients and 19.6% vs 8.8% on 240 case reports published after the model's cutoff (Holm-adjusted p < 0.001 each). By disease name, the lead held on MyGene2 and CADA but not on the case reports (21.7% vs 18.3%), where much of it was retrieval of the correct entry; it was not significant for CADA's 205 collaborators' patients, and GPT-6.1 asked directly did not differ significantly on MyGene2 (54.8%).

**Discussion** Masking changed benchmark results substantially; held-out tests missed a failure external patients exposed.

**Conclusion** Evaluations should mask case sources, test outside the development source and fix the plan in advance.
