---
title: "A tool-using agent for phenotype-driven rare-disease diagnosis, evaluated with source-paper masking, prespecified external tests and case reports published after the model's cutoff"
author: "[Author names and affiliations — to be completed]"
---

**Corresponding author:** [name, address, e-mail, ORCID — to be completed]

## Key Points

- Hiding each test case's own source paper from the knowledge base halves the first-place accuracy of a published phenotype-driven tool (LIRICAL) on published cases, from 63% to 30%.
- An agent built on one inexpensive language model with phenotype tools ranked the confirmed diagnosis first more often than that model asked directly in three prespecified tests: 52% against 8% (146 MyGene2 patients), 24% against 15% (577 CADA patients) and 20% against 9% (240 case reports published after the model's training cutoff).
- The lead is narrower than these figures suggest: it was not significant for CADA's clinic patients, and on the case reports about half of it was the agent finding the right identifier — judged by disease name it was 22% against 18%, not significant. A frontier model asked directly was not significantly different from the agent on MyGene2.
- The agent's first version lost to its own model on patients curated elsewhere, a failure that a held-out test from its development source did not reveal; its traces pointed to tools that rank by fit and ignore prevalence.
- Every test is reported, failures included, with the plan fixed before it and the outcome of every case.

## Abstract

Language-model agents are reported to diagnose rare diseases from phenotypes, but their test cases usually come from the papers that phenotype knowledge bases were curated from, may be in a model's training data, and are not patients as clinics record them. We built an agent on one inexpensive model (`deepseek-flash`) with tools over public phenotype knowledge, and evaluated it with each case's source paper masked from everything the tools read, under plans committed before each test. Masking halved the first-place accuracy of a published tool, LIRICAL, on 840 held-out published cases (63.2% to 30.1%); masked, the agent's first version reached 42.4%, against 14.3% for its model asked directly. On patients curated elsewhere that version lost to its own model. Revised, the agent ranked the confirmed disease first more often than its model in three prespecified tests: 52.1% against 7.5% on 146 MyGene2 patients, 23.6% against 14.7% on 577 CADA patients, and 19.6% against 8.8% on 240 case reports published after the model's training cutoff (Holm-adjusted p < 0.001 each). The lead was not significant for CADA's clinic patients, and on the case reports about half of it came from the agent's lookup of identifiers: judged by disease name it was 21.7% against 18.3% (p = 0.19). GPT-6.1 asked directly was not significantly different from the agent on MyGene2 (54.8%). Accuracy on patients is far below unmasked benchmark figures; benchmarks should mask case sources and test outside the development source.

**Keywords:** rare disease; differential diagnosis; large language model; agent; Human Phenotype Ontology; data leakage; prespecified evaluation

## 1. Introduction

A patient with a rare disease often waits years for a diagnosis. Phenotype-driven tools were built to shorten that wait: given the patient's findings as Human Phenotype Ontology (HPO) terms [1], they rank the diseases whose annotated phenotype fits best [2–5]. Large language models (LLMs) have since been put to the same question, asked directly [6–9] and as agents or pipelines that call such tools, search the literature and reason over what they find [10–13]. The reported accuracies are high — a recent agentic system reports ranking the confirmed diagnosis first in 57% of cases on average across nine datasets [10] — and they are hard to read, for three reasons.

**Benchmarks leak through the knowledge base.** The public test cases are published case reports, and HPO's disease annotations are curated from published case reports — often the same ones. A tool that reads the annotations while it is tested on the very patient they were written from is, in part, reading the answer. Standard corpora and frameworks for benchmarking these tools now exist [14,15], but the overlap between test cases and annotation sources is rarely controlled, and its size has not, to our knowledge, been measured for a published tool.

**A model may have read the test.** A benchmark that was public before a model's training data ends can be memorised [8]. A model asked directly then looks stronger than it is, and so does any agent built on it.

**Published cases are not patients.** A case report describes a patient the authors chose, after the diagnosis was known. Patients as a clinic or a diagnostic laboratory records them have fewer findings, and more of them have the commoner rare diseases [16,17].

This paper reports an agent built and measured with each of the three in view. The agent itself is deliberately plain: one inexpensive general-purpose model with reasoning mode off, five or six tools over pinned public knowledge, at most eight model calls and about one US cent per case. What we consider the contribution is how it was measured, and what the measurement showed:

1. Every evaluation hides each case's own source paper from everything the tools read, and audits every tool output afterwards. On published cases the mask halves a published tool's first-place accuracy.
2. Every test followed a plan committed to the project's repository before its first run — the cases, the systems, the single comparison that decides the primary claim. Three prespecified claims failed and are reported as failures: the first version against its own model on cases published after the model's cutoff, and against a fixed pipeline on two external patient sets (Section 3.4), and the note reader against a dictionary (Supplementary S5).
3. After the first version lost to its own model on patients curated elsewhere, we revised it and tested the revision, under one plan, on three sets no system had been run on and no one had read: patients shared by families and clinicians (MyGene2 [18,19]), patients of diagnostic laboratories and clinics (the CADA test set [20]), and case reports that entered PubMed after the model's training data ends, each cut before the first sentence that gives its diagnosis away. We report where its lead holds and where it does not.

## 2. Methods

### 2.1 Task and scoring

A system is given a patient's findings as HPO terms, and the patient's sex where recorded, and nothing else — no diagnosis, no gene, no source; findings recorded as absent are withheld from every system. It answers with up to ten diseases, best first, each with an OMIM or Orphanet identifier. A case is solved at rank *k* when one of the first *k* identifiers is the confirmed diagnosis, or an identifier that Mondo [21] (release 2026-09-01) maps to it exactly. For a condition with several genetic subtypes this asks for the subtype, which a phenotype alone often cannot decide. A case with no answer is a miss and stays in the denominator. Rates carry 95% Wilson intervals [22]. Two systems are compared on the same cases by the two-sided exact sign test on the cases that exactly one of them solves; the three primary tests of Section 3.6–3.7 are corrected together by Holm's method [23], and every other p-value is unadjusted.

Answers were also scored by name with DeepRare's judging prompt [10], which asks a model whether each of the first five names denotes the confirmed disease. The judge was `deepseek-flash`, the model inside the systems it judged. Prespecified claims are decided by identifiers.

### 2.2 Cases

Table 1 lists every set of cases, how it was used and which version of the agent it tested.

**Development and held-out cases.** Phenopacket Store 0.1.27 [14,24] holds 10,374 published patients with HPO-coded findings and a confirmed OMIM diagnosis, from 1,733 papers (780 diseases). Papers, not patients, were split before any development: 6,014 patients for development (the "design" split, which also fills the bank of similar patients that one tool searches) and 4,360 patients from 840 papers held out. A development set of 200 cases, one per paper, was used for every design decision. The held-out test takes one case from each of the 840 papers; other providers' models and DeepRare were run on a fixed random 200 of them.

**Temporal test.** One case from each paper in the store whose first public day — the earliest of PubMed's entry, electronic-publication and issue dates — is on or after 1 June 2025, the reported end of the model's training data: 21 papers from the held-out split and 26 added to the store after release 0.1.27 (47 cases).

**External sets.** RareBench's [6] HMS (88 patients of a clinic at Hannover Medical School) and RAMEDIS (624 patients of a registry of metabolic diseases) tested the first version; after their errors were read they became development sets. RareBench's MME (40 published cases whose source cannot be masked) was used once for each of the first two versions and then for development. Further development sets were 498 case reports from RareArena [25], read into HPO terms, and 300 of the CADA training patients.

**Prespecified tests of the revised agent**, fixed in one plan before any system ran on them; no one had read their cases:

- *MyGene2* [19]: features and causal genes shared on mygene2.org by families and clinicians, as preprocessed for SHEPHERD [18] (146 patients with an OMIM diagnosis; CC0). Its 44 diseases are concentrated: types of distal arthrogryposis account for 54 patients (type 5 alone for 24), the related CLIFAHDD syndrome for 15, Nager syndrome for 15 and scalp-ear-nipple syndrome for 10; 26 patients share their exact set of findings with another patient. Fifty-four patients carry a PubMed identifier (six papers), which was masked like any case's source; the other 92 name no source and could not be masked. DeepRare reports on the same file [10].
- *CADA test set* [20]: we kept the CADA authors' split; of their test file, the 577 patients with an OMIM diagnosis are the test, a fixed random 300 of their training file were developed on, and their validation file was left unread. Of the 577, 239 are ClinVar submissions that carry HPO terms, whose label is the condition the submitting laboratory asserted for a pathogenic variant; 205 are patients of the CADA authors' collaborating clinics; and 133 are published cases compiled for an earlier study. No CADA case names its source, so the mask could not act on any of them; the 133 published cases may be among the sources of HPO's annotations. The median patient has five findings (interquartile range 2–11), and almost a third (182) have one or two.
- *Case reports after the cutoff* (Supplementary S3): PubMed case reports in English with open-access full text, first public between 1 June 2025 and 24 October 2026, processed in one random order fixed by a seed. A report was kept when its title named exactly one disease that Orphanet lists [26] and two automatic annotators agreed on it — PubTator3 [27] from the title and abstract, and the model from the title, abstract and case description; disagreements were dropped, not adjudicated. The case description from the PMC BioC service [28] was cut, without rewriting, before the first sentence that names the disease, a synonym or its gene, reports a confirming test (a biopsy, a culture, sequencing, antibodies and the like), or that the model pointed to; each disease was drawn to the test or the development side by a seeded draw, so the sides share no disease. The kept text was read into HPO terms by the note reader (Section 2.4). The test side holds 240 reports of 142 diseases, first public between June 2025 and July 2026, with a median of 186 words kept and ten findings (interquartile range 6–17). The diagnosis is the one the report gives, not confirmed by us, and is often not Mendelian: 141 reports have a disease without an OMIM entry, and the diagnoses include infections (dengue fever, scrub typhus, herpes simplex encephalitis), tumours (Kaposi sarcoma, mantle cell lymphoma), autoimmune and inflammatory diseases (Kawasaki disease, microscopic polyangiitis) and a poisoning. An audit of 30 development-side reports found the answer key right in 29 and the diagnosis still readable from the kept text in 3 (10%; 95% CI 3.5–25.6). No one read the test side before the test.

### 2.3 Knowledge and leakage control

The tools read HPO's disease annotations (release 2026-09-01; 8,478 OMIM diseases) and, in v2 (Section 2.4), Orphanet's as well, merged by Mondo's exact matches (2,122 Orphanet entries merged into their OMIM disease; 2,233 Orphanet diseases of their own), together with Orphanet's prevalence classes and short disease descriptions from Orphanet and MedlinePlus Genetics.

While a system works on a case, the case's source paper is masked from all of it (Fig. 1):

- an annotation supported only by that paper is removed; an annotation other papers also support stays, without the masked paper among its sources;
- a disease known only from that paper does not exist for any tool — not in rankings, not by name, not as a similar patient's diagnosis — and a tool asked about it answers exactly as for an identifier that was never assigned, so the model cannot tell that something is hidden;
- patients from that paper are not in the bank of similar patients.

The mask works at the level of the paper, so it also removes what the same paper says about its other patients; it bounds the leak from above. Orphanet's annotations cite no paper and are never masked. A case that names no paper has nothing to mask. After each run, every tool output recorded in the traces is searched for the case's own paper and for diseases known only from it; a run with a single hit is void.

### 2.4 The agent

All versions run on LangChain's agent loop (LangGraph) with `deepseek-flash`, reasoning mode off, temperature 0, and at most eight model calls per case, the last of which is offered only the final answer. The tools are `rank_diseases` (every disease ranked by phenotype similarity to the patient [2]), `check_match` (the patient's findings against one disease: explained, unexplained, recorded as absent in the disease, and the disease's frequent features the patient lacks), `lookup_disease`, `find_disease` (an identifier from a name, by fuzzy matching against every name and synonym), `find_similar_patients` (the closest published patients of the design split, with their diagnoses) and, from v1.1 on, `search_disease_texts`.

- **v1.0** starts from the tools' evidence: the ten best candidates of a no-model ranking (the similarity's top thirty, reordered by findings explained), each with its match report. Its turns go to what the tools cannot do, such as a disease it suspects that they did not propose. Tested on the held-out, temporal, HMS and RAMEDIS sets.
- **v1.1** first answers from the model's own knowledge, before any tool runs. Each disease it names is looked up in the knowledge base — by the identifier the model wrote if the knowledge knows it, otherwise by its name — and checked like the tools' candidates; the first message shows both lists, each candidate with Orphanet's prevalence class, and the instructions ask the model to weigh the two as equals and, between candidates that fit comparably, to prefer the more common. "Relatively common" means an Orphanet class of one patient in 100,000 or more. An earlier form of v1.1, whose prompts still asked for a Mendelian disease and an OMIM number (v1.1a), was run on the temporal cases and MME without a prespecified comparison; v1.1 itself was tested on MyGene2 and CADA.
- **v2** is v1.1 with three changes, each measured without a model on the development sets beforehand: Orphanet's diseases merged into the knowledge; the tools' list taken from a one-way similarity (the patient's findings looked for in the disease, not the disease's in the patient [2,5]), in its own order; and a guard on the final order — when the model's own first answer is a relatively common rare disease that the tools also rank in their top thirty, it leads. Tested on the case reports.

On the four of five planned development sets that were run, v2 was not better than v1.1 (Supplementary Table S2), so under a rule written beforehand v1.1 is the system tested on MyGene2 and CADA, whose diagnoses all carry OMIM identifiers. That v2 would nevertheless be the system for the case reports, many of whose diagnoses are diseases v1.1's knowledge does not contain, was decided after the four sets had been run, and v2 had not been run on case reports before the test.

A clinical note is read into HPO terms by a separate reader before diagnosis (Supplementary S5): the model lists each finding with the note's words and its status (present, denied, in a relative) and never writes an identifier; exact names are coded directly, the rest chosen among candidates from a hybrid search over HPO's names and synonyms. Prompts are in Supplementary S4.

### 2.5 Comparators

The same model asked once without tools ("asked directly"), with a prompt that asks for a rare disease and an OMIM or Orphanet identifier; a fixed pipeline (the tools' top ten with their evidence, ranked by one model call); three no-model rankings — phenotype similarity alone, the nearest published patients' diagnoses, and "rank, then check" (the similarity's top thirty reordered by findings explained, v1.0's starting list); LIRICAL 2.4.1 [3] in phenotype-only mode on OMIM's diseases, given for each case its own copy of the annotation file written under the mask; three other providers' current models asked directly with the same prompt (GPT-6.1, Claude Sonnet 5.5, Gemini 4); and DeepRare [10], run from its published code with four substitutions that availability forced (Supplementary Table S8): the agent's non-reasoning model in place of DeepSeek-R1, the public part of its case bank only [29], DuckDuckGo as its web search, and one bug fixed. DeepRare searches the web and its case bank and could not be masked; everything it read was searched afterwards for each patient's own paper. On the case reports the comparators were the model asked directly, LIRICAL, rank-then-check, and the list that v2 starts from — the one-way similarity over the merged knowledge, without a model.

### 2.6 Plans, runs and records

Each test followed a plan committed to the project's git repository before its first run, fixing the cases, the systems and their frozen version, the one comparison that decides the primary claim, and that each system is scored once (Supplementary S7 lists each plan's commit). Commit times are recorded by the authors' own tools and are not independently time-stamped; the plans are written in Chinese, and S7 summarises them in English. A run that lost cases to failures of the model's API was completed by asking only those cases again. A run whose records were incomplete was void and repeated without its score being read; Supplementary S6 lists every such run. Every run, with every model call and tool call, is recorded with MLflow; per-case outcomes of every reported run are in the repository. Analyses not named in a plan are marked as unplanned where they are reported.

An AI assistant (Claude, Anthropic) wrote most of the software, ran the analyses and drafted the text under the authors' direction; the authors checked the results and take responsibility for them (Supplementary S9).

## 3. Results

The sets were used in this order. v1.0 was tested on the held-out cases (3.1–3.3), then on the temporal and two external sets, where it lost to its own model (3.4). Its errors on the external sets were read, and v1.1 and then v2 were developed (3.5). One plan then tested v1.1 on MyGene2 and CADA (3.6) and v2 on the case reports (3.7).

### 3.1 Masking each case's source paper halves LIRICAL's first-place accuracy on published cases

LIRICAL, a published and maintained tool, ranks the confirmed disease first in 63.2% of the 840 held-out cases unmasked and in 30.1% masked (278 cases lost, none gained). For three quarters of the cases HPO's annotation of the confirmed disease cites the case's own paper, and the whole difference comes from them. Part of it is that 122 of the 840 diseases are known to HPO only from the patient's own paper and vanish under the mask; on the 718 cases that remain answerable LIRICAL falls from 62.4% to 35.2%. The project's own no-model rankings lose as much (Fig. 2): rank-then-check falls from 67.9% to 32.1% at first place, and on the 200 development cases the phenotype similarity has the confirmed disease in its top ten for 82.0% unmasked and 49.0% masked. Masked or not, the tools keep their order relative to one another.

### 3.2 Held-out published cases

On the 840 held-out cases, one per paper, v1.0 ranked the confirmed disease first in 42.4% (95% CI 39.1–45.7) and in its top ten in 62.0% (58.7–65.2) (Fig. 3a; Table 2). The prespecified primary claim — the agent against the fixed pipeline at first place — holds: the agent alone solved 57 cases and the pipeline alone 10 (p = 4 × 10⁻⁹). The model inside the agent, asked directly, solved 14.3% (agent alone 257, model alone 21). Against LIRICAL the agent alone solved 121 cases and LIRICAL alone 18; masked, LIRICAL (30.1%) is level with the project's no-model rank-then-check (32.1%). With simulated sequencing — the causal gene among fifty candidates, the other 49 drawn uniformly from known disease genes, a favourable setting — the agent reached 65.9% against 59.5% for a gene ranking without a model.

### 3.3 Against frontier models and another agent

On a fixed random 200 of the held-out cases (Fig. 3b; Table 2), v1.0's 43.0% at first place is ahead of GPT-6.1 (33.0%; paired 37 : 17, p = 0.009), Gemini 4 (27.0%; 46 : 14) and Claude Sonnet 5.5 (23.5%; 52 : 13), each asked directly with the same prompt, and of LIRICAL (28.0%); the agent's own model scores 15.0% alone. DeepRare, run as described in Section 2.5, scores 8.5% by identifier and 27.5% by name, against the agent's 43.0% and 42.5% (paired by name, 48 : 18, p < 0.001); its reading included a patient's own paper for 3 of the 200 cases, none of which it solved. It took a median of 27 model calls and 3.2 minutes per case, against the agent's four to eight calls and 13 seconds. These conditions are not DeepRare's own, and the result does not speak to its published figures.

Split afterwards by Orphanet's prevalence class of the confirmed disease (on all 840 cases; unplanned), the model asked directly solved 61.9% of the 42 cases with a relatively common disease and v1.0 57.1%, while on the 272 cases with a disease rarer than one in a million the model solved 9.6% and v1.0 52.6%.

### 3.4 Outside the curated source, the first version lost to its own model

Two plans committed beforehand tested v1.0 once each (Fig. 4a). On the 47 temporal cases it solved 23.4% and its model asked directly 8.5% (paired 9 : 2, p = 0.065): the prespecified claim was not established. GPT-6.1, Claude Sonnet 5.5 and Gemini 4 asked directly also solved 23.4% each (paired with v1.0, 3 : 3, 4 : 4 and 4 : 4), although for them these papers are not all after their training cutoff, and LIRICAL 14.9%; 14 of the 47 cases cannot be answered by an annotation-reading tool under the mask (13 diseases known only from the case's own paper, one absent from HPO). On the two external patient sets v1.0 lost to its own model: 19.3% against 31.8% on HMS (4 : 15, p = 0.019) and 24.7% against 32.7% on RAMEDIS (47 : 97, p < 0.001). The claim prespecified for these sets — the agent against the fixed pipeline — also failed (54 : 45, p = 0.42).

On HMS the three frontier models asked directly scored below `deepseek-flash` (14.8–22.7% against 31.8%), the reverse of their order on the held-out cases. That could mean that `deepseek-flash` has seen RareBench, but on MME, also from RareBench, it solved 5%; we cannot tell. It does not excuse the agent, which runs on the same model and did not use what the model knew.

### 3.5 Why it lost, and what was changed

Read afterwards, the traces pointed to ranking rather than retrieval. Where the model alone was right and v1.0 wrong, v1.0's own top ten held the answer in 12 of 15 HMS cases and 85 of 97 RAMEDIS cases, and v1.0 had itself checked the right disease in most of them before preferring a rarer one with a richer annotation. The tools score how well a disease explains the findings, not how common it is, and OMIM's annotations describe the commoner rare diseases thinly: Behçet disease has 15 annotated findings in OMIM's entry and 85 in Orphanet's. The held-out set had hidden both problems, because it is made of published single-gene cases: only 42 of its 840 cases have a relatively common diagnosis. A prior adjusted by a clinician is one published answer to the same problem [30]; ours was to show the model each candidate's prevalence.

v1.1a, the first form of v1.1, was then run once on the temporal cases, where it beat the model asked directly 10 : 2 (p = 0.039) — a second test of the same set, without a prespecified comparison — and once on MME, where it was not better than v1.0 (72.5% against 80.0%; 1 : 4) on cases that could not be masked (Fig. 4b).

### 3.6 Prespecified tests of v1.1 on patients

One plan fixed three tests, each with one primary question — does the agent rank the confirmed disease first more often than its own model asked directly, on the same findings — with the three p-values corrected together by Holm's method. This section reports the two sets of patients, tested with v1.1; Section 3.7 the case reports. Both claims on patients hold (Fig. 4c; Fig. 5; Table 3).

On **MyGene2** (146 patients) v1.1 ranked the confirmed disease first in 52.1% (95% CI 44.0–60.0) and in its top ten in 74.0%; the model asked directly, in 7.5% (4.3–13.0) and 34.9%. Paired, the agent alone solved 69 patients and the model alone 4 (difference 44.5 points, 95% CI 35.6–53.4; Holm-adjusted p < 0.001); in the top ten, 64 : 7. The no-model rank-then-check solved 41.1%, and the agent was ahead of it too (17 : 1): on this set most of the agent's accuracy comes from its tools.

On the **CADA test set** (577 patients, 345 diseases) v1.1 ranked the confirmed disease first in 23.6% (20.3–27.2) and in its top ten in 43.8%; the model asked directly, in 14.7% (12.1–17.9) and 34.8%. Paired, 73 : 22 (difference 8.8 points, 5.6–12.1; Holm-adjusted p < 0.001); in the top ten, 88 : 36. Here rank-then-check is the weakest of the three (11.6%; agent against it, 71 : 2): with few findings the tools have little to rank on. The agent gave no answer for four patients, which count as misses.

**Clustering, scoring and lookup.** Patients cluster by disease, which inflates a sign test over patients. Counting diseases instead (unplanned), the agent solved more of a disease's patients than the model for 14 of MyGene2's diseases and fewer for 2 (p = 0.004), and 53 against 13 of CADA's (p < 0.001). Judged by name, the model asked directly gains — on MyGene2 from 7.5% to 13.7%, on CADA from 14.7% to 18.7% — and the agent hardly moves (54.1% and 24.8%); paired, 66 : 7 and 75 : 40 (p = 0.001). Looking up the direct model's answers the way v1.1 looks up its own (by the identifier written if the knowledge knows it, otherwise by the name; unplanned, no new model calls) leaves it exactly where it was, 7.5% on MyGene2 and 14.7% on CADA (a name-only lookup gives 2.7% and 12.0%): on these sets the model's errors are diagnoses, not numbers.

**Where CADA's patients come from** (Table 4; descriptive, unadjusted). The agent solved 13.4% of the 239 ClinVar submissions against the model's 7.5% (18 : 4), 20.0% of the 205 clinic patients against 15.6% (19 : 10, p = 0.14) and 47.4% of the 133 published cases against 26.3% (36 : 8). Judged by name, the difference was not significant for either group of patients (23 : 14, p = 0.19; 19 : 12, p = 0.28). The published cases, which the mask could not reach, contribute half of the agent's net lead; without them (unplanned) the agent solved 16.4% of 444 patients and the model 11.3% (37 : 14, p = 0.002; by name 42 : 26, p = 0.07).

**By number of findings** (Fig. 6; Supplementary Table S10). On CADA the lead was small and not significant with up to five findings (1–2: 12.1% against 9.3%, 7 : 2; 3–5: 23.0% against 18.5%, 12 : 6) and clear from six on (6–10: 27.0% against 15.3%, 19 : 6; 11 or more: 35.6% against 17.4%, 35 : 8). On MyGene2 it was large in every band from three findings on.

**Other comparators.** LIRICAL solved 41.8% of MyGene2 patients and 12.0% of CADA patients, level with rank-then-check on both and behind the agent on both (18 : 3, p = 0.001; 75 : 8). The budget allowed one frontier model on patients: GPT-6.1 asked directly on MyGene2 solved 54.8% (46.7–62.6) at first place and 75.3% in its top ten, not significantly different from the agent (22 : 26; difference −2.7 points, −12.0 to 6.6) at about the same cost per patient (Section 3.8). MyGene2 was public before that model's training data ends. DeepRare reports 74% on the same file [10], judged by name by GPT-4o, with web search and without masking; the figures are not comparable.

### 3.7 Prespecified test of v2 on case reports published after the cutoff

On the **240 case reports** v2 ranked the confirmed disease first in 19.6% (95% CI 15.1–25.1) and in its top ten in 43.3% (37.2–49.7); its own model asked directly, in 8.8% (5.8–13.0) and 20.0% (Fig. 4c; Fig. 5c; Table 3). Paired, the agent alone solved 30 reports and the model alone 4 (difference 10.8 points, 6.3–15.4; Holm-adjusted p < 0.001): the prespecified claim holds. Counting diseases, 28 : 4. The list v2 starts from, the one-way similarity without a model, solved 7.1%, and the agent was ahead of it (35 : 5). LIRICAL and rank-then-check solved 0.8% and 2.1%; they read only OMIM's diseases, so at most 99 of the 240 diagnoses were within their reach, and on those 99 they solved 2.0% and 5.1%. The agent gave no answer for two reports.

**Much of the lead is the identifier.** Judged by name, the agent solved 21.7% and the model asked directly 18.3% (18 : 10, p = 0.19; difference 3.3 points, −1.0 to 7.6); the one-way list 7.5% (agent against it, 39 : 5). The difference between the two scorings lies in the 141 reports whose disease has no OMIM entry (Table 5; unplanned). On them the model asked directly named the right disease first for 24 but gave a right identifier for 3; the agent, for 25 and 20. Looking the direct model's answers up the agent's way raises it only to 10.0%, because the Orphanet codes it writes mostly exist but name other diseases (agent against it, 28 : 5); looking them up by name alone raises it to 14.6% — 13.5% on the reports without an OMIM entry, against the agent's 14.2% — and the agent's lead to 21 : 9 (p = 0.04; unplanned, unadjusted). On the 99 reports with an OMIM disease the two scorings agree: 27.3% against 18.2% by identifier (12 : 3, p = 0.035) and 27.3% against 20.2% by name (11 : 4, p = 0.12). Of the agent's 10.8-point lead by identifier, 5.0 points remain against the name-only lookup and 3.3 under the name-based judge: on these reports about half or more of what the agent adds over its model is the right entry in the knowledge base — the record a clinician or a downstream tool would open — and the rest, a smaller gain in diagnosis that the judge does not establish. On the diseases without an OMIM entry, the whole difference is the entry.

By number of findings the agent was ahead in each band with three or more (Supplementary Table S10); six reports had one or two.

### 3.8 Cost

On MyGene2 and CADA v1.1 took a median of 17 seconds per patient, about 71,000 input tokens (three quarters served from the provider's cache) and 2,200 output tokens: US$0.008 per patient at list price, against US$0.007 for GPT-6.1 asked directly and US$0.0005 for its own model asked directly. On the case reports v2 took a median of 18 seconds and US$0.010 per report.

## 4. Discussion

A deliberately plain agent — one inexpensive model, a handful of tools over pinned public knowledge, at most eight model calls — ranked the confirmed disease first more often than its own model asked directly in three prespecified tests. The more useful findings are about how far that statement reaches.

**Masking matters, and is an upper bound.** On published cases, hiding each case's own paper halves a published tool's first-place accuracy, and an unmasked benchmark therefore inflates methods that read the annotations relative to those that do not. Our mask is strict — it removes whole papers, and with them 122 of 840 held-out diseases — so it bounds the leak from above; on the cases that stay answerable the drop is still from 62% to 35%. The mask cannot act on cases that name no source: all of CADA and most of MyGene2, where the 133 published CADA cases supplied half of the agent's lead.

**What the comparison with the model shows.** The primary question asked whether tools add to the model they run on; it does not show that the agent outperforms stronger models, established tools tuned differently, or a fixed tool-plus-model pipeline, which was not run on the new sets. Against its own model the answer depends on where the model fails. On the patient sets the model asked directly mostly named the wrong disease, and looking its answers up did not help it; the agent's lead survived name-based judging and counting by disease. On the case reports, whose diseases are often outside OMIM, the model often knew the disease and not its Orphanet number; looked up by name its answers closed about half of the gap, and under the name-based judge the agent's lead was not established. Finding the record is not nothing — a name without an identifier cannot be checked against a knowledge base or passed to another tool — but it is not diagnosis.

**Against stronger models.** A frontier model asked directly was behind the agent on the held-out cases, level with v1.0 on the temporal cases, and not significantly different from v1.1 on MyGene2. Tools do not make a small model better than a large one everywhere; what they give is accuracy that depends less on what the model has read — the agent's own model named 7.5% of MyGene2's diagnoses first (13.7% judged by name) — and evidence, for each candidate, that a clinician can check. In unplanned breakdowns the gain over the agent's own model was concentrated in the rarest diseases and, on CADA, in patients with six or more findings.

**A held-out set from the development source is not an external test.** v1.0 passed its held-out test with a wide margin and then lost to its own model on a clinic's and a registry's patients. Nothing in the held-out result warned of this: the held-out cases are published, monogenic, richly described and almost never of a relatively common disease. Phenotype-similarity methods have long debated one-way against symmetric similarity [2,5] and how to bring prior probabilities into the ranking [3,30]; our failure was a version of the second problem, and it showed only outside the development source.

**What the test sets are.** MyGene2 is dominated by distal arthrogryposis and related disorders, with patients clustered by disease and a sixth of them sharing an identical set of findings with another. CADA mixes laboratory submissions, whose labels are asserted conditions and whose median submission has three findings, with clinic patients and published cases; the agent's lead was clear for the submissions and the published cases and not established for the clinic patients. The case reports are mostly not Mendelian — infections, tumours, autoimmune diseases — and an automatic cut leaves about one in ten readable; tools built from Mendelian annotations are not expected to do well there, and did not.

**Limitations.** (i) Every test is retrospective and on public, de-identified data; no clinician used the system or adjudicated its answers, and no claim about clinical benefit is made. (ii) The agent sees only phenotype terms; sequencing, by which most Mendelian diagnoses are reached and which does not apply to non-genetic rare diseases, enters only as simulated candidate genes on the held-out set. (iii) One model was used throughout; its training cutoff is known only from third-party reports, and MyGene2 and CADA were public before it, so the model may have seen them. (iv) Exact-match scoring asks for genetic subtypes that a phenotype often cannot decide; it caps every phenotype-only system below 100%, and a scoring at the level of the disease group was not done. (v) Scoring by identifier favours a system that looks identifiers up over one that writes them from memory; the name-based judge was the systems' own model, and its judgments were not checked by a clinician. (vi) The choice between v1.1 and v2 used four of five planned development sets; three of v1.1's four figures there came from v1.1a (Supplementary S2). (vii) The plans are in the authors' working language and time-stamped only by their git commits. (viii) The case-report answer key, the reader that turned the reports into findings and the systems tested are built on the same model, and the case-report test measures the reader and the diagnosis together.

## 5. Conclusion

Measured with each case's own source hidden where it is known, on sets fixed in advance and scored once, a plain tool-using agent on an inexpensive model ranked a rare disease's identifier first more often than that model asked directly: on held-out published cases, on two sets of patients it was not developed on, and on case reports published after the model's training cutoff — on the last, about half of it by finding the right identifier, and not significantly when judged by name. It was not better than a frontier model asked directly on the one patient set where that comparison was made. Its first version failed on a clinic's and a registry's patients for a reason no held-out test from its development source could show. We suggest three practices to anyone reporting such systems: mask each test case's source from the knowledge base; test outside the source the system was developed on before quoting its accuracy; and commit the plan before the run, so that a failure is as visible as a success.

## Declarations

**Data and code availability.** Code, manifests, plans with their commit history, and per-case outcomes of every reported run are in the project repository [URL and archived DOI — to be completed]. Every dataset is public and pinned by version and checksum in `evals/datasets.toml`. The case-report texts are the one exception to redistribution (some licences are non-commercial); the committed table names each paper, the number of sentences kept and the checksum of the kept text, from which the set can be rebuilt.

**Ethics.** Only public, de-identified data were used. No patient was contacted and no clinical record was accessed.

**Funding.** [to be completed]

**Competing interests.** [to be completed]

**Author contributions (CRediT).** [to be completed]

**Use of generative AI.** An AI assistant (Claude, Anthropic) wrote most of the software, ran the analyses and drafted and edited the text under the authors' direction (Section 2.6; Supplementary S9). The authors reviewed the code, results and text and take full responsibility for the content. [To be confirmed and adapted to the journal's wording by the authors.]

## References

[see `references.md`; inserted at conversion]

## Figure legends

**Fig. 1. How a case is asked, and what is hidden while it is.** The model first answers from its own knowledge; the tools rank every disease and check the leading candidates; the agent then weighs both lists with further tool calls (v1.1 and v2; v1.0 starts from the tools' list only). While a case is asked, its own source paper is masked from everything the tools read, and every tool output is audited afterwards.

**Fig. 2. What the mask removes.** Share of cases with the confirmed disease found, with each case's own source paper left in the knowledge (open circles) and masked (filled): at first place on the 840 held-out cases for LIRICAL and the project's two no-model rankings, and in the top ten on the 200 development cases for the phenotype similarity.

**Fig. 3. Held-out published cases, v1.0.** Confirmed disease ranked first, with 95% Wilson intervals, scored by identifier. (a) 840 held-out cases, one per paper. (b) A fixed random 200 of them, with LIRICAL, three other providers' models asked directly and DeepRare run on the agent's model; DeepRare's 27.5% under name-based judging is given in the text.

**Fig. 4. The agent against its own model asked directly, on every test.** Rates at first place with 95% intervals; at the right, the cases only the agent and only the model solved, and the two-sided exact sign test (unadjusted). (a) v1.0, under prespecified plans. (b) v1.1a, without a prespecified comparison: the temporal cases a second time, and MME, whose source papers cannot be masked. (c) The three prespecified tests: v1.1 on the two sets of patients, v2 on the case reports.

**Fig. 5. The three prespecified tests.** Confirmed disease ranked first, with 95% Wilson intervals, for the agent, its own model asked directly, and the comparators run on each set, scored by identifier. (a) MyGene2 (v1.1). (b) CADA test set (v1.1). (c) Case reports published after the cutoff (v2; one-way similarity is the list v2 starts from; LIRICAL and rank-then-check read only OMIM's diseases, which include 99 of the 240 diagnoses).

**Fig. 6. The agent and its own model by how many findings the case has**, on each of the three prespecified tests. At the right, the cases only the agent and only the model solved, with the two-sided exact sign test (unadjusted).

## Tables

**Table 1. The sets of cases and how each was used.**

| set | cases | what the cases are | source masked | role |
|---|---|---|---|---|
| Design split | 6,014 (893 papers) | published patients, Phenopacket Store | — | development; bank of similar patients |
| dev-200 | 200 (one per paper) | from the design split | yes | development: every design decision |
| Held-out | 840 (one per paper) | published patients, papers disjoint from the design split | yes | prespecified test of v1.0 |
| Temporal | 47 (one per paper) | published after the model's training cutoff (21 also in the held-out set) | yes | prespecified test of v1.0; v1.1a afterwards |
| HMS | 88 | a clinic's patients (RareBench) | no source | prespecified test of v1.0; then development |
| RAMEDIS | 624 | a metabolic registry's patients (RareBench) | no source | prespecified test of v1.0; then development |
| MME | 40 | published cases (RareBench) | cannot be | v1.0 and v1.1a once each; then development |
| RareArena sample | 498 | case reports read into HPO terms | — | development |
| CADA development | 300 | from the CADA training file | no source | development |
| **MyGene2** | **146** | patients shared by families and clinicians | 54 of 146 | **prespecified test of v1.1** |
| **CADA test** | **577** | ClinVar submissions (239), collaborating clinics' patients (205), published cases (133) | no source | **prespecified test of v1.1** |
| Case reports, development side | 300 | after the cutoff; diseases disjoint from the test side | yes | not used here |
| **Case reports after the cutoff** | **240** | PubMed case reports first public on or after 2025-06-01, cut before the diagnosis | yes | **prespecified test of v2** |

**Table 2. Held-out published cases, v1.0.** Confirmed disease at first place and in the top ten, with 95% Wilson intervals, scored by identifier; each case's own source paper masked unless stated.

| system | top-1 | top-10 |
|---|---|---|
| *840 cases, one per paper* | | |
| Agent (v1.0) | 42.4% [39.1–45.7] | 62.0% [58.7–65.2] |
| Fixed pipeline | 36.8% [33.6–40.1] | 51.5% [48.2–54.9] |
| Rank, then check (no model) | 32.1% [29.1–35.4] | 51.5% [48.2–54.9] |
| LIRICAL | 30.1% [27.1–33.3] | 48.3% [45.0–51.7] |
| LIRICAL, unmasked | 63.2% [59.9–66.4] | 79.4% [76.5–82.0] |
| Nearest published patients (no model) | 27.9% [24.9–31.0] | 50.2% [46.9–53.6] |
| Phenotype similarity alone (no model) | 17.5% [15.1–20.2] | 44.4% [41.1–47.8] |
| Same model, asked directly | 14.3% [12.1–16.8] | 29.0% [26.1–32.2] |
| *a fixed random 200 of them* | | |
| Agent (v1.0) | 43.0% [36.3–49.9] | 60.5% [53.6–67.0] |
| GPT-6.1, asked directly | 33.0% [26.9–39.8] | 49.0% [42.2–55.9] |
| LIRICAL | 28.0% [22.2–34.6] | 47.0% [40.2–53.9] |
| Gemini 4, asked directly | 27.0% [21.3–33.5] | 42.0% [35.4–48.9] |
| Claude Sonnet 5.5, asked directly | 23.5% [18.2–29.8] | 38.5% [32.0–45.4] |
| Same model, asked directly | 15.0% [10.7–20.6] | 25.5% [20.0–32.0] |
| DeepRare on the same model, by identifier | 8.5% [5.4–13.2] | 11.5% [7.8–16.7] (top five) |
| DeepRare on the same model, judged by name | 27.5% | |

**Table 3. The three prespecified tests.** Confirmed disease within the first *k* answers, scored by identifier unless marked; the last column gives the cases only the agent and only the named system solved at first place, with the two-sided exact sign test (unadjusted; the three primary comparisons with the model asked directly are Holm-adjusted in the text). Rows judged by name use DeepRare's judging prompt, which reads the first five names.

| set | system | top-1 [95% CI] | top-3 | top-5 | top-10 | agent : system |
|---|---|---|---|---|---|---|
| MyGene2 (n = 146) | **Agent (v1.1)** | **52.1%** [44.0–60.0] | 63.0% | 68.5% | 74.0% | |
| | Same model, asked directly | 7.5% [4.3–13.0] | 18.5% | 28.8% | 34.9% | 69 : 4 (p < 0.001) |
| | Rank, then check (no model) | 41.1% [33.4–49.2] | 53.4% | 56.8% | 61.0% | 17 : 1 (p < 0.001) |
| | LIRICAL | 41.8% [34.1–49.9] | 49.3% | 53.4% | 56.2% | 18 : 3 (p = 0.001) |
| | GPT-6.1, asked directly | 54.8% [46.7–62.6] | 67.1% | 70.5% | 75.3% | 22 : 26 (p = 0.67) |
| | *judged by name:* agent (v1.1) | 54.1% | | | | |
| | *judged by name:* same model, asked directly | 13.7% | | | | 66 : 7 (p < 0.001) |
| CADA test (n = 577) | **Agent (v1.1)** | **23.6%** [20.3–27.2] | 32.6% | 36.4% | 43.8% | |
| | Same model, asked directly | 14.7% [12.1–17.9] | 22.2% | 27.0% | 34.8% | 73 : 22 (p < 0.001) |
| | Rank, then check (no model) | 11.6% [9.2–14.5] | 17.9% | 21.3% | 26.3% | 71 : 2 (p < 0.001) |
| | LIRICAL | 12.0% [9.6–14.9] | 19.9% | 23.4% | 28.6% | 75 : 8 (p < 0.001) |
| | *judged by name:* agent (v1.1) | 24.8% | | | | |
| | *judged by name:* same model, asked directly | 18.7% | | | | 75 : 40 (p = 0.001) |
| Case reports (n = 240) | **Agent (v2)** | **19.6%** [15.1–25.1] | 29.6% | 35.0% | 43.3% | |
| | Same model, asked directly | 8.8% [5.8–13.0] | 11.7% | 15.8% | 20.0% | 30 : 4 (p < 0.001) |
| | One-way similarity, merged knowledge (no model) | 7.1% [4.5–11.0] | 11.7% | 17.9% | 26.2% | 35 : 5 (p < 0.001) |
| | Rank, then check (no model; OMIM only) | 2.1% [0.9–4.8] | 4.6% | 5.0% | 7.1% | 43 : 1 (p < 0.001) |
| | LIRICAL (OMIM only) | 0.8% [0.2–3.0] | 3.8% | 4.2% | 6.2% | 45 : 0 (p < 0.001) |
| | *judged by name:* agent (v2) | 21.7% | | 37.9% | | |
| | *judged by name:* same model, asked directly | 18.3% | | 30.0% | | 18 : 10 (p = 0.19) |

**Table 4. The CADA test set by where its patients come from** (descriptive; p-values unadjusted). First place.

| source | patients | agent (v1.1) | same model, asked directly | rank, then check | agent : model | by name, agent : model |
|---|---|---|---|---|---|---|
| ClinVar submissions | 239 | 13.4% [9.6–18.3] | 7.5% [4.8–11.6] | 6.3% [3.8–10.1] | 18 : 4 (p = 0.004) | 23 : 14 (p = 0.19) |
| Collaborating clinics | 205 | 20.0% [15.1–26.0] | 15.6% [11.3–21.2] | 8.3% [5.2–12.9] | 19 : 10 (p = 0.14) | 19 : 12 (p = 0.28) |
| Published cases (source not masked) | 133 | 47.4% [39.1–55.8] | 26.3% [19.6–34.4] | 26.3% [19.6–34.4] | 36 : 8 (p < 0.001) | 33 : 14 (p = 0.008) |

**Table 5. Case reports by the kind of identifier the confirmed disease carries** (unplanned; p-values unadjusted). First place. *Lookup as the agent's*: the direct model's answers looked up the way v2 looks up its own (the identifier written if the knowledge knows it, otherwise the closest name); *lookup by name only*: the closest name at a similarity of 90 or more; *by name*: DeepRare's judging prompt with `deepseek-flash` as judge. No new model calls.

| confirmed disease | reports | agent, by identifier | agent, by name | model, by identifier | model, lookup as the agent's | model, lookup by name only | model, by name | agent : model, lookup by name only |
|---|---|---|---|---|---|---|---|---|
| No OMIM entry (Orphanet only) | 141 | 14.2% | 17.7% | 2.1% | 4.3% | 13.5% | 17.0% | 7 : 6 (p = 1.00) |
| OMIM | 99 | 27.3% | 27.3% | 18.2% | 18.2% | 16.2% | 20.2% | 14 : 3 (p = 0.013) |
| All | 240 | 19.6% | 21.7% | 8.8% | 10.0% | 14.6% | 18.3% | 21 : 9 (p = 0.04) |
