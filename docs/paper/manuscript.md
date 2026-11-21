---
title: "A tool-using agent for rare-disease diagnosis, tested where its knowledge cannot leak: held-out reports, patients from clinics and diagnostic laboratories, and reports published after the model's cutoff"
author: "[Author names and affiliations — to be completed]"
---

**Corresponding author:** [name, address, e-mail — to be completed]

## Highlights

- Masking each case's own source paper from the knowledge base halves the measured accuracy of phenotype-driven tools on published cases.
- On held-out published cases, an agent on one inexpensive model with a handful of tools ranks the confirmed disease first more often than three frontier models asked directly.
- Its first version lost to its own model on patients curated elsewhere; the cause, found in its traces, was a ranking blind to how common a disease is.
- Revised, and tested once under a plan committed beforehand on patients no system had seen, it ranked the confirmed disease first in 52.1% of 146 patients shared by families and clinicians and 23.6% of 577 diagnostic-laboratory and clinic patients, against 7.5% and 14.7% for its own model.
- Every test followed a plan committed before its run; three pre-registered claims failed and are reported as failures.

## Abstract

**Background.** Language-model agents are reported to diagnose rare diseases from a patient's phenotype, but three things make such reports hard to read: the public test cases come from the same papers the knowledge bases were curated from, a model may have memorised a public benchmark, and published case reports are not patients as a clinic records them.

**Methods.** We built an agent on one inexpensive general-purpose model (`deepseek-flash`, reasoning off, at most eight model calls per case) with tools over pinned public knowledge (HPO, Orphanet, published patients), and measured it with each of the three problems in view. Every evaluation hides the case's own source paper from everything the tools read and audits each tool output afterwards. Every test followed a plan committed before its run, and each system ran once. After a first version was tested on 840 held-out published cases, on cases published after the model's training cutoff and on two external patient sets, we revised it and tested the revision on sets no system had seen: 146 patients shared by families and clinicians (MyGene2) and 577 patients of diagnostic laboratories and clinics (the CADA test set).

**Results.** Unmasked, a published tool (LIRICAL) ranked the confirmed disease first in 63.2% of 840 held-out cases; masked, in 30.1%. Masked, the agent reached 42.4% (95% CI 39.1–45.8), against 14.3% for its own model asked directly and 33.0%, 27.0% and 23.5% for GPT-6.1, Gemini 4 and Claude Sonnet 5.5 on a fixed 200 of the cases. On patients curated elsewhere the first version lost to its own model (19.3% against 31.8% on a clinic's 88 patients; 24.7% against 32.7% on a registry's 624): every tool scored how well a disease explains the findings and none how common it is. Revised to weigh the model's own answer and each candidate's prevalence beside the tools' evidence, the agent ranked the confirmed disease first in 52.1% (44.0–60.0) of MyGene2 patients against 7.5% for its own model (cases only one solved, 69 : 4; Holm-adjusted p < 0.001) and in 23.6% (20.3–27.2) of CADA patients against 14.7% (73 : 22; p < 0.001). Within CADA the lead was established for laboratory submissions and published cases but not for the 205 patients of collaborating clinics (20.0% against 15.6%; 19 : 10, p = 0.14). A frontier model asked directly, run on MyGene2 only, was level with the agent there (GPT-6.1: 54.8%).

**Conclusions.** A plain agent on an inexpensive model adds most where the model alone knows least — rare diseases, in patients with several recorded findings — and what it achieves on patients is far below what an unmasked benchmark of published cases would suggest. Benchmarks of phenotype-driven diagnosis on published cases should mask each case's source, and a system should be tested outside the source it was developed on before its accuracy is quoted.

**Keywords:** rare disease; differential diagnosis; large language model; agent; Human Phenotype Ontology; data leakage; pre-registration

## 1. Introduction

A patient with a rare disease often waits years for a diagnosis. Phenotype-driven tools were built to shorten that wait: given the patient's findings as Human Phenotype Ontology (HPO) terms [10], they rank the diseases whose annotated phenotype fits best [1–3]. Large language models (LLMs) have since been put to the same question, asked directly [4,5] and as agents that call such tools, search the literature and reason over what they find [6–8]. The reported accuracies are high — a recent agentic system reports ranking the confirmed diagnosis first in 57% of cases on average across nine datasets [6] — and they are hard to read, for three reasons.

**Benchmarks leak through the knowledge base.** The public test cases are published case reports, and HPO's disease annotations are curated from published case reports — often the same ones. A tool that reads the annotations while it is tested on the very patient they were written from is, in part, reading the answer. The effect has been noted [25] but is rarely controlled, and its size on a standard benchmark has not, to our knowledge, been measured for a published tool.

**A model may have read the test.** A benchmark that was public before a model's training data ends can be memorised. A model asked directly then looks stronger than it is, and so does any agent built on it; the same benchmark can also make an agent look weaker than its own model when the agent fails to use what the model remembers.

**Published cases are not patients.** A case report describes a patient the authors chose, after the diagnosis was known. Patients as a clinic or a diagnostic laboratory records them have fewer findings, and more of them have the commoner rare diseases, which curated annotations describe thinly [17,18].

This paper reports an agent built and measured with each of the three in view. The agent itself is deliberately plain: one inexpensive general-purpose model with reasoning mode off, six tools over pinned public knowledge, at most eight model calls per case, for under one US cent. What we consider the contribution is how it was measured, and what the measurement showed:

1. Every evaluation hides each case's own source paper from everything the tools read, and audits every tool output afterwards. We quantify what the mask removes: for a published tool on published cases, about half of its score.
2. Every test followed a plan committed to the public repository before its first run — the cases, the systems, the single comparison that decides the primary claim — and each system ran once. Three pre-registered claims failed; they are reported as failures, with the cause we found.
3. After the first version lost to its own model on patients curated elsewhere, we found the cause in its traces, revised it, and tested the revision on sets that no system had been run on and that no one had read: patients shared by families and clinicians (MyGene2 [13,26]), patients of diagnostic laboratories and clinics (the CADA test set [14]). [[CASEREPORTS-INTRO]]

## 2. Methods

### 2.1 Task and scoring

A system is given a patient's findings as HPO terms and nothing else — no diagnosis, no gene, no source — and answers with up to ten diseases, best first, each with an OMIM or Orphanet identifier. A case is solved at rank *k* when one of the first *k* identifiers is the confirmed diagnosis, or an identifier that Mondo [11] (release 2026-09-01) maps to it exactly. Names are not compared. A case with no answer is a miss and stays in the denominator. Rates carry 95% Wilson intervals [21]. Two systems are compared on the same cases by the two-sided exact sign test on the cases that exactly one of them solves; where several tests answer one question each, their p-values are corrected by Holm's method [22].

Systems that write disease names more reliably than identifiers (models asked directly, DeepRare) were also scored by name with DeepRare's own judging prompt [6]; the two scorings are reported side by side, and pre-registered claims are decided by identifiers.

### 2.2 Cases

Table 1 lists every set of cases and how it was used.

**Development and held-out cases.** Phenopacket Store 0.1.27 [9,19] holds 10,374 published patients with HPO-coded findings and a confirmed OMIM diagnosis, from 1,733 papers (780 diseases). Papers, not patients, were split before any development: 6,014 patients for development (the "design" split, which also fills the bank of similar patients that one tool searches) and 4,360 patients from 840 papers held out. A development set of 200 cases, one per paper, was used for every design decision. The held-out test takes one case from each of the 840 papers; other providers' models and DeepRare were run on a fixed random 200 of them.

**Temporal test.** One case from each paper added to the store that first became public on or after 1 June 2025, the reported end of the model's training data (47 cases). A paper's first public day is the earliest of PubMed's entry, electronic-publication and issue dates.

**External sets used once, then developed on.** RareBench's [4] HMS (88 patients of a clinic at Hannover Medical School) and RAMEDIS (624 patients of a registry of metabolic diseases) tested the first version; after their errors were read they became development sets. RareBench's MME (40 published cases) tested the first two versions and then joined them. Further development sets were 498 case reports from RareArena [20], read into HPO terms, and 300 of the CADA training patients.

**Tests of the revised agent**, registered before any system ran on them and read by no one beforehand:

- *MyGene2* [26]: patients' features and causal genes shared on mygene2.org by families and clinicians, as preprocessed for SHEPHERD [13] (146 patients with an OMIM diagnosis; CC0). DeepRare reports on the same file [6]. A PubMed identifier, given for 54 patients, was masked like any case's source.
- *CADA test set* [14]: ClinVar submissions that carry HPO terms, from diagnostic laboratories and research programmes, and patients of the CADA authors' collaborating clinics. We kept the authors' own split: of their test file, the 577 patients with an OMIM diagnosis are the test; of their training file, a fixed random 300 were developed on; their validation file was left unread. Of the 577, 239 are ClinVar submissions, 205 are patients of the collaborating clinics and 133 are published cases that the CADA authors had compiled for an earlier study. The median patient has five findings (interquartile range 2–11), and almost a third (182) have one or two.
*Case reports after the cutoff.* The set was built by a fixed procedure, committed with its rules before any report was read. Candidates were the 71,351 PubMed case reports in English with open-access full text that entered PubMed between 1 June 2025 and 24 October 2026, put in one random order by a fixed seed and processed in that order. Two independent annotators named each report's diagnosis: PubTator3 [15] from the title and abstract (MeSH identifiers, mapped through Mondo), and the model from the title, abstract and case description. A report was kept only if its title named exactly one rare disease of the knowledge base (one that Orphanet lists [12]) and the model's diagnosis, matched by name against every name and exact synonym of each disease, was that disease. Disagreements were dropped, not adjudicated. The case description — the paragraphs that the PMC BioC service [16] types as the case — was then cut before the first sentence that gives the diagnosis away: the sentence the model pointed to; the first sentence in which a program finds the disease's name, a synonym or its gene; or the first sentence that reports a confirming test (a biopsy, histology, a culture, sequencing, antibodies and the like), whichever is earliest. Nothing was rewritten. Each disease was assigned to the test side or the development side by a draw that depends only on the disease and the seed, so the two sides share no disease. The kept text was read into HPO terms by the note reader (Section 2.4), and every system received the same terms. The procedure was piloted on reports from before the cutoff; an audit of 30 development-side reports of a first, unfinished build found the answer key right in all 30 and the diagnosis still readable in about six, after which the cut was made stricter (the confirming-test rule) and the set rebuilt from the start. No one read the test side before the test.

### 2.3 Knowledge and leakage control

The tools read HPO's disease annotations (release 2026-09-01; 8,478 OMIM diseases) and, in the agent's second revision, Orphanet's as well, merged by Mondo's exact matches (2,122 Orphanet entries merged into their OMIM disease; 2,233 Orphanet diseases of their own), together with Orphanet's prevalence classes and short disease descriptions from Orphanet and MedlinePlus Genetics.

While a system works on a case, the case's source paper is masked from all of it (Fig. 1):

- an annotation supported only by that paper is removed; an annotation other papers also support stays, without the masked paper among its sources;
- a disease known only from that paper does not exist for any tool — not in rankings, not by name, not as a similar patient's diagnosis — and a tool asked about it answers exactly as for an identifier that was never assigned, so the model cannot tell that something is hidden;
- patients from that paper are not in the bank of similar patients.

After each run, every tool output recorded in the traces is searched for the case's own paper and for diseases known only from it; a run with a single hit is void. A case that names no paper has nothing to mask.

### 2.4 The agent

All versions run on LangChain's agent loop (LangGraph) with `deepseek-flash`, reasoning mode off, temperature 0, and at most eight model calls per case, the last of which is offered only the final answer. The tools are `rank_diseases` (every disease ranked by phenotype similarity to the patient [1]), `check_match` (the patient's findings against one disease: explained, unexplained, recorded absent, and the disease's frequent features the patient lacks), `lookup_disease`, `find_disease` (an identifier from a name), `find_similar_patients` (the closest published patients of the design split, with their diagnoses) and `search_disease_texts`.

- **v1.0** starts from the tools' evidence: the ten best candidates of a no-model ranking (the similarity's top thirty, reordered by findings explained), each with its match report. Its turns go to what the tools cannot do, such as a disease it suspects that they did not propose.
- **v1.1** first answers from the model's own knowledge, before any tool runs. Each disease it names is found in the knowledge base and checked like the tools' candidates; the first message shows both lists, each candidate with Orphanet's prevalence class, and the instructions ask the model to weigh the two as equals and, between candidates that fit comparably, to prefer the more common.
- **v2** is v1.1 with three changes, each measured without a model on the development sets beforehand: Orphanet's diseases merged into the knowledge; the tools' list taken from a one-way similarity (the patient's findings looked for in the disease, not the disease's in the patient), in its own order; and a guard on the final order — when the model's own first answer is a relatively common rare disease (Orphanet: one patient in 100,000 or more) that the tools also rank in their top thirty, it leads.

On five development sets v2 was not better than v1.1 where both can answer (Supplementary Table S2), so under a rule written beforehand v1.1 is the system tested on MyGene2 and CADA, whose diagnoses all carry OMIM identifiers; v2 is the system for the case-report set, many of whose diagnoses are Orphanet diseases that v1.1's knowledge does not contain.

A clinical note is read into HPO terms by a separate reader before diagnosis: the model lists each finding with the note's words and its status (present, denied, in a relative) and never writes an identifier; exact names are coded directly, the rest chosen among candidates from a hybrid search over HPO's names and synonyms.

### 2.5 Comparators

The same model asked once without tools; a fixed pipeline (the tools' top ten with their evidence, ranked by one model call); the no-model ranking ("rank, then check"); LIRICAL 2.4.1 [2], given for each case its own copy of the annotation file written under the mask; three other providers' current models asked directly with the same prompt (GPT-6.1, Claude Sonnet 5.5, Gemini 4); and DeepRare [6], run from its published code on the agent's model. DeepRare searches the web and its own case bank and could not be masked; everything it read was searched afterwards for each patient's own paper.

### 2.6 Plans, runs and records

Each test followed a plan committed to the repository before its first run: the cases, the systems and their frozen version, the one comparison that decides the primary claim, and the rule that each system runs once. A run that lost cases to failures of the model's API was completed by asking only those cases again. A run whose records were incomplete was void and repeated without its score being read. Every run, with every model call and tool call, is recorded with MLflow; per-case outcomes of every reported run are in the repository.

## 3. Results

### 3.1 An unmasked benchmark of published cases is about half leakage

On the 200 development cases the phenotype-similarity tool has the confirmed disease in its top ten for 82.0% of cases with each case's own paper left in the knowledge, and for 49.0% with it masked (Fig. 2). For 153 of the 200 cases, HPO's annotation of the confirmed disease cites the case's own paper. LIRICAL, a published and maintained tool, ranks the confirmed disease first in 63.2% of the 840 held-out cases unmasked and in 30.1% masked (278 cases lost, none gained). The whole difference comes from the three quarters of cases whose disease annotation cites their paper; on the remaining quarter the mask changes no answer. Under the mask, 122 of the 840 cases cannot be answered by any tool that reads the annotations: their disease is known to HPO only from the patient's own paper.

### 3.2 Held-out published cases

On the 840 held-out cases, one per paper, the first version of the agent ranked the confirmed disease first in 42.4% (95% CI 39.1–45.8) and in its top ten in 62.0% (58.7–65.2) (Fig. 3a; Table 2). The pre-registered primary claim — the agent against the fixed pipeline at first place — holds: the agent alone solved 57 cases and the pipeline alone 10 (p = 4 × 10⁻⁹). Against LIRICAL the agent alone solved 121 cases and LIRICAL alone 18. Masked, LIRICAL (30.1%) is level with the project's own no-model ranking (32.1%), which was therefore no strawman. The model inside the agent, asked directly, solved 14.3%. With simulated sequencing (fifty candidate genes per case) the agent reached 65.9% against 59.5% for a gene ranking without a model.

### 3.3 Against frontier models and another agent

On a fixed random 200 of the held-out cases (Fig. 3b), the agent's 43.0% at first place is ahead of GPT-6.1 (33.0%; paired 37 : 17, p = 0.009), Gemini 4 (27.0%; 46 : 14) and Claude Sonnet 5.5 (23.5%; 52 : 13), each asked directly with the same prompt; the agent's own model scores 15.0% alone. DeepRare, run from its code on the agent's model, scores 8.5% by identifier and 27.5% by its own name-based judging, against the agent's 43.0% and 42.5% (paired 48 : 18 under name-based judging, p < 0.001). It took a median of 27 model calls and 3.2 minutes per case, against the agent's four to eight calls and 13 seconds.

Split afterwards by Orphanet's prevalence class of the confirmed disease (not planned; descriptive), the model alone is level with the agent on the relatively common rare diseases (61.9% against 57.1%; 42 cases) and far behind on the rarest (9.6% against 52.6%; 272 cases under one patient in a million). The agent's gain over its own model is in the long tail.

### 3.4 Outside the curated source, the first version lost to its own model

Two further plans tested the frozen first version once each (Fig. 4a). On the 47 cases published after the model's training cutoff the agent solved 23.4% and the model alone 8.5% (paired 9 : 2, p = 0.065): the pre-registered claim was not established. On the two external patient sets the agent lost to its own model: 19.3% against 31.8% on HMS (4 : 15, p = 0.019) and 24.7% against 32.7% on RAMEDIS (47 : 97, p < 0.001). The claim registered for these sets — the agent against the fixed pipeline — also failed (54 : 45, p = 0.42).

Three frontier models asked directly scored below `deepseek-flash` on HMS (14.8–22.7% against 31.8%), the reverse of their order on the held-out cases, which suggests that this model has seen the public RareBench. That does not excuse the agent: it runs on the same model, and did not use what the model knew.

### 3.5 Why it lost, and what was changed

Read afterwards, the failure was one of ranking, not of retrieval. Where the model alone was right and the agent wrong, the agent's own top ten held the answer in 12 of 15 HMS cases and 85 of 97 RAMEDIS cases, and the agent had itself checked the right disease in most of them before preferring a rarer one with a richer annotation. Every tool scored how well a disease explains the findings and none how common it is. The knowledge also kept only OMIM's annotations, which describe the commoner rare diseases thinly: Behçet disease has 15 annotated findings in OMIM's entry and 85 in Orphanet's. The held-out set had hidden both problems, because it is made of published single-gene cases: only 42 of its 840 cases have a relatively common diagnosis.

The revised agent (v1.1) puts the model's own answer beside the tools' and shows each candidate's prevalence. On the temporal cases it beat the model asked directly, 10 : 2 (p = 0.039; this was the second version scored on that set, Fig. 4b). On a fresh external set of 40 published cases (MME) it was not better than the first version (72.5% against 80.0%; 1 : 4), and on HMS and RAMEDIS, now development sets, it reached 37.5% and 30.6% against the model's 31.8% and 32.7%.

### 3.6 Pre-registered tests of the revised agent on patients

The plan for these tests fixed one primary question per set — does the agent rank the confirmed disease first more often than its own model asked directly, on the same findings — and each system ran once. Both claims hold (Fig. 4c; Fig. 5; Table 3).

On **MyGene2** (146 patients, 44 diseases, median five findings) the agent ranked the confirmed disease first in 52.1% (95% CI 44.0–60.0) and in its top ten in 74.0% (66.3–80.4); the model asked directly, in 7.5% (4.3–13.0) and 34.9%. Paired, the agent alone solved 69 patients and the model alone 4 (p = 2 × 10⁻¹⁶; Holm-adjusted over the two tests, p < 0.001). The no-model ranking solved 41.1%, and the agent was ahead of it too (17 : 1, p < 0.001): on this set most of the agent's accuracy comes from its tools, and the agent adds eleven points to them.

On the **CADA test set** (577 patients, 345 diseases) the agent ranked the confirmed disease first in 23.6% (20.3–27.2) and in its top ten in 43.8% (39.9–47.9); the model asked directly, in 14.7% (12.1–17.9) and 34.8%. Paired, 73 : 22 (p = 1.5 × 10⁻⁷; Holm-adjusted p < 0.001). Here the no-model ranking is the weakest of the three (11.6%; agent against it, 71 : 2): with few findings the tools have little to rank on, and the model's own knowledge carries more of the answer. The agent gave no answer for four patients, which count as misses.

Pooled over the two sets (723 patients), the agent solved 29.3% at first place and the model 13.3% (142 : 26).

**Scoring by name.** Under DeepRare's name-based judging the model asked directly gains — on MyGene2 it rises from 7.5% to 13.7%, having often named the right disease with a wrong number — while the agent hardly moves (52.1% to 54.1%) and the no-model ranking scores 43.8%. On the CADA test set the model rises from 14.7% to 18.7% and the agent from 23.6% to 24.8%; paired, the agent's lead narrows from 73 : 22 to 75 : 40 and remains (p = 0.001). The judge was the model inside both systems. The conclusion does not depend on the scoring.

**By number of findings.** The agent's lead over its model grows with what the patient's record holds (Fig. 6). With one or two findings (199 patients) neither does well: 12.6% against 8.5% (10 : 2, p = 0.039). With three to five findings the agent solved 35.9% against 16.7% (45 : 8); with six to ten, 30.3% against 13.2% (34 : 8); with eleven or more, 40.0% against 15.0% (53 : 8).

**By where CADA's patients come from** (Table 4). The lead is not uniform. It is established for the 239 ClinVar submissions (13.4% against 7.5%; 18 : 4, p = 0.004) and for the 133 published cases (47.4% against 26.3%; 36 : 8, p < 0.001), which contribute half of the agent's advantage on this set. For the 205 patients of the collaborating clinics the agent solved 20.0% and the model 15.6% (19 : 10, p = 0.14): the same direction, not established.

**Other comparators.** LIRICAL ranked the confirmed disease first for 41.8% of MyGene2 patients and 12.0% of CADA patients, level with the project's own no-model ranking on both sets and behind the agent on both (paired 18 : 3, p = 0.001, and 75 : 8, p < 0.001). The credit left for other providers' models allowed one such comparison: GPT-6.1 asked directly on MyGene2. It ranked the confirmed disease first for 54.8% (46.7–62.6) and in its top ten for 75.3% — level with the agent (52.1% and 74.0%; paired 22 : 26, p = 0.67), where the agent's own model alone scored 7.5%. On the held-out published cases the same GPT-6.1 had been ten points behind the agent (Section 3.3). MyGene2 has been public since before that model's training data ends, and its 44 diseases are well-described syndromes; we cannot tell how much of the difference between the two sets is the mask and how much is the patients. The comparison was not run on CADA.

**Beside a published number.** DeepRare reports ranking the diagnosis first for 74% of the same MyGene2 file [6]. The two figures were not measured alike — DeepRare's answers were judged by name by GPT-4o, its system searches the web and its own case bank, and nothing was masked — so they cannot be ranked. We note only that the agent reaches 52–54% with an inexpensive model, pinned offline knowledge and each patient's own paper hidden.

[[CASEREPORTS-RESULTS]]

### 3.7 Cost

On these two tests the revised agent took a median of 17 seconds per patient and used about 71,000 input tokens (three quarters of them served from the provider's cache) and 2,200 output tokens, which at the provider's list price is US$0.008 per patient; the 723 patients cost US$5.76 at list price for the agent and US$0.35 for the model asked directly.

## 4. Discussion

An agent that is deliberately plain — one inexpensive model, six tools over pinned public knowledge, eight model calls — ranked the confirmed disease first for half of a set of patients shared by families and clinicians and for a quarter of a set of laboratory and clinic patients, in both cases well ahead of the same model asked directly, under plans committed before either set had been run on or read. How these numbers were obtained matters at least as much as the numbers.

**Masking is not optional.** The size of the leakage effect — half of a published tool's first-place accuracy on published cases — means that an unmasked benchmark on public case reports cannot rank methods: a method that leans harder on the annotations gains more from the leak. The mask we used is strict; it removes 122 of 840 held-out cases from what any annotation-reading tool can answer, because their disease is known to HPO only from the patient's own paper. That is the honest condition: a clinician who meets the first described patient with a disease has no annotation to read either.

**A held-out set from the development source is not an external test.** The first version passed its pre-registered held-out test with a wide margin and then lost to its own model on a clinic's and a registry's patients. Nothing in the held-out result warned of this, because the held-out cases share the development cases' distribution: published, monogenic, long phenotype lists, and almost no relatively common disease. The failure was specific and instructive — tools that score fit and ignore prevalence prefer a richly annotated rarity to a thinly annotated common disease — and it would have gone unseen had the external test not been planned and run.

**What the agent adds, and where.** The model alone knows the commoner rare diseases and almost none of the rarest; the tools know the rarest as well as their annotations allow and have no notion of how common anything is. The agent's value is in combining the two, and its gain over its own model is concentrated in the long tail. Tools do not make a small model better than a large one everywhere: on MyGene2 a single call to GPT-6.1 did as well as the agent, at about the same price per patient. What the tools give is an accuracy that does not depend on what the model happens to have read — the agent's own model knows 7.5% of those diagnoses — and evidence, for each candidate, that a clinician can check. The breakdown by number of findings says the same from another side: with one or two findings there is little for a tool to match and the two are close; from three findings on, the agent solves two to three times as many patients as its model.

**How far the result on patients reaches.** MyGene2's patients carry developmental and skeletal syndromes with several well-chosen findings; the no-model ranking alone solves 41% of them, and the agent adds to it. CADA's are harder and more mixed, and there the honest reading is narrower than the headline: the agent's lead is clear for laboratories' ClinVar submissions and for published cases, and unproven for the collaborating clinics' own patients, where every system's accuracy is low. That a quarter of the CADA test set is published cases is itself a caution about what benchmarks of “real-world” patients contain.

**Limitations.** (i) Every test is retrospective and on public, de-identified data; no clinician used the system or judged its answers, and no claim about clinical benefit is made. (ii) The agent sees only phenotype terms; a patient's sequencing data, which decides most rare-disease diagnoses, enters only as simulated candidate genes on the held-out set. (iii) One model was used throughout, and its training cutoff is known only from third-party reports. (iv) MyGene2 and CADA were public before that cutoff, so the model may have seen them; the comparison of the agent with the same model bounds, but does not remove, that concern. (v) The CADA test is restricted to patients with an OMIM diagnosis, and both real-patient sets carry diagnoses with OMIM identifiers, so they do not test the commoner rare diseases that only Orphanet lists. (vi) Scoring by identifier is strict for a model asked directly, which often names the right disease with a wrong number; name-based judging, reported alongside, used the same model family as the systems judged. (vii) The selection between the two revisions used four of five planned development sets, the fifth having been dropped for cost. (viii) The plans were written in the authors' working language (Chinese); the repository holds them with their commit history. [[CASEREPORTS-LIMITS]]

## 5. Conclusion

Measured with each case's own source hidden, on sets fixed in advance and run once, a plain tool-using agent on an inexpensive model outperforms that model at naming a rare disease from a patient's findings: on held-out published cases, on cases published after the model's training cutoff, and on two sets of patients it was not developed on. On the held-out cases it also outperforms three frontier models asked directly; on one of the patient sets, the one frontier model we could run was its equal. In its first version it also failed on a clinic's and a registry's patients, for a reason that no held-out test from its development source could have shown. We suggest three practices to anyone reporting such systems: mask each test case's source from the knowledge base; test outside the source the system was developed on before quoting its accuracy; and commit the plan before the run, so that a failure is as visible as a success.

## Declarations

**Data and code availability.** Code, manifests, plans with their commit history, and per-case outcomes of every reported run are in the project repository [URL — to be completed]. Every dataset is public and pinned by version and checksum in `evals/datasets.toml`. The case-report texts are not redistributed (some licences are non-commercial); the committed table names each paper, the number of sentences kept and the checksum of the kept text, from which the set can be rebuilt.

**Ethics.** Only public, de-identified data were used. No patient was contacted and no clinical record was accessed.

**Funding.** [to be completed]

**Competing interests.** [to be completed]

**Author contributions (CRediT).** [to be completed]

**Declaration of generative AI and AI-assisted technologies.** During the preparation of this work the author(s) used an AI coding and writing assistant (Claude, Anthropic) to write software, run analyses and draft and edit text. The author(s) reviewed and edited the content and take full responsibility for the content of the publication. [To be confirmed and adapted to the journal's wording by the authors.]

## References

[see `references.md`; inserted at conversion]

## Figure legends

**Fig. 1. How a case is asked, and what is hidden while it is.** The model first answers from its own knowledge; the tools rank every disease and check the leading candidates; the agent then weighs both lists with further tool calls. While a case is asked, its own source paper is masked from everything the tools read, and every tool output is audited afterwards.

**Fig. 2. What the mask removes.** Share of cases with the confirmed disease found, with each case's own source paper left in the knowledge (open circles) and masked (filled).

**Fig. 3. Held-out published cases (first version).** Confirmed disease ranked first, with 95% Wilson intervals. (a) 840 held-out cases, one per paper. (b) A fixed random 200 of them, with three other providers' models asked directly and DeepRare run on the agent's model (scored by identifier).

**Fig. 4. The agent against its own model asked directly, on every test.** Rates at first place with 95% intervals; at the right, the cases only the agent and only the model solved, and the two-sided exact sign test. (a) First version. (b) Revised agent on sets it was not developed on. (c) Pre-registered tests of the revised agent on patients.

**Fig. 5. The pre-registered tests on patients.** Confirmed disease ranked first, with 95% Wilson intervals, for the revised agent, its own model asked directly, and the comparators run on each set. (a) MyGene2. (b) CADA test set.

**Fig. 6. The agent and its own model by how many findings the patient has.** MyGene2 and the CADA test set pooled (723 patients). At the right, the patients only the agent and only the model solved, with the two-sided exact sign test.

## Tables

**Table 1. The sets of cases and how each was used.** A test set was run on once by each system under a plan committed beforehand.

| set | cases | what the cases are | role |
|---|---|---|---|
| Design split | 6,014 (893 papers) | published patients, Phenopacket Store | development; bank of similar patients |
| Held-out | 840 (one per paper) | published patients, papers disjoint from the design split | test of v1.0 |
| Temporal | 47 (one per paper) | published after the model's training cutoff | test of v1.0, then of v1.1 |
| HMS | 88 | a clinic's patients (RareBench) | test of v1.0, then development |
| RAMEDIS | 624 | a metabolic registry's patients (RareBench) | test of v1.0, then development |
| MME | 40 | published cases (RareBench) | test of v1.0 and v1.1, then development |
| CADA development | 300 | diagnostic-laboratory and clinic patients | development |
| **MyGene2** | **146** | patients shared by families and clinicians | **test of v1.1** |
| **CADA test** | **577** | ClinVar submissions (239), collaborating clinics' patients (205), published cases (133) | **test of v1.1** |

**Table 2. Held-out published cases, first version of the agent.** Confirmed disease at first place and in the top ten, with 95% Wilson intervals; each case's own source paper masked unless stated.

| system | top-1 | top-10 |
|---|---|---|
| *840 cases, one per paper* | | |
| Agent (v1.0) | 42.4% [39.1–45.8] | 62.0% [58.7–65.2] |
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
| Gemini 4, asked directly | 27.0% [21.3–33.5] | 42.0% [35.4–48.9] |
| Claude Sonnet 5.5, asked directly | 23.5% [18.2–29.8] | 38.5% [32.0–45.4] |
| Same model, asked directly | 15.0% [10.7–20.6] | 25.5% [20.0–32.0] |
| DeepRare on the same model, by identifier | 8.5% [5.4–13.2] | 11.5% [7.8–16.7] (top five) |

**Table 3. Pre-registered tests of the revised agent on patients.** Confirmed disease within the first *k* answers; the last column gives the patients only the agent and only the named system solved at first place, with the two-sided exact sign test.

| set | system | top-1 [95% CI] | top-3 | top-5 | top-10 | agent : system |
|---|---|---|---|---|---|---|
| MyGene2 (n = 146) | **Agent (v1.1)** | **52.1%** [44.0–60.0] | 63.0% | 68.5% | 74.0% | |
| | Same model, asked directly | 7.5% [4.3–13.0] | 18.5% | 28.8% | 34.9% | 69 : 4 (p < 0.001) |
| | Rank, then check (no model) | 41.1% [33.4–49.2] | 53.4% | 56.8% | 61.0% | 17 : 1 (p < 0.001) |
| | LIRICAL | 41.8% [34.1–49.9] | 49.3% | 53.4% | 56.2% | 18 : 3 (p = 0.001) |
| | GPT-6.1, asked directly | 54.8% [46.7–62.6] | 67.1% | 70.5% | 75.3% | 22 : 26 (p = 0.67) |
| CADA test (n = 577) | **Agent (v1.1)** | **23.6%** [20.3–27.2] | 32.6% | 36.4% | 43.8% | |
| | Same model, asked directly | 14.7% [12.1–17.9] | 22.2% | 27.0% | 34.8% | 73 : 22 (p < 0.001) |
| | Rank, then check (no model) | 11.6% [9.2–14.5] | 17.9% | 21.3% | 26.3% | 71 : 2 (p < 0.001) |
| | LIRICAL | 12.0% [9.6–14.9] | 19.9% | 23.4% | 28.6% | 75 : 8 (p < 0.001) |
| Pooled (n = 723) | **Agent (v1.1)** | **29.3%** [26.1–32.7] | 38.7% | 42.9% | 49.9% | |
| | Same model, asked directly | 13.3% [11.0–15.9] | 21.4% | 27.4% | 34.9% | 142 : 26 (p < 0.001) |

**Table 4. The CADA test set by where its patients come from.** First place.

| source | patients | agent (v1.1) | same model, asked directly | rank, then check | agent : model |
|---|---|---|---|---|---|
| ClinVar submissions | 239 | 13.4% [9.6–18.3] | 7.5% [4.8–11.6] | 6.3% [3.8–10.1] | 18 : 4 (p = 0.004) |
| Collaborating clinics | 205 | 20.0% [15.1–26.0] | 15.6% [11.3–21.2] | 8.3% [5.2–12.9] | 19 : 10 (p = 0.14) |
| Published cases | 133 | 47.4% [39.1–55.8] | 26.3% [19.6–34.4] | 26.3% [19.6–34.4] | 36 : 8 (p < 0.001) |
