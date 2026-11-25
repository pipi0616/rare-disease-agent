## Introduction

A patient with a rare disease often waits years for a diagnosis. Phenotype-driven tools were built to shorten that wait: given the patient's findings as Human Phenotype Ontology (HPO) terms [1], they rank the diseases whose annotated phenotype fits best [2–5]. Large language models (LLMs) have since been put to the same question, asked directly [6–9] and as agents or pipelines that call such tools and search the literature [10–13]. The reported accuracies are high — a recent agentic system ranks the confirmed diagnosis first in 57% of cases on average across nine datasets [10] — and hard to read, for three reasons.

First, the public test cases are published case reports, and HPO's disease annotations are curated from published case reports — often the same ones, so a tool that reads the annotations is, in part, reading the answer. Benchmarks for these tools exist [14,15], but the overlap is rarely controlled (one recent study removed it [13]), and its effect on a published tool has not, to our knowledge, been reported. Second, a benchmark public before a model's training data ends can be memorised. Third, published cases are not patients: patients as clinics and laboratories record them have fewer findings, and more of them have the commoner rare diseases [16,17].

We built a deliberately simple agent — one inexpensive model, five or six tools over pinned public knowledge, about one US cent per case — and evaluated it with each case's source paper masked from everything the tools read and under plans fixed before each run: on held-out published cases, on external patients, and in three prespecified tests on cases never used in its development — patients shared by families and clinicians (MyGene2 [18,19]), patients of diagnostic laboratories and clinics (CADA [20]) and case reports published after the model's training cutoff.

## Methods

### Task and scoring

A system is given a patient's findings as HPO terms, and sex where recorded, and nothing else; findings recorded as absent are withheld. It answers with up to ten diseases, best first, each with an OMIM or Orphanet identifier. A case is solved at rank *k* when one of the first *k* identifiers is the confirmed diagnosis or one that Mondo [21] maps to it exactly; for a disease with genetic subtypes this asks for the subtype. A case without an answer is a miss. Rates carry 95% Wilson intervals [22]. Two systems are compared on the same cases by the two-sided exact sign test on the cases only one of them solves ("a : b"); paired differences with Wald intervals were added after the tests; the three primary tests of the revised agent are corrected together by Holm's method [23], and other p-values are unadjusted. Answers were also judged by name, on the first five names, with DeepRare's prompt [10]; the judge was `deepseek-flash`, the model inside the systems it judged. Prespecified claims are decided by identifiers. The study is reported following TRIPOD+AI [30] (online supplemental file 2).

### Cases

[[T:sets]] lists every set and how it was used; online supplemental file 1 (sections S1–S14) gives details, the case reports in S3. Phenopacket Store 0.1.27 [14,24] holds 10,374 published patients with a confirmed OMIM diagnosis from 1,733 papers. Papers were split before any development into a design split (6,014 patients) and 840 held-out papers, one case each. v1.0 was also tested on 47 cases first public on or after 1 June 2025, the reported end of the model's training data, and on two external patient sets of RareBench [6], HMS (88 patients of one clinic) and RAMEDIS (624 patients of a metabolic registry), which then became development sets.

The revised agent was tested on three sets fixed in one plan before any system ran on them; no one had read their cases. *MyGene2* [19]: features and causal genes shared by families and clinicians, as preprocessed for SHEPHERD [18] (146 patients with an OMIM diagnosis, 54 of them with a distal arthrogryposis); 54 patients (not the same 54) name a source paper, which was masked. *CADA test set* [20]: the 577 patients of the authors' test file with an OMIM diagnosis — 239 ClinVar submissions, 205 patients of seven cohorts of the authors' collaborators, and 133 of the PEDIA cohort, 25 of them labelled as published cases. No CADA case names its source, so none could be masked; median five findings. Because 300 cases of the authors' training file were a development set, the test file is held out from a development source rather than external. *Case reports after the cutoff*: PubMed case reports with open full text that entered PubMed by 24 October 2026 and were first public on or after 1 June 2025, kept when the title named one disease that Orphanet lists [26] and two automatic annotators, PubTator3 [27] and the model, agreed on it. The case description from the PMC BioC service [28] was cut, without rewriting, before the first sentence that names the disease or its gene, reports a confirming test, or was pointed to by the model, and read into HPO terms by the note reader described below. Diseases were drawn to a test or a development side; the test side holds 240 reports of 142 diseases (median ten findings), 141 with no OMIM entry. An audit of 30 development-side reports found the key right in 29 and the diagnosis still readable in 3 (95% CI 3.5–25.6%).

### Knowledge and masking

The tools read HPO's disease annotations (release 2026-09-01; 8,478 OMIM diseases) and, in v2, Orphanet's as well, merged by Mondo's exact matches, with Orphanet's prevalence classes and descriptions from Orphanet and MedlinePlus Genetics. While a system works on a case, the case's source paper is masked from all of it ([[F:design]]): annotations supported only by that paper are removed, a disease known only from it does not exist for any tool, and its patients leave the bank of similar patients. The mask removes whole papers, including what they say about their other patients, but cannot remove annotations that cite no paper (30.6% of HPO's phenotype annotations of OMIM diseases cite only OMIM entries, and Orphanet's cite none), so it is neither an upper nor a lower bound on the leak. After each run every tool output is searched for the case's paper and for diseases known only from it; a single hit voids the run.

### The agent

All versions run on LangChain's agent loop with `deepseek-flash`, reasoning off, temperature 0, and at most eight model calls per case. The tools rank every disease by phenotype similarity [2], check one disease against the findings, look a disease up, find an identifier from a name, find the closest published patients, and (from v1.1) search disease descriptions. v1.0 starts from the tools' ten best candidates. v1.1 first answers from the model's own knowledge; each disease it names is looked up and checked like the tools' candidates, with each candidate's Orphanet prevalence class shown, and the model is asked to prefer the more common of comparably fitting candidates ("relatively common": one patient in 100,000 or more). v2 adds Orphanet's diseases, takes the tools' list from a one-way similarity (findings looked for in the disease [2,5]), and lets the model's own first answer lead when it is relatively common and in the tools' top thirty. An earlier form of v1.1 (v1.1a) was run without a prespecified comparison (S11). A rule, stated in the plan to predate v2's development results but first committed together with the results of four of the five planned development sets, on which v2 was not better, chose v1.1 for MyGene2 and CADA, whose diagnoses carry OMIM identifiers (S2); that v2 would be tested on the case reports, many of whose diagnoses v1.1's knowledge does not contain, was decided after those four sets had been run. A separate reader turns clinical notes into HPO terms and never writes an identifier (S5); its prespecified primary claim failed: it beat the model writing identifiers (58 : 5) but not a dictionary of HPO names (29 : 38, p = 0.33). Prompts are in S4.

### Comparators

The same model asked once without tools ("asked directly"); a fixed pipeline (the tools' top ten ranked by one model call); three rankings without a model — phenotype similarity, the nearest published patients, and "rank, then check" (v1.0's starting list); LIRICAL 2.4.1 [3], phenotype only, with each case's own masked annotation file; GPT-6.1, Claude Sonnet 5.5 and Gemini 4 asked directly; and DeepRare [10], run from its published code on the agent's model with its case bank limited to the public RareArena cases [25] and the other substitutions in S8. DeepRare searches the web and could not be masked. Model identifiers and dates are in S12.

### Plans and records

Each prespecified test followed a plan committed to the project's git repository before its first run, fixing the cases, the systems and their version, the comparison that decides the primary claim, and that each system is scored once. The plans state twelve primary claims; nine held and three failed (S7). One plan was changed, with a dated note, after part of its results had been seen: questions lost to API failures were asked again instead of the run being voided. The plans are in Chinese and timed by git. Analyses not named in a plan are marked as unplanned.

### Use of generative AI

[[AI_USE]]

### Patient and public involvement

Patients and/or the public were not involved in the design, conduct, reporting or dissemination plans of this research.

## Results

### The effect of masking

LIRICAL ranked the confirmed disease first in 63.2% of the 840 held-out cases unmasked and in 30.1% masked (278 cases lost, none gained; [[F:mask]]). Part of the drop is that 122 cases cannot be answered under the mask at all; on the 718 cases that stay answerable, LIRICAL still falls from 62.4% to 35.2%.

### The first version and its failure on external patients

On the 840 held-out cases v1.0 ranked the confirmed disease first in 42.4% (95% CI 39.1–45.7), ahead of the fixed pipeline (57 : 10), LIRICAL (121 : 18) and its own model asked directly (14.3%; 257 : 21). On a fixed random 200 of them it was ahead of GPT-6.1 asked directly (37 : 17, p = 0.009) and of the other comparators ([[F:heldout]]; [[T:heldout]]); DeepRare ran under conditions not its own.

Two plans tested v1.0 once more ([[F:agentmodel]]a). On the 47 temporal cases it solved 23.4% and its model 8.5% (9 : 2, p = 0.065): not established. On the two external patient sets it lost to its own model: 19.3% against 31.8% on HMS (4 : 15, p = 0.019) and 24.7% against 32.7% on RAMEDIS (47 : 97, p < 0.001); the prespecified claim against the fixed pipeline, on the two sets pooled, also failed (54 : 45, p = 0.42). Judged by name, DeepRare was ahead of v1.0 on HMS (38.6% against 20.5%; 8 : 24, p = 0.007). Where the model alone was right and v1.0 wrong, v1.0's own top ten held the answer in 12 of 15 HMS and 85 of 97 RAMEDIS cases, and v1.0 had usually checked it before preferring a rarer disease with a richer annotation. The held-out set had hidden this: only 42 of its 840 cases have a relatively common disease, and on those the model asked directly solved 61.9% and v1.0 57.1% (unplanned). v1.1 was built to use what the model knew.

### Prespecified tests of the revised agent

On MyGene2, v1.1 solved 52.1% (95% CI 44.0–60.0) and its model asked directly 7.5% (4.3–13.0): 69 : 4, a difference of 44.5 points (35.6–53.4). On the CADA test set, 23.6% (20.3–27.2) against 14.7% (12.1–17.9): 73 : 22, 8.8 points (5.6–12.1). On the case reports, v2 solved 19.6% (15.1–25.1) against 8.8% (5.8–13.0): 30 : 4, 10.8 points (6.3–15.4). Holm-adjusted, p < 0.001 for each ([[F:agentmodel]]b; [[T:tests]], which also gives the top three, five and ten; [[F:newtests]]). The agent was ahead of its tools without a model on every set (17 : 1 on MyGene2, 71 : 2 on CADA, 35 : 5 against v2's starting list on the case reports) and of LIRICAL (18 : 3, 75 : 8, 45 : 0; on the case reports LIRICAL reads only OMIM's diseases, which include 99 of the 240 diagnoses).

### What the lead is made of

Judged by name, the agent's lead remains on MyGene2 (66 : 7) and on CADA as a whole (75 : 40, p = 0.001); looking the model's answers up the way the agent looks up its own leaves the model's accuracy unchanged on both sets (unplanned).

On CADA (descriptive; [[T:cada]]) the lead was clear for the ClinVar submissions (18 : 4) and for the PEDIA cohort (36 : 8), but not for the 205 patients of the collaborators' cohorts (20.0% against 15.6%; 19 : 10, p = 0.14), and judged by name (unplanned) it was not significant for the ClinVar submissions or the collaborators' cohorts. Without the 25 cases labelled as published (unplanned), the agent solved 22.8% of the remaining 552 and its model 14.9% (65 : 21, p < 0.001). By number of findings the lead on CADA was small with up to five findings and clear from six on, partly confounded with cohort ([[F:findings]]).

On the case reports, roughly half to two-thirds of the lead is retrieving the correct entry (unplanned; [[T:idkind]]). Judged by name, the agent solved 21.7% and its model 18.3% (18 : 10, p = 0.18). On the 141 reports without an OMIM entry the model named the right disease first 24 times but gave its identifier 3 times — the Orphanet codes it wrote mostly exist but name other diseases — and the agent gave it 20 times. Of the 10.8-point lead, 5.0 points remain against the model's answers looked up by name (21 : 9) and 3.3 under the name judge (18 : 10), so 54–69% of it is retrieval.

### A frontier model, and cost

GPT-6.1 asked directly on MyGene2 solved 54.8% (46.7–62.6), not significantly different from v1.1 (22 : 26; −2.7 points, −12.0 to 6.6), so a deficit of up to 12 points is not excluded; MyGene2 was public before its training data end. Split afterwards (unplanned), the agent solved more of the 54 distal arthrogryposes (14 : 6, p = 0.12), GPT-6.1 more of the other 92 patients (8 : 20, p = 0.036) and of the 54 whose source paper was masked for the agent only (7 : 18, p = 0.043). v1.1 cost US$0.008 per patient at list price (median 17 seconds), GPT-6.1 asked directly US$0.007 and its own model US$0.0005; v2 cost US$0.010 per case report.

## Discussion

**Benchmark leakage can be large.** Masking each case's source paper halves an annotation-reading tool's first-place accuracy on published cases without changing the order of such tools, so unmasked benchmarks favour them over models asked directly and over agents whose gains come from elsewhere.

**External tests catch what held-out tests miss.** The first version failed for a reason — ranking blind to prevalence — that phenotype matching has met before [3,29] and that its held-out test, with 42 cases of a relatively common disease among 840, did not reveal.

**Retrieving the right entry is a contribution of tools, not a diagnosis.** A valid identifier for the wrong disease passes any format check; on the case reports, finding the right one is much of what the tools add. A clinician or a downstream tool needs that entry, but the diagnostic gain beyond it was not established by the name judge.

**Limitations.** The tests are retrospective, on public de-identified data, without clinicians, and use phenotype terms only; whether the evidence the agent records for each candidate helps clinicians was not tested. The agent used one model throughout; its training cutoff is known only from third-party reports, and MyGene2 and CADA were public before it. The mask could not act on CADA or on 92 of the 146 MyGene2 patients. Exact-match scoring asks for genetic subtypes a phenotype often cannot decide and favours systems that look identifiers up; the name judge was the systems' own model, unchecked by a clinician. v1.1 was not run on the case reports nor v2 on the patient sets; Claude Sonnet 5.5 and Gemini 4, GPT-6.1 beyond MyGene2, and the fixed pipeline were not run on the new sets. CADA's test file comes from a source that also supplied a development set. Each system was run once, and run-to-run variation at temperature 0 was not measured. On the case reports the answer key, the reader and the systems share one model, reports were kept only when the model's diagnosis resolved through the agent's own name matcher, and about one report in ten stays readable.

## Conclusions

With each case's known source masked and every test fixed in advance, two revisions of a simple tool-using agent on an inexpensive model ranked the confirmed disease's identifier first more often than their own model in all three prespecified tests; on the case reports much of the lead was retrieving the correct entry, and judged by name it was not significant. Its first version failed on external patients for a reason its held-out test did not reveal. Benchmarks should mask each case's source, test outside the development source, and fix the plan before the run.
