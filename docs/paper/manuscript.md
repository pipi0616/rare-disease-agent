---
title: "Source-paper masking and prespecified tests of a low-cost tool-using agent for rare-disease diagnosis"
author: "[Author names and affiliations — to be completed]"
---

**Corresponding author:** [name, address, e-mail, ORCID — to be completed]

## Key Points

- Phenotype knowledge bases are often curated from the very case reports used as test cases; hiding each test case's source paper halved a published tool's first-place accuracy, from 63% to 30%.
- In three prespecified tests on cases never used in its development, revisions of an agent on one inexpensive language model ranked the confirmed disease's identifier first more often than that model asked directly: 52% against 8% (146 MyGene2 patients), 24% against 15% (577 CADA cases) and 20% against 9% (240 case reports published after the model's reported training cutoff).
- Judged by disease name the lead held on MyGene2 and on CADA as a whole, but not on the case reports, where roughly half to two-thirds of it was the agent retrieving the correct knowledge-base entry. It was not established for the 205 patients of CADA's collaborators' cohorts, and GPT-6.1 asked directly was not significantly different from the agent on MyGene2.
- A first version passed a held-out test from its development source but lost to its own model on a clinic's and a registry's patients: held-out cases from the development source are not an external test.
- The agent costs about one US cent per case, and every prespecified test is reported against its plan, committed beforehand.

## Abstract

Reported accuracies of language-model agents for rare-disease diagnosis rest on published cases that knowledge bases were curated from, that models may have read, and that differ from clinic patients. We built an agent on one inexpensive model (`deepseek-flash`) with tools over public phenotype knowledge, masked each case's known source paper from the tools, and fixed each test's plan in advance. Masking halved the first-place accuracy of a published tool, LIRICAL, on 840 held-out published cases (63.2% to 30.1%). In three prespecified tests on cases never used in its development, two revisions of the agent (v1.1 on the patient sets, v2 on the case reports) ranked the confirmed disease's identifier first more often than their model asked directly: 52.1% against 7.5% on 146 MyGene2 patients, 23.6% against 14.7% on 577 CADA cases and 19.6% against 8.8% on 240 case reports published after the model's reported training cutoff (Holm-adjusted p < 0.001 each), at about one US cent per case. The lead was not significant for the 205 patients of CADA's collaborators' cohorts, nor for the case reports judged by disease name (21.7% against 18.3%), where roughly half to two-thirds of it was finding the correct identifier. GPT-6.1 asked directly did not differ significantly from the agent on MyGene2 (54.8%). A first version had passed its held-out test but lost to its model on a clinic's and a registry's patients. Benchmarks should mask case sources and test outside the development source.

**Keywords:** rare disease; differential diagnosis; large language model; agent; data leakage; prespecified evaluation

## 1. Introduction

A patient with a rare disease often waits years for a diagnosis. Phenotype-driven tools were built to shorten that wait: given the patient's findings as Human Phenotype Ontology (HPO) terms [1], they rank the diseases whose annotated phenotype fits best [2–5]. Large language models (LLMs) have since been put to the same question, asked directly [6–9] and as agents or pipelines that call such tools, search the literature and reason over what they find [10–13]. The reported accuracies are high — a recent agentic system ranks the confirmed diagnosis first in 57% of cases on average across nine datasets [10] — and hard to read, for three reasons.

**Benchmarks leak through the knowledge base.** The public test cases are published case reports, and HPO's disease annotations are curated from published case reports — often the same ones. A tool that reads the annotations while it is tested on the patient they were written from is, in part, reading the answer. Standard corpora and frameworks for benchmarking these tools exist [14,15], but the overlap is rarely controlled — one recent study removed it before its evaluation [13] — and its effect on a published tool has not, to our knowledge, been reported.

**A model may have read the test.** A benchmark public before a model's training data ends can be memorised, and a model asked directly, and any agent built on it, then looks stronger than it is.

**Published cases are not patients.** A case report describes a patient the authors chose, after the diagnosis was known. Patients as clinics and laboratories record them have fewer findings, and more of them have the commoner rare diseases [16,17].

We built a deliberately simple agent — one inexpensive model, five or six tools over pinned public knowledge, at most eight model calls, about one US cent per case — so that what it adds can be traced to its tools rather than to scale, and measured it with the three problems in view. We make three contributions. First, we measure how much a benchmark of published cases leaks through the knowledge base, by masking each case's source paper from everything the tools read. Second, we show that a held-out test from the development source missed a failure that external patients exposed, and what caused it. Third, we test the revised agent, under one plan, on three sets whose cases were never used in its development — patients shared by families and clinicians (MyGene2 [18,19]), patients of diagnostic laboratories and clinics (CADA [20]), and case reports that entered PubMed after the model's training cutoff — and find it ahead of its own model on all three when answers are scored by identifier; we report how much of that lead is diagnosis and how much is retrieval of the correct knowledge-base entry. Every prespecified test is reported against its plan, committed beforehand, including the three prespecified claims that failed.

## 2. Methods

### 2.1 Task and scoring

A system is given a patient's findings as HPO terms, and the patient's sex where recorded, and nothing else; findings recorded as absent are withheld from every system. It answers with up to ten diseases, best first, each with an OMIM or Orphanet identifier. A case is solved at rank *k* when one of the first *k* identifiers is the confirmed diagnosis or one that Mondo [21] (release 2026-09-01) maps to it exactly; for a disease with genetic subtypes this asks for the subtype. A case without an answer is a miss. Rates carry 95% Wilson intervals [22]. Two systems are compared on the same cases by the two-sided exact sign test on the cases only one of them solves ("a : b"); paired differences with Wald intervals were added after the tests; the three primary tests of Section 3.4 are corrected together by Holm's method [23], and other p-values are unadjusted. Answers were also judged by name with DeepRare's prompt [10], which asks a model whether each of the first five names denotes the confirmed disease; the judge was `deepseek-flash`, the model inside the systems it judged. Prespecified claims are decided by identifiers.

### 2.2 Cases

Table 1 lists every set, how it was used and which version it tested; Supplementary sections S1 and S3 give details.

**Development and held-out cases.** Phenopacket Store 0.1.27 [14,24] holds 10,374 published patients with a confirmed OMIM diagnosis from 1,733 papers. Papers were split before any development into a design split (6,014 patients, also the bank of similar patients one tool searches) and 840 held-out papers, one case each; a fixed random 200 of these were used for other providers' models and DeepRare. Every design decision of v1.0 used 200 development cases, one per paper.

**Temporal and external tests of the first version.** The temporal test takes one case from each paper in the store first public on or after 1 June 2025, the reported end of the model's training data (47 cases, 21 of them also in the held-out set). RareBench's [6] HMS (88 patients of one clinic) and RAMEDIS (624 patients of a metabolic registry) were external tests and then, once their errors had been read, development sets, as were RareBench's MME (40 published cases that name no source), 498 RareArena case reports [25] and 300 CADA training patients.

**Prespecified tests of the revised agent**, fixed in one plan before any system ran on them; no one had read their cases:

- *MyGene2* [19]: features and causal genes shared by families and clinicians, as preprocessed for SHEPHERD [18] (146 patients with an OMIM diagnosis). Distal arthrogryposis types account for 54 patients and three other syndromes for 40; 26 patients share their exact set of findings with another. Fifty-four patients (not the same 54) name a source paper, which was masked.
- *CADA test set* [20]: of the authors' test file, the 577 patients with an OMIM diagnosis — 239 ClinVar submissions, whose label is the condition a laboratory asserted for a pathogenic variant; 205 patients of seven cohorts of the CADA authors' collaborators (Tübingen and others); and 133 of the PEDIA cohort, of whom 108 were submitted by named individuals and 25 are labelled as published cases. No CADA case names its source, so none could be masked. Median five findings; 182 cases have one or two. Because 300 cases of the authors' training file were a development set, the test file is held out from a development source rather than external.
- *Case reports after the cutoff* (Supplementary S3): PubMed case reports with open full text that entered PubMed between 1 June 2025 and 24 October 2026 and were first public on or after 1 June 2025, in a seeded random order. A report was kept when its title named one disease that Orphanet lists [26] and two automatic annotators — PubTator3 [27] and the model, whose answer was matched to the knowledge base by the agent's own name matcher — agreed on it. The case description from the PMC BioC service [28] was cut, without rewriting, before the first sentence that names the disease or its gene, reports a confirming test, or was pointed to by the model, and read into HPO terms by the note reader (Section 2.4). Diseases were drawn to a test or a development side. The test side holds 240 reports of 142 diseases, first public up to 8 July 2026 (median ten findings); 141 of the 240 reports have a diagnosis with no OMIM entry, and many are not Mendelian (infections, tumors, autoimmune diseases). An audit of 30 development-side reports found the key right in 29 and the diagnosis still readable in 3 (95% CI 3.5–25.6%).

### 2.3 Knowledge and masking

The tools read HPO's disease annotations (release 2026-09-01; 8,478 OMIM diseases) and, in v2, Orphanet's as well, merged by Mondo's exact matches (2,122 merged into an OMIM disease; 2,233 kept as Orphanet-only diseases), with Orphanet's prevalence classes and disease descriptions from Orphanet and MedlinePlus Genetics. While a system works on a case, the case's source paper is masked from all of it (Fig. 1): annotations supported only by that paper are removed; a disease known only from it does not exist for any tool, which answers as for an identifier never assigned; and its patients leave the bank of similar patients. The mask removes whole papers, including what they say about their other patients, but cannot remove annotations that cite no paper: 30.6% of HPO's phenotype annotations of OMIM diseases cite only OMIM entries, and Orphanet's cite none. It is therefore neither an upper nor a lower bound on the leak. After each run every tool output is searched for the case's paper and for diseases known only from it; a single hit voids the run.

### 2.4 The agent

All versions run on LangChain's agent loop with `deepseek-flash`, reasoning off, temperature 0, and at most eight model calls per case. The tools rank every disease by phenotype similarity [2], check one disease against the findings, look a disease up, find an identifier from a name, find the closest published patients, and (from v1.1) search disease descriptions.

- **v1.0** starts from the tools' ten best candidates, each with its match report. Tested on the held-out, temporal, HMS and RAMEDIS sets, and once on MME without a prespecified comparison.
- **v1.1** first answers from the model's own knowledge; each disease it names is looked up — by the identifier written if the knowledge knows it, otherwise by name — and checked like the tools' candidates, with each candidate's Orphanet prevalence class shown, and the model is asked to prefer the more common of comparably fitting candidates ("relatively common": one patient in 100,000 or more). Tested on MyGene2 and CADA. An earlier form (v1.1a, prompts still asking for a Mendelian disease and an OMIM number) was run without a prespecified comparison on the temporal cases, MME and the fixed 200 held-out cases, and on RAMEDIS once it had become a development set (Supplementary Table S11).
- **v2** adds Orphanet's diseases to the knowledge, takes the tools' list from a one-way similarity (the patient's findings looked for in the disease [2,5]), and lets the model's own first answer lead when it is relatively common and in the tools' top thirty. Tested on the case reports.

A rule — stated in the plan to have been written before v2's development results were seen, but first committed together with four of them — chose v1.1 for MyGene2 and CADA, whose diagnoses carry OMIM identifiers: on the four of five planned development sets that were run, v2 was not better (Supplementary S2). That v2 would nevertheless be tested on the case reports, many of whose diagnoses v1.1's knowledge does not contain, was decided after those four sets had been run, and v2 had not been run on case reports before. Clinical notes are read into HPO terms by a separate reader that lists each finding with the note's words and its status and never writes an identifier (Supplementary S5); its prespecified primary claim — better than both baselines on clinical notes — failed: it beat the model writing identifiers (58 : 5) but not a dictionary of HPO names (29 : 38, p = 0.33). Prompts are in Supplementary S4.

### 2.5 Comparators

The same model asked once without tools ("asked directly"; asked for an OMIM identifier on the held-out, temporal and external sets, and for an OMIM or Orphanet identifier on the three later tests); a fixed pipeline (the tools' top ten ranked by one model call); three rankings without a model — phenotype similarity, the nearest published patients, and "rank, then check" (v1.0's starting list); LIRICAL 2.4.1 [3], phenotype only, on OMIM's diseases, with each case's own masked annotation file; GPT-6.1, Claude Sonnet 5.5 and Gemini 4 asked directly with the same prompt; and DeepRare [10], run from its published code on the agent's model with its case bank limited to the public RareArena cases [25] and the other substitutions in Supplementary Table S8. DeepRare searches the web and could not be masked; its reading was searched for each patient's paper. On the case reports the comparators were the model asked directly, LIRICAL, rank-then-check and v2's starting list without a model. Model identifiers and dates are in Supplementary S12.

### 2.6 Plans and records

Each prespecified test followed a plan committed to the project's git repository before its first run, fixing the cases, the systems and their version, the comparison that decides the primary claim, and that each system is scored once. The plans state twelve primary claims; nine held and three failed (Supplementary S7), and primary claims were not adjusted across plans. One plan was changed, with a dated note, after part of its results had been seen: questions lost to API failures were asked again instead of the run being voided. Commit times come from the authors' git client and the plans are written in Chinese; Supplementary section S7 lists each plan's commit and summarises the last one in English. A run with incomplete records was void and repeated without its score being read (Supplementary S6). Every model and tool call is recorded with MLflow. Per-case outcomes of most prespecified tests and other runs are in the repository; a few development and secondary figures are recorded only in the plan documents (Supplementary S9). Analyses not named in a plan are marked as unplanned. An AI assistant (Claude, Anthropic) wrote most of the software, ran the analyses and drafted the text under the authors' direction (Supplementary S9).

## 3. Results

Masking halved a published tool's accuracy (3.1). The first version led its model and every other comparator on masked held-out cases (3.2) but lost to its own model on external patients (3.3). Revised, it led its model in all three prespecified tests (3.4), with a lead made partly of diagnosis and partly of retrieving the correct entry (3.5), at about one US cent per case (3.6).

### 3.1 Masking each case's source paper halves a published tool's first-place accuracy

LIRICAL ranked the confirmed disease first in 63.2% of the 840 held-out cases unmasked and in 30.1% masked (278 cases lost, none gained). For three quarters of the cases HPO's annotation of the confirmed disease cites the case's own paper, and the whole difference comes from them. Part of it is that 122 cases cannot be answered under the mask at all — for 119 the disease is known to HPO only from the patient's own paper, for 3 HPO lacks it; on the 718 cases that stay answerable, LIRICAL still falls from 62.4% to 35.2%. The project's own rankings lose as much (Fig. 2). The mask lowers every annotation-reading method alike without reordering them; what it changes is their standing against a model asked directly, which reads no annotations.

### 3.2 On masked held-out cases the first version led its comparators

On the 840 held-out cases v1.0 ranked the confirmed disease first in 42.4% (95% CI 39.1–45.7) (Fig. 3a; Table 2). Its prespecified claims held: against the fixed pipeline 57 : 10 (p = 4 × 10⁻⁹) and against LIRICAL 121 : 18; against its own model asked directly (14.3%) it was 257 : 21. On the fixed 200 (Fig. 3b) it was ahead of GPT-6.1 (37 : 17, p = 0.009), Gemini 4 (46 : 14) and Claude Sonnet 5.5 (52 : 13) asked directly, and of DeepRare by identifier (71 : 2) and by name (48 : 18); DeepRare ran under conditions not its own (Section 2.5), and the result does not bear on its published figures.

### 3.3 A held-out test from the development source missed a failure that external patients exposed

Two plans tested v1.0 once more (Fig. 4a). On the 47 temporal cases it solved 23.4% and its model 8.5% (9 : 2, p = 0.065): not established. On two external patient sets it lost to its own model: 19.3% against 31.8% on HMS (4 : 15, p = 0.019) and 24.7% against 32.7% on RAMEDIS (47 : 97, p < 0.001); the prespecified claim against the fixed pipeline, on the two sets pooled, also failed (54 : 45, p = 0.42; HMS 12 : 6, RAMEDIS 42 : 39). Judged by name, DeepRare was ahead of v1.0 on HMS (38.6% against 20.5%; 8 : 24, p = 0.007). Supplementary Table S11 gives the other comparators on these sets.

The traces pointed to ranking rather than retrieval. Where the model alone was right and v1.0 wrong, v1.0's own top ten held the answer in 12 of 15 HMS and 85 of 97 RAMEDIS cases, and v1.0 had usually checked it before preferring a rarer disease with a richer annotation. The tools score fit, not prevalence, and OMIM describes the commoner rare diseases thinly — Behçet disease has 15 annotated findings in OMIM and 85 in Orphanet. The held-out set had hidden this: only 42 of its 840 cases have a relatively common disease. On those 42 the model asked directly solved 61.9% and v1.0 57.1%; on the 272 rarer than one in a million, 9.6% against 52.6% (unplanned). Whatever made the model right on HMS, it knew answers the agent did not use; v1.1 was built to use them. On RAMEDIS, by then a development set, v1.1a was still behind the model asked directly (30.6% against 32.7%; 56 : 69).

### 3.4 Revised, the agent ranked the confirmed disease first more often than its model in all three prespecified tests

On **MyGene2**, v1.1 solved 52.1% (95% CI 44.0–60.0) and its model asked directly 7.5% (4.3–13.0): 69 : 4, a difference of 44.5 points (35.6–53.4). On the **CADA test set**, 23.6% (20.3–27.2) against 14.7% (12.1–17.9): 73 : 22, 8.8 points (5.6–12.1). On the **case reports**, v2 solved 19.6% (15.1–25.1) against 8.8% (5.8–13.0): 30 : 4, 10.8 points (6.3–15.4). Holm-adjusted, p < 0.001 for each (Fig. 4b; Fig. 5; Table 3, which also gives the top three, five and ten). In the top ten, 64 : 7, 88 : 36 and 59 : 3. Pooled over the two patient sets (723 cases), 29.3% against 13.3% (142 : 26).

### 3.5 What the lead is made of

**More than either part.** The agent was ahead of its tools without a model on every set (17 : 1 on MyGene2, 71 : 2 on CADA, 35 : 5 against v2's starting list on the case reports) and of LIRICAL (18 : 3, 75 : 8, 45 : 0; on the case reports LIRICAL reads only OMIM's diseases, which include 99 of the 240 diagnoses). The tools alone carried much of MyGene2 (41.1%); on CADA, whose patients have few findings, the tools alone solved 11.6% and the model more.

**Clustering and scoring.** Counted by disease (unplanned), the agent solved more of a disease's patients than its model for 14 diseases and fewer for 2 on MyGene2, 53 against 13 on CADA and 28 against 4 on the case reports. Judged by name, the model gains (MyGene2 13.7%, CADA 18.7%) and the agent's lead remains on MyGene2 (66 : 7) and on CADA as a whole (75 : 40, p = 0.001). Looking the model's answers up the way the agent looks up its own leaves it unchanged on both sets (unplanned): its errors are rarely invalid codes, and where the name judge credits it (9 more first places on MyGene2, 23 on CADA) it named the right disease with a wrong identifier, on CADA mostly the wrong subtype.

**Where it is weaker** (descriptive). On CADA the lead was clear for the ClinVar submissions (18 : 4) and for the PEDIA cohort (36 : 8), but not for the 205 patients of the collaborators' seven cohorts (20.0% against 15.6%; 19 : 10, p = 0.14); judged by name (unplanned) it was not significant for the ClinVar submissions or the collaborators' cohorts (Table 4). Without the 25 cases labelled as published (unplanned), the agent solved 22.8% of the remaining 552 and its model 14.9% (65 : 21, p < 0.001; counted by disease 47 : 12; judged by name 69 : 34, p < 0.001). By number of findings the lead on CADA was small with up to five findings and clear from six on (Fig. 6; Supplementary Table S10), a pattern partly confounded with cohort — 111 of the 260 cases with six or more findings are from the PEDIA cohort; outside it, 17 : 7 with up to five findings and 20 : 7 with six or more (unplanned).

**On the case reports, roughly half to two-thirds of the lead is retrieving the correct entry** (Table 5; unplanned). Judged by name, the agent solved 21.7% and its model 18.3% (18 : 10, p = 0.18). On the 141 reports without an OMIM entry the model named the right disease first 24 times but gave its identifier 3 times — the Orphanet codes it wrote mostly exist but name other diseases — and the agent gave it 20 times. On the 99 reports with an OMIM disease the two scorings point the same way (12 : 3 by identifier, p = 0.035; 11 : 4 by name, p = 0.12). Of the 10.8-point lead, 5.0 points remain against the model's answers looked up by name (21 : 9) and 3.3 under the name judge (18 : 10), so 54–69% of it is retrieval; on the 141 reports without an OMIM entry, nearly all of it is retrieval (18 : 1 by identifier, 7 : 6 by name).

### 3.6 Against a frontier model, and cost

GPT-6.1 asked directly on MyGene2 solved 54.8% (46.7–62.6), not significantly different from v1.1 (22 : 26; −2.7 points, −12.0 to 6.6), so a deficit of up to 12 points is not excluded; MyGene2 was public before its training data end. Split afterwards (unplanned), the agent solved more of the 54 distal arthrogryposes (14 : 6, p = 0.12) and GPT-6.1 more of the other 92 patients (8 : 20, p = 0.036) and of the 54 whose source paper was masked for the agent but not for GPT-6.1 (7 : 18, p = 0.043). DeepRare reports 74% on the same file [10], judged by name with web search and no mask; the figures are not comparable. v1.1 took a median of 17 seconds and US$0.008 per patient at list price, GPT-6.1 asked directly US$0.007 and its own model US$0.0005; v2 on the case reports US$0.010 per report.

## 4. Discussion

Measured with each known source masked, on cases never used in its development, a tool-using agent on one inexpensive model ranked the confirmed disease's identifier first more often than its own model in all three prespecified tests, and was ahead of its tools alone on each.

**Benchmark leakage can be large.** Masking each case's source paper halves an annotation-reading tool's first-place accuracy on published cases without changing the order of such tools. Unmasked benchmarks therefore favour them over models asked directly and over agents whose gains come from elsewhere. A paper-level mask is not an exact measure — it removes what a paper says about its other patients and misses annotations that cite no paper — but on the cases that stay answerable the drop is still from 62% to 35%.

**Tools and model are complementary.** On the patient sets the model's errors were rarely invalid codes, and looking its answers up did not repair them; the tools supplied the ranking, and on CADA's sparse records the model supplied more. On held-out published cases v1.0's gain over its model was largest for diseases rarer than one in a million (unplanned); on CADA the lead grew with the number of findings, a pattern partly confounded with where the cases came from and not tested for interaction.

**Retrieving the right entry is a contribution of tools, not a diagnosis.** A valid identifier for the wrong disease passes any format check; on the case reports, finding the right one is much of what the tools add. A clinician or a downstream tool needs that entry, but the diagnostic gain beyond it was not established by the name judge.

**External tests catch what held-out tests miss.** The first version failed for a reason — ranking blind to prevalence — that phenotype matching has met before [3,29] and that its held-out test, with 42 cases of a relatively common disease among 840, did not reveal.

**Frontier models and cost.** On MyGene2 the inexpensive model with tools was not significantly different from GPT-6.1 asked directly at similar cost, but the interval allows a deficit of up to 12 points, and GPT-6.1 solved more outside the distal arthrogryposes and where the agent's source was masked (both unplanned). The agent records, for each candidate, the evidence it used; whether that helps clinicians was not tested.

**Limitations.** The tests are retrospective, on public de-identified data, without clinicians, and use phenotype terms only. The agent used one model throughout; its training cutoff is known only from third-party reports, and MyGene2 and CADA were public before it. The mask could not act on CADA or on 92 of the 146 MyGene2 patients. Exact-match scoring asks for genetic subtypes a phenotype often cannot decide and favours systems that look identifiers up; the name judge was the systems' own model, unchecked by a clinician. The choice of v1.1 used four of five planned development sets, and v2 for the case reports was decided afterwards; v1.1 was not run on the case reports nor v2 on the patient sets, and Claude Sonnet 5.5 and Gemini 4, and GPT-6.1 beyond MyGene2, were not run on the new sets. CADA's test file comes from a source that also supplied a development set. Each system was run once, and run-to-run variation at temperature 0 was not measured. The plans are in Chinese and timed only by git. On the case reports the answer key, the reader and the systems share one model, reports were kept only when the model's diagnosis resolved through the agent's own name matcher, and about one report in ten stays readable. The fixed pipeline was not run on the new sets.

## 5. Conclusion

With each case's known source masked and every test fixed in advance, a simple tool-using agent on an inexpensive model ranked the confirmed disease's identifier first more often than that model on held-out published cases, on two patient sets and on case reports published after the model's cutoff; on the last, roughly half to two-thirds of the lead was retrieving the correct entry, and judged by name the lead there was not significant. Its first version failed on external patients for a reason its held-out test did not reveal. Benchmarks should mask each case's source, test outside the development source, and fix the plan before the run.

## Declarations

**Data availability.** Code, manifests, plans with their commit history, and per-case outcomes of most reported runs are in the project repository [URL and archived DOI — to be completed]. Every dataset is public and pinned by version and checksum in `evals/datasets.toml`. The case-report texts are not redistributed (some licences are non-commercial); the committed table names each paper, the sentences kept and the checksum of the kept text, from which the set can be rebuilt.

**Ethics.** Only public, de-identified data were used. No patient was contacted and no clinical record was accessed.

**Funding.** [to be completed]

**Acknowledgements.** [to be completed]

**Conflict of interest.** [to be completed]

**Author contributions.** [to be completed]

**Use of generative AI.** An AI assistant (Claude, Anthropic) wrote most of the software, ran the analyses and drafted and edited the text under the authors' direction (Section 2.6; Supplementary S9). The authors reviewed the code, results and text and take full responsibility for the content. [To be confirmed by the authors.]

**Author biographies.** [About 30 words per author — to be completed.]

## References

[see `references.md`; inserted at conversion]

## Figure legends

**Fig. 1. How a case is asked, and what is hidden while it is.** The model first answers from its own knowledge; the tools rank every disease and check the leading candidates; the agent then weighs both lists with further tool calls (v1.1 and v2; v1.0 starts from the tools' list only and shows no prevalence). While a case is asked, its known source paper, where one is named, is masked from everything the tools read, and every tool output is audited afterwards. Tools: rank_diseases (phenotype-similarity ranking), check_match (one disease against the findings), lookup_disease, find_disease (an identifier from a name), find_similar_patients (the closest published patients) and search_disease_texts (disease descriptions; v1.1 and v2 only). HPO: Human Phenotype Ontology.

**Fig. 2. What the mask removes.** Share of the 840 held-out cases with the confirmed disease found, with each case's own source paper masked (filled circles) and unmasked (open circles): at first place for LIRICAL and for two of the project's three rankings without a model (rank, then check; phenotype similarity), and in the top ten for the phenotype similarity. Cases lost : gained under the mask: LIRICAL 278 : 0; rank, then check 301 : 1; phenotype similarity 257 : 1 at first place and 274 : 4 in the top ten. No intervals are drawn.

**Fig. 3. Held-out published cases, v1.0.** Confirmed disease ranked first, with 95% Wilson intervals, scored by identifier; each case's own source paper masked for every system except DeepRare, which searches the web and could not be masked. (a) 840 held-out cases, one per paper (the nearest published patients, 27.9%, are in Table 2). (b) A fixed random 200 of them, with LIRICAL, three other providers' models asked directly and DeepRare run on the agent's model; judged by name, DeepRare solved 27.5% and the agent 42.5% (Table 2).

**Fig. 4. The agent against its own model asked directly, on every prespecified test set.** The comparison was the primary claim on the temporal set and in panel b, and a prespecified secondary comparison on the held-out, HMS and RAMEDIS sets. Rates at first place, scored by identifier, with 95% Wilson intervals; at the right, the cases only the agent and only the model solved, with the two-sided exact sign test (unadjusted). (a) v1.0. (b) The revised agent: v1.1 on the two patient sets, v2 on the case reports. Values are in Tables 2 and 3 and Supplementary Table S11; v1.1a, run without a prespecified comparison, is in Supplementary Table S11.

**Fig. 5. The three prespecified tests of the revised agent.** Confirmed disease ranked first, with 95% Wilson intervals, scored by identifier, for the agent, its own model asked directly, and the comparators run on each set, in the order of Table 3. (a) MyGene2 (v1.1). (b) CADA test set (v1.1). (c) Case reports published after the cutoff (v2; one-way similarity is v2's starting list; rank, then check and LIRICAL read only OMIM's diseases, which include 99 of the 240 diagnoses).

**Fig. 6. The agent and its own model asked directly, by the number of findings per case** (HPO terms recorded as present). (a) MyGene2, v1.1. (b) CADA test set, v1.1. (c) Case reports published after the cutoff, v2. Confirmed disease ranked first, scored by identifier, with 95% Wilson intervals; at the right, the cases only the agent and only the model solved, with the two-sided exact sign test (unadjusted; a secondary analysis named in the plan, descriptive). Values are in Supplementary Table S10.

## Tables

**Table 1. The sets of cases and how each was used.** Source masked: yes, each case's own source paper was masked; no source, the cases name none; cannot be, a source exists but is not given; 54 of 146, only those cases name one; —, not applicable (development data). Bold: the three prespecified tests of the revised agent. HMS, RAMEDIS and MME are subsets of RareBench [6].

| set | cases | what the cases are | source masked | role |
|---|---|---|---|---|
| Design split | 6,014 (893 papers) | published patients, Phenopacket Store | — | development; bank of similar patients |
| dev-200 | 200 (one per paper) | from the design split | yes | development: every design decision |
| Held-out | 840 (one per paper) | published patients, papers disjoint from the design split | yes | prespecified test of v1.0 |
| Temporal | 47 (one per paper) | published after the model's training cutoff (21 also in the held-out set) | yes | prespecified test of v1.0; v1.1a afterwards |
| HMS | 88 | a clinic's patients (RareBench) | no source | prespecified test of v1.0; then development |
| RAMEDIS | 624 | a metabolic registry's patients (RareBench) | no source | prespecified test of v1.0; then development |
| MME | 40 | published cases (RareBench) | cannot be | v1.0 and v1.1a once each; then development |
| RareArena sample | 498 | case reports read into HPO terms | yes | development |
| CADA development | 300 | from the CADA training file | no source | development |
| **MyGene2** | **146** | patients shared by families and clinicians | 54 of 146 | **prespecified test of v1.1** |
| **CADA test** | **577** | ClinVar submissions (239), collaborators' cohorts (205), PEDIA cohort (133; 25 labelled as published cases) | no source | **prespecified test of v1.1** |
| Case reports, development side | 300 | after the cutoff; diseases disjoint from the test side | yes | not tested; 30 reports audited (Supplementary S3) |
| **Case reports after the cutoff** | **240** | PubMed case reports first public on or after 2025-06-01, cut before the diagnosis | yes | **prespecified test of v2** |

**Table 2. Held-out published cases, v1.0.** Confirmed disease at first place and in the top ten, with 95% Wilson intervals, scored by identifier unless marked (rows judged by name use DeepRare's judging prompt); each case's own source paper masked unless stated (DeepRare could not be masked).

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
| Agent (v1.0), judged by name | 42.5% [35.9–49.4] | |
| DeepRare on the same model, judged by name | 27.5% [21.8–34.1] | |

**Table 3. The three prespecified tests.** Confirmed disease within the first *k* answers, scored by identifier unless marked; the last column gives the cases only the agent and only the named system solved at first place, with the two-sided exact sign test (unadjusted; the three primary comparisons with the model asked directly are Holm-adjusted in the text). Rows judged by name use DeepRare's judging prompt, which reads the first five names.

| set | system | top-1 [95% CI] | top-3 | top-5 | top-10 | agent : system |
|---|---|---|---|---|---|---|
| MyGene2 (n = 146) | **Agent (v1.1)** | **52.1%** [44.0–60.0] | 63.0% | 68.5% | 74.0% | |
| | Same model, asked directly | 7.5% [4.3–13.0] | 18.5% | 28.8% | 34.9% | 69 : 4 (p < 0.001) |
| | Rank, then check (no model) | 41.1% [33.4–49.2] | 53.4% | 56.8% | 61.0% | 17 : 1 (p < 0.001) |
| | LIRICAL | 41.8% [34.1–49.9] | 49.3% | 53.4% | 56.2% | 18 : 3 (p = 0.001) |
| | GPT-6.1, asked directly | 54.8% [46.7–62.6] | 67.1% | 70.5% | 75.3% | 22 : 26 (p = 0.67) |
| | *judged by name:* agent (v1.1) | 54.1% | | 69.9% | | |
| | *judged by name:* same model, asked directly | 13.7% | | 30.1% | | 66 : 7 (p < 0.001) |
| CADA test (n = 577) | **Agent (v1.1)** | **23.6%** [20.3–27.2] | 32.6% | 36.4% | 43.8% | |
| | Same model, asked directly | 14.7% [12.1–17.9] | 22.2% | 27.0% | 34.8% | 73 : 22 (p < 0.001) |
| | Rank, then check (no model) | 11.6% [9.2–14.5] | 17.9% | 21.3% | 26.3% | 71 : 2 (p < 0.001) |
| | LIRICAL | 12.0% [9.6–14.9] | 19.9% | 23.4% | 28.6% | 75 : 8 (p < 0.001) |
| | *judged by name:* agent (v1.1) | 24.8% | | 37.1% | | |
| | *judged by name:* same model, asked directly | 18.7% | | 30.7% | | 75 : 40 (p = 0.001) |
| Case reports (n = 240) | **Agent (v2)** | **19.6%** [15.1–25.1] | 29.6% | 35.0% | 43.3% | |
| | Same model, asked directly | 8.8% [5.8–13.0] | 11.7% | 15.8% | 20.0% | 30 : 4 (p < 0.001) |
| | One-way similarity, merged knowledge (no model) | 7.1% [4.5–11.0] | 11.7% | 17.9% | 26.2% | 35 : 5 (p < 0.001) |
| | Rank, then check (no model; OMIM only) | 2.1% [0.9–4.8] | 4.6% | 5.0% | 7.1% | 43 : 1 (p < 0.001) |
| | LIRICAL (OMIM only) | 0.8% [0.2–3.0] | 3.8% | 4.2% | 6.2% | 45 : 0 (p < 0.001) |
| | *judged by name:* agent (v2) | 21.7% | | 37.9% | | |
| | *judged by name:* same model, asked directly | 18.3% | | 30.0% | | 18 : 10 (p = 0.18) |

**Table 4. The CADA test set by cohort, as recorded in the CADA test file** (descriptive; p-values unadjusted; the column judged by name and the split of the PEDIA cohort by submitter were added after the tests). First place.

| source | patients | agent (v1.1) | same model, asked directly | rank, then check | agent : model | by name, agent : model |
|---|---|---|---|---|---|---|
| ClinVar submissions | 239 | 13.4% [9.6–18.3] | 7.5% [4.8–11.6] | 6.3% [3.8–10.1] | 18 : 4 (p = 0.004) | 23 : 14 (p = 0.19) |
| Collaborators' cohorts (Tübingen and six others) | 205 | 20.0% [15.1–26.0] | 15.6% [11.3–21.2] | 8.3% [5.2–12.9] | 19 : 10 (p = 0.14) | 19 : 12 (p = 0.28) |
| PEDIA cohort, all | 133 | 47.4% [39.1–55.8] | 26.3% [19.6–34.4] | 26.3% [19.6–34.4] | 36 : 8 (p < 0.001) | 33 : 14 (p = 0.008) |
| — submitted by named individuals | 108 | 49.1% [39.8–58.4] | 29.6% [21.8–38.8] | 25.9% [18.6–34.9] | 28 : 7 (p < 0.001) | 27 : 8 (p = 0.002) |
| — labelled as published cases | 25 | 40.0% [23.4–59.3] | 12.0% [4.2–30.0] | 28.0% [14.3–47.6] | 8 : 1 (p = 0.039) | 6 : 6 (p = 1.00) |

**Table 5. Case reports by the kind of identifier the confirmed disease carries** (unplanned; p-values unadjusted). First place. *Lookup as the agent's*: the direct model's answers looked up the way v2 looks up its own (the identifier written if the knowledge knows it, otherwise the closest name); *lookup by name only*: the closest name at a similarity of 90 or more; *by name*: DeepRare's judging prompt with `deepseek-flash` as judge. No new model calls.

| confirmed disease | reports | agent, by identifier | agent, by name | model, by identifier | model, lookup as the agent's | model, lookup by name only | model, by name | agent (by identifier) : model (lookup by name only) |
|---|---|---|---|---|---|---|---|---|
| No OMIM entry (Orphanet only) | 141 | 14.2% | 17.7% | 2.1% | 4.3% | 13.5% | 17.0% | 7 : 6 (p = 1.00) |
| OMIM | 99 | 27.3% | 27.3% | 18.2% | 18.2% | 16.2% | 20.2% | 14 : 3 (p = 0.013) |
| All | 240 | 19.6% | 21.7% | 8.8% | 10.0% | 14.6% | 18.3% | 21 : 9 (p = 0.043) |
