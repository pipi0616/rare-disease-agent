---
title: "A tool-using agent for rare-disease diagnosis, tested where its knowledge cannot leak: held-out reports, patients from clinics and diagnostic laboratories, and reports published after the model's cutoff"
author: "[Author names and affiliations — to be completed]"
---

**Corresponding author:** [name, address, e-mail — to be completed]

## Highlights

- Masking each case's own source paper from the knowledge base halves the measured accuracy of phenotype-driven tools on published cases.
- An agent on one inexpensive model, with a handful of tools, ranks the confirmed disease first more often than three frontier models asked directly.
- Its first version lost to its own model on patients curated elsewhere; the cause, found in its traces, was a ranking blind to how common a disease is.
- [[PENDING — one highlight on the pre-registered tests on MyGene2 and CADA]]
- Every test followed a plan committed before its run; three pre-registered claims failed and are reported as failures.

## Abstract

**Background.** Language-model agents are reported to diagnose rare diseases from a patient's phenotype, but three things make such reports hard to read: the public test cases come from the same papers the knowledge bases were curated from, a model may have memorised a public benchmark, and published case reports are not patients as a clinic records them.

**Methods.** We built an agent on one inexpensive general-purpose model (`deepseek-flash`, reasoning off, at most eight model calls per case) with tools over pinned public knowledge (HPO, Orphanet, published patients), and measured it with each of the three problems in view. Every evaluation hides the case's own source paper from everything the tools read and audits each tool output afterwards. Every test followed a plan committed before its run, and each system ran once. After a first version was tested on 840 held-out published cases, on cases published after the model's training cutoff and on two external patient sets, we revised it and tested the revision on sets no system had seen: 146 patients shared by families and clinicians (MyGene2) and 577 patients of diagnostic laboratories and clinics (the CADA test set)[[PENDING — and N case reports published after the cutoff, cut before the sentence that gives the diagnosis away]].

**Results.** Unmasked, a published tool (LIRICAL) ranked the confirmed disease first in 63.2% of 840 held-out cases; masked, in 30.1%. Masked, the agent reached 42.4% (95% CI 39.1–45.8), against 14.3% for its own model asked directly and 33.0%, 27.0% and 23.5% for GPT-6.1, Gemini 4 and Claude Sonnet 5.5 on a fixed 200 of the cases. On patients curated elsewhere the first version lost to its own model (19.3% against 31.8% on a clinic's 88 patients; 24.7% against 32.7% on a registry's 624): every tool scored how well a disease explains the findings and none how common it is. [[PENDING — results of the revised agent on MyGene2 and CADA, with paired counts and corrected p-values]]

**Conclusions.** [[PENDING]] Benchmarks of phenotype-driven diagnosis on published cases should mask each case's source, and a system should be tested outside the source it was developed on before its accuracy is quoted.

**Keywords:** rare disease; differential diagnosis; large language model; agent; Human Phenotype Ontology; data leakage; pre-registration

## 1. Introduction

A patient with a rare disease often waits years for a diagnosis. Phenotype-driven tools were built to shorten that wait: given the patient's findings as Human Phenotype Ontology (HPO) terms [10], they rank the diseases whose annotated phenotype fits best [1–3]. Large language models (LLMs) have since been put to the same question, asked directly [4,5] and as agents that call such tools, search the literature and reason over what they find [6–8]. The reported accuracies are high — a recent agentic system reports ranking the confirmed diagnosis first in 57% of cases on average across nine datasets [6] — and they are hard to read, for three reasons.

**Benchmarks leak through the knowledge base.** The public test cases are published case reports, and HPO's disease annotations are curated from published case reports — often the same ones. A tool that reads the annotations while it is tested on the very patient they were written from is, in part, reading the answer. The effect has been noted [25] but is rarely controlled, and its size on a standard benchmark has not, to our knowledge, been measured for a published tool.

**A model may have read the test.** A benchmark that was public before a model's training data ends can be memorised. A model asked directly then looks stronger than it is, and so does any agent built on it; the same benchmark can also make an agent look weaker than its own model when the agent fails to use what the model remembers.

**Published cases are not patients.** A case report describes a patient the authors chose, after the diagnosis was known. Patients as a clinic or a diagnostic laboratory records them have fewer findings, and more of them have the commoner rare diseases, which curated annotations describe thinly [17,18].

This paper reports an agent built and measured with each of the three in view. The agent itself is deliberately plain: one inexpensive general-purpose model with reasoning mode off, six tools over pinned public knowledge, at most eight model calls per case, for under one US cent. What we consider the contribution is how it was measured, and what the measurement showed:

1. Every evaluation hides each case's own source paper from everything the tools read, and audits every tool output afterwards. We quantify what the mask removes: for a published tool on published cases, about half of its score.
2. Every test followed a plan committed to the public repository before its first run — the cases, the systems, the single comparison that decides the primary claim — and each system ran once. Three pre-registered claims failed; they are reported as failures, with the cause we found.
3. After the first version lost to its own model on patients curated elsewhere, we found the cause in its traces, revised it, and tested the revision on sets that no system had been run on and that no one had read: patients shared by families and clinicians (MyGene2 [13,26]), patients of diagnostic laboratories and clinics (the CADA test set [14])[[PENDING — , and case reports first public after the model's training cutoff, each cut before the sentence that gives its diagnosis away]].

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
- *CADA test set* [14]: ClinVar submissions that carry HPO terms, from diagnostic laboratories and research programmes, and patients of the CADA authors' collaborating clinics. We kept the authors' own split: of their test file, the 577 patients with an OMIM diagnosis are the test; of their training file, a fixed random 300 were developed on; their validation file was left unread. These are patients as a laboratory records them: in the development sample the median patient has four findings, and a quarter have one or two.
- [[PENDING — *Case reports after the cutoff*: description, n]]

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

[[PENDING — MyGene2 and CADA results: Table 3, Fig. 4c, Fig. 5, Fig. 6; primary claims with Holm correction; breakdown by number of findings and by submitter; name-based judging; GPT-6.1 on MyGene2; case reports if run]]

### 3.7 Cost

[[PENDING — tokens, calls, seconds and cost per case on the tests]]

## 4. Discussion

[[PENDING — first paragraph: what the new tests show]]

**Masking is not optional.** The size of the leakage effect — half of a published tool's first-place accuracy on published cases — means that an unmasked benchmark on public case reports cannot rank methods: a method that leans harder on the annotations gains more from the leak. The mask we used is strict; it removes 122 of 840 held-out cases from what any annotation-reading tool can answer, because their disease is known to HPO only from the patient's own paper. That is the honest condition: a clinician who meets the first described patient with a disease has no annotation to read either.

**A held-out set from the development source is not an external test.** The first version passed its pre-registered held-out test with a wide margin and then lost to its own model on a clinic's and a registry's patients. Nothing in the held-out result warned of this, because the held-out cases share the development cases' distribution: published, monogenic, long phenotype lists, and almost no relatively common disease. The failure was specific and instructive — tools that score fit and ignore prevalence prefer a richly annotated rarity to a thinly annotated common disease — and it would have gone unseen had the external test not been planned and run.

**What the agent adds, and where.** The model alone knows the commoner rare diseases and almost none of the rarest; the tools know the rarest as well as their annotations allow and have no notion of how common anything is. The agent's value is in combining the two, and its gain over its own model is concentrated in the long tail. [[PENDING — one sentence tying this to the breakdown by number of findings]]

**Limitations.** (i) Every test is retrospective and on public, de-identified data; no clinician used the system or judged its answers, and no claim about clinical benefit is made. (ii) The agent sees only phenotype terms; a patient's sequencing data, which decides most rare-disease diagnoses, enters only as simulated candidate genes on the held-out set. (iii) One model was used throughout, and its training cutoff is known only from third-party reports. (iv) MyGene2 and CADA were public before that cutoff, so the model may have seen them; the comparison of the agent with the same model bounds, but does not remove, that concern. (v) The CADA test is restricted to patients with an OMIM diagnosis, and both real-patient sets carry diagnoses with OMIM identifiers, so they do not test the commoner rare diseases that only Orphanet lists. (vi) Scoring by identifier is strict for a model asked directly, which often names the right disease with a wrong number; name-based judging, reported alongside, used the same model family as the systems judged. (vii) The selection between the two revisions used four of five planned development sets, the fifth having been dropped for cost. (viii) The plans were written in the authors' working language (Chinese); the repository holds them with their commit history. [[PENDING — case-report limitations if the set is tested]]

## 5. Conclusion

[[PENDING]]

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

**Fig. 4. The agent against its own model asked directly, on every test.** Rates at first place with 95% intervals; at the right, the cases only the agent and only the model solved, and the two-sided exact sign test. (a) First version. (b) Revised agent on sets it was not developed on. [[PENDING — (c) Pre-registered tests of the revised agent.]]

[[PENDING — Fig. 5, Fig. 6 legends]]
