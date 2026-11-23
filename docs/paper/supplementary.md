---
title: "Supplementary material"
subtitle: "Source-paper masking and prespecified external tests of a low-cost tool-using agent for rare-disease diagnosis"
---

## S1. Datasets and how each was used

**Table S1.** Every set of cases, its source and its role. A prespecified test was run under a plan committed before its first run (S7), and each system was scored on it once.

| set | cases | source | role |
|---|---|---|---|
| Design split | 6,014 patients (893 papers) | Phenopacket Store 0.1.27 | development; bank of similar patients |
| dev-200 | 200 (one per paper) | design split | development: every design decision |
| Held-out | 840 (one per paper) | Phenopacket Store 0.1.27, papers disjoint from the design split | prespecified test of v1.0; a fixed 200 for systems billed per case |
| Temporal | 47 (one per paper) | papers first public on or after 2025-06-01 (21 from the held-out split, 26 added after release 0.1.27) | prespecified test of v1.0; v1.1a afterwards, without a prespecified comparison |
| HMS | 88 | RareBench (a clinic's patients) | prespecified test of v1.0; development afterwards |
| RAMEDIS | 624 | RareBench (a metabolic registry) | prespecified test of v1.0; development afterwards |
| MME | 40 | RareBench (published cases; source not given, so not masked) | v1.0 and v1.1a once each, without a prespecified comparison; development afterwards |
| RareArena sample | 498 | case reports read into HPO terms | development |
| CADA development | 300 | CADA training file, fixed random sample | development |
| **MyGene2** | 146 | patients shared by families and clinicians; 54 name a source paper | **prespecified test of v1.1** |
| **CADA test** | 577 | CADA test file, patients with an OMIM diagnosis; none names a source | **prespecified test of v1.1** |
| **Case reports after the cutoff** | 240 (all read into HPO terms) | PubMed case reports first public on or after 2025-06-01 | **prespecified test of v2** (development side: 300, of which 298 could be read into HPO terms; not used here) |

Data that were considered and not used: the 75 Peking Union Medical College Hospital cases of RareBench (withdrawn from the public archive by its authors in December 2024); MIMIC-IV-Rare (requires credentialed access, and its use policy excludes services whose data handling cannot be verified); the Xinhua and Hunan hospital cohorts of DeepRare (controlled access); the Undiagnosed Diseases Network (controlled access); RareBench's LIRICAL subset (its file names no source papers, so the cases cannot be masked).

## S2. Choosing between the two revisions

**Table S2.** Agent v2 against v1.1 on the development sets, first place; paired counts are cases only the first-named system solved against cases only the second solved (two-sided exact sign test).

| development set | cases | v2, top-1 / top-10 | v1.1, top-1 / top-10 | v2 : v1.1 | v2 : model asked directly |
|---|---|---|---|---|---|
| CADA development | 300 | 22.3% / 49.0% | 23.7% / 49.3% | 13 : 17 (p = 0.59) | 29 : 10 (p = 0.003) |
| HMS | 88 | 39.8% / 65.9% | 37.5% / 56.8% | 9 : 7 (p = 0.80) | 9 : 2 (p = 0.065) |
| MME | 40 | 70.0% / 90.0% | 72.5% / 87.5% | 2 : 3 (p = 1.00) | 27 : 1 (p < 0.001) |
| dev-200 | 200 | 38.5% / 61.5% | 41.5% / 64.0% | 10 : 16 (p = 0.33) | 49 : 1 (p < 0.001) |
| RAMEDIS (200) | 200 | voided after 38 cases (funds) | — | — | — |

The rule, which the plan states was written before v2's development results were seen (it was first committed, in 644abfe on 20 November 2026, together with the results of four development sets): v2 is the system to test if it is significantly worse than v1.1 on no development set and solves at least as many cases in total; otherwise v1.1. Pooled over the four sets that were run, v2 solved 207 cases and v1.1 216 (paired 34 : 43), so v1.1 was tested on MyGene2 and CADA. On HMS, MME and dev-200 the v1.1 column holds the recorded answers of v1.1a, the earlier form whose prompts still asked for a Mendelian disease and an OMIM number; on the CADA development cases it is v1.1 itself. That v2 would be the system for the case-report test although the rule chose v1.1 was added after the four sets had been run, because many case-report diagnoses are diseases that v1.1's knowledge does not contain; v2 had not been run on case reports before the test (the planned run on the development side of the case reports was dropped for cost). The fifth set was stopped after 38 cases when funds ran out, voided, and not rerun; the guard in v2 was expected to help most there, so the comparison is, if anything, unfavourable to v2. On the same CADA development cases v1.1 solved 23.7%, the model asked directly 16.0%, the no-model ranking 14.0% and LIRICAL 13.3% (v1.1 against the model: 35 : 12, p = 0.001).

**Versions and prompts.** v1.0: agent prompt agent-v3 (seeded-v1), five tools. v1.1a: hypotheses-v2, code 788e56e (2026-10-18). v1.1: hypotheses-v4, which differs from v1.1a in asking for a rare (not only Mendelian) disease and allowing an Orphanet code for a disease with no OMIM entry; the model asked directly was changed the same way (direct-v1 to direct-v2). v2: hypotheses-v4 with the changes of Section 2.4. All tests of v1.1 and v2 ran on code 2cea0e9.

Before v2 was built, eighteen combinations of similarity, ordering and knowledge were compared without a model, against a rule fixed beforehand (no set significantly worse at first place or in the top ten, at least two significantly better), on development sets of four kinds of patients; none passed. A fifth kind — RareArena case reports — was added after those results had been seen, and on five kinds one combination passed: the one-way similarity in its own order on the knowledge with Orphanet merged in. Its passing therefore rested on a set added afterwards, which is one reason it was taken to the case-report test.

## S3. The case-report set

**Procedure** (rules committed before any test-side report was read, and made stricter after the development-side audit described below; see `docs/casereports_plan.md` in the repository, with its history).

1. *Candidates.* PubMed: publication type "Case Reports", English, open-access full text in PMC, entered between 2025-06-01 and 2026-10-24 (71,351 records). One random order by a fixed seed (20261025); processed in that order.
2. *Annotator A.* PubTator3 on the title and abstract; disease mentions as MeSH identifiers; each mapped to a Mondo class by Mondo's exact matches, and through it to OMIM and Orphanet identifiers. A "rare disease of the knowledge base" is a class that matches an Orphanet entry and has a disease in the merged knowledge base.
3. *First rules, on A alone.* The paper is not used elsewhere in the project; it first became public on or after the cutoff; its title names exactly one rare disease of the knowledge base; the side that disease belongs to still has room (at most three reports per disease; at least a third of each side relatively common diseases).
4. *Full text.* The paragraphs of the section that the PMC BioC service types as the case. Section titles, tables and figure captions are not read.
5. *Annotator B.* The model (temperature 0, fixed prompt, below) reads the title, the abstract and the numbered sentences of the case description and returns the final diagnosis, the number of patients, whether the description begins before the diagnosis was known, and the number of the first sentence that gives the diagnosis away.
6. *Agreement.* B's diagnosis is matched by name (the matching of the agent's `find_disease` tool: rapidfuzz WRatio at least 90) against every form of every disease's name — each part of its name in the knowledge base, its Mondo name and Mondo's exact synonyms — and must be the disease A found in the title. A written diagnosis more than 2.2 times as long as the form it matches does not count. A report is kept only on agreement; nothing is adjudicated by a person.
7. *Further rules.* One patient; the description begins before the diagnosis was known; at least 60 words remain after the cut.
8. *The cut.* Everything from the first revealing sentence on is dropped. That sentence is the earliest of: B's sentence; the first sentence in which a program finds a name, synonym or abbreviation of the disease (also the name without the type it ends in) or one of its genes; the first sentence that mentions a confirming test (e.g. biopsy, histology, immunohistochemistry, cytology, bone marrow, culture, PCR, sequencing, karyotype, FISH, mutation, zygosity, serology, antibody, antigen). Nothing is rewritten.
9. *Sides.* A disease is on the test side with probability 240/540 by a draw that depends only on the disease and the seed.
10. *Reading.* The kept text is read into HPO terms by the note reader; only findings stated as present are used.

**Annotator B's prompt (version casereport-key-v3).**

> You read one published case report and answer four questions about it. Reply with a json object and nothing else: {"diagnosis": "...", "patients": 1, "diagnostic": true, "reveal": 7}
>
> - "diagnosis": the patient's final diagnosis, the disease the report is about: the disease's name alone, as the authors write it in full — no site, cause, complication or circumstance around it, not an abbreviation alone, not a group of diseases when they give the specific one. If what looked like one disease turned out to be another thing (a foreign body, a drug reaction), name what it turned out to be.
> - "patients": how many patients the report describes.
> - "diagnostic": true if the case description begins before the diagnosis was known and tells how it was reached; false if the diagnosis is already known where the description begins (a report about treating or following a known disease).
> - "reveal": the number of the first sentence of the case description from which a reader would know the diagnosis, or null if there is none. It is the first sentence that does any of these: (a) names the disease, a synonym or its abbreviation, or says it is suspected, considered or to be ruled out; (b) names its causal gene, a variant, or the organism that causes it; (c) reports the result of a test done to establish it — genetic or molecular testing; a biopsy, histopathology, cytology or bone-marrow examination; a culture, PCR, antigen test or serology for the organism; an antibody or enzyme assay specific to the disease — or says that such a test for this disease was ordered; (d) names a treatment used only for this disease. Symptoms, signs, routine blood tests and imaging findings do not give it away, unless the sentence also names the disease.

**Pilot.** On 783 case reports entered in the first week of March 2025 (before the cutoff; never used as cases), the first 368 in the fixed order gave 120 that annotator A let through and 18 accepted reports. The pilot changed six rules before any report from after the cutoff was read. Four concern the answer key: disagreements are dropped rather than adjudicated by a person (the builder is also the developer, and would otherwise read test cases); a written diagnosis far longer than the name it matches does not count (a title — "a forgotten foreign body presenting as allergic bronchopulmonary aspergillosis" — had matched the disease it was mistaken for); names are matched against synonyms too; and only diseases that Orphanet lists are kept (osteoporosis had been accepted through an OMIM susceptibility entry). The other two: entries with the same name all count as correct, and the human audits are made on the development side only.

**First build and audit.** A first build under these rules stopped at 154 accepted reports (58 test side, 96 development side) of 6,177 processed. Of the 2,286 that annotator A let through, 865 named the disease only in the abstract, 491 had no full text in the BioC service (about half of the papers from 2026), 325 had first become public before the cutoff, 181 failed on B's diagnosis (133 not found in the knowledge base, 48 disagreeing with A), 90 had no case section, 87 named more than one rare disease in the title, 61 were not a single patient or began with the diagnosis known, 18 kept fewer than 60 words, and 14 exceeded three reports per disease. Thirty development-side reports, drawn by a fixed seed, were read by one of us; the test side was not read. The answer key matched the title and B's diagnosis in all 30 (in seven, a subtype or site had been mapped to the disease itself). In about six of the 30 the diagnosis could still be read from the kept text: a confirming test's result (39% blasts in the marrow for acute myeloid leukaemia, twice; amyloid in a renal biopsy; specific IgE to *Aspergillus*), a test for the disease being ordered (an *SS18* break-apart probe), or the disease's name inside a sentence that the splitter had joined to the next. The cut was therefore made stricter — the confirming-test rule, a splitter that handles a missing space, the name without its type — and the set rebuilt from the start of the same order, with annotator B asked again under the stricter prompt.

**Final build.** Under the stricter cut both sides were filled after 35,895 of the 71,351 candidates: 240 test reports (142 diseases; 130 with a relatively common diagnosis) and 300 development reports (188 diseases; 135 relatively common), sharing no disease, first public between 1 June 2025 and 13 July 2026. The kept text has a median of 186 words on either side (interquartile range 130–301 and 121–274). Of the 13,605 papers that annotator A let through, 5,071 named the disease only in the abstract, 1,988 had first become public before the cutoff, 1,939 had no full text in the BioC service, 1,133 belonged to the development side after it was full, 948 exceeded three reports per disease, 696 failed on annotator B's diagnosis (478 not found in the knowledge base, 218 disagreeing with A), 495 named more than one rare disease in the title, 356 had no case section, 349 were not a single patient or began with the diagnosis known, 83 kept fewer than 60 words, and 7 were used elsewhere in the project. Annotator B was asked 1,668 times (US$0.79 at list price).

**Second audit.** Thirty development-side reports of the final build, drawn by a fixed seed, were read by one of us; the test side was not read. The answer key was right in 29; in one, a report of liquorice-induced apparent mineralocorticoid excess had been keyed to the inherited disease of the same name. In three the diagnosis could still be read from the kept text: the opening pressure at lumbar puncture (idiopathic intracranial hypertension), the words "pulmonary hypertension" in a sentence about what had not been investigated (pulmonary arterial hypertension), and an abbreviation that Mondo does not list (SOS, for sinusoidal obstruction syndrome). The rules were left as they were, as fixed beforehand; about one test report in ten can therefore be expected to give its diagnosis away in the text. Every system is given the same terms read from that text.

## S4. Prompts

**The model asked directly** (also the agent's first answer; version direct-v2, used on MyGene2, CADA and the case reports; on the held-out, temporal and external sets, version direct-v1 asked for a Mendelian disease and an OMIM number).

> You are a clinical geneticist. You will be given the phenotype of a patient with a suspected rare disease, as Human Phenotype Ontology (HPO) terms. List the 10 most likely diagnoses, most likely first. For each, give: disease_name: the name of the disease; disease_id: its OMIM phenotype number, written OMIM:nnnnnn (six digits); for a disease with no OMIM entry, its Orphanet code, written ORPHA:n; gene: the HGNC symbol of the causal gene, if it has one. Answer with a json object only, in exactly this format: {"candidates": [{"disease_name": "...", "disease_id": "OMIM:123456", "gene": "ABC1"}]}

The user message lists the patient's sex ("unknown" when not recorded) and each finding as "label (HPO id)".

**The agent, v1.1 and v2** (system prompt, version hypotheses-v4).

> You are a clinical geneticist. Your task is to diagnose a patient with a suspected rare disease from their phenotype, given as Human Phenotype Ontology (HPO) terms.
>
> Your tools work over the HPO disease annotations: [one line per tool]
>
> Before any tool ran, you answered from your own knowledge alone. The first message shows that differential ([H1], [H2], ...), each disease found in the HPO annotations and checked against the patient, then the phenotype tools' leading candidates ([T1], [T2], ...), checked the same way. Weigh the two lists as equals: what you know of a disease is evidence, as the tools' match is. The HPO annotations are incomplete: well-known diseases, above all immune, inflammatory and metabolic ones, can have few annotated features, so a disease you suspect for good reason is not ruled out because it explains few findings here; read how it is described with search_disease_texts. Nor is a candidate right because the tools rank it first: one that explains only a small part of the patient's findings, none of them specific, needs another reason. Each disease shows how common Orphanet says it is. Where diseases fit comparably, the more common is the likelier: a well-known disease that fits is more likely than a far rarer one that explains a few more annotated findings, and a disease known from a handful of families needs findings that set it apart. An unknown prevalence is not evidence of rarity. Spend your turns where the lists disagree, or on a disease neither has. Weigh the evidence: a diagnosis should explain the patient's findings, above all the specific ones; findings recorded absent and missing hallmark features count against it; inheritance and onset should fit. You may name a disease the tools know little about if you have good reason.
>
> Your budget is 8 turns, and the last one is for your answer; answer sooner if the evidence is clear. Give your final answer: up to 10 diseases (OMIM or ORPHA ids), most likely first, each with a one-sentence reason.

## S5. Reading a clinical note into HPO terms

Tested once under a plan committed beforehand, against hand-annotated public text; document-level micro F1.

| reader | ID-68 (68 clinical notes) | GSC-2024 (206 abstracts) |
|---|---|---|
| this reader | 71.7% (precision 64.7, recall 80.3) | 71.5% |
| a dictionary of HPO names | 72.3% (precision 89.9, recall 60.5) | 58.6% |
| the model writing HPO identifiers itself | 55.3% | 47.3% |

The prespecified primary claim — better than both baselines on the clinical notes — failed: paired per note, the reader beat the model writing identifiers (58 notes to 5, p < 0.001) but not the dictionary (29 to 38, p = 0.33). On the abstracts it beat both (122 to 31; 160 to 11).

## S6. Runs that were void

A run whose records were incomplete was void and repeated without its score being read. In October: LIRICAL on HMS once (its process ended mid-run); v1.0 on MME once (11 of 40 records, probably because another run was writing to MLflow); LIRICAL on MME and v1.1a on the fixed 200 held-out cases once each (interrupted with the session). During the tests of Sections 3.4–3.5 this happened to: the no-model ranking on MyGene2 once (and a duplicate complete run of it, bd5bc3c5, was discarded unread) (11 of 146 records lost to a locked database; the tests were thereafter recorded in a store of their own); the model asked directly on MyGene2 twice and agent v1.1 on MyGene2 three times (the process was killed with the session, by a kernel panic of the shared machine, or stopped to protect it from memory exhaustion); LIRICAL on MyGene2 once (stopped: too many parallel Java processes). No score of a void run was computed or seen. No case-report run was void: agent v2 and LIRICAL were each paused once by the memory guard (for about one minute and one and a half minutes, while another job on the machine held 11 GB) and resumed; both recorded all 240 reports and passed the leak audit.

## S7. The plans, and when each was committed

Each plan is a Markdown file in `docs/` of the repository, written in Chinese. Together they state twelve primary claims; nine held and three failed. Primary claims were not adjusted across plans; within the last plan the three were Holm-adjusted. Its sections before "results" were committed before the first run of the test it governs and were not changed afterwards, with two exceptions: `comparison_plan_llms.md` carries a dated change, made after part of its results had been seen, by which questions lost to API failures were asked again instead of the run being voided; and `comparison_plan_deeprare.md` gained a dated note on how DeepRare writes disease names (0b7ca25, 18:51 on 14 October), two minutes after its held-out run had started and before any result, which did not change the primary claim. Results, and anything added later, are in later sections marked as such. Some pre-test commits were later squashed when their branch was merged; they are kept under the tags given below. Commit times come from the authors' git client and are not independently time-stamped; the repository will be public with the submission.

| plan (file) | first committed | tests it governs | primary claim | outcome |
|---|---|---|---|---|
| `heldout_plan.md` | 8b9c9bb, 2026-10-13 12:51 (tag `v1.0`) | v1.0 on the 840 held-out cases | v1.0 > fixed pipeline at first place | held (57 : 10) |
| `comparison_plan.md` | fe41c63, 2026-10-13 22:47 (tag `plan/lirical-2026-10-13`) | LIRICAL on the held-out cases | v1.0 > LIRICAL, both masked | held (121 : 18) |
| `comparison_plan_llms.md` | 68084f9, 2026-10-14 10:03 (tag `plan/llms-2026-10-14`) | GPT-6.1, Claude Sonnet 5.5, Gemini 4 asked directly on the fixed 200 | v1.0 > each model (three claims) | held (37 : 17, 52 : 13, 46 : 14) |
| `comparison_plan_deeprare.md` | 510494f, 2026-10-14 12:05 (tag `plan/deeprare-2026-10-14`) | DeepRare on the fixed 200 | v1.0 > DeepRare by identifier | held (71 : 2) |
| `phenotyping_plan.md` | 62eaf7e, 2026-10-14 19:32 | the note reader on ID-68 and GSC-2024 | reader > both baselines on clinical notes | failed (S5) |
| `temporal_plan.md` | 56ef8c2, 2026-10-15 13:07 | v1.0 on the 47 temporal cases | v1.0 > model asked directly | failed (9 : 2, p = 0.065) |
| `external_plan.md` | 56ef8c2, 2026-10-15 13:07 | v1.0 on HMS and RAMEDIS | v1.0 > fixed pipeline | failed (54 : 45) |
| `casereports_plan.md` | 1c87c92, 2026-11-20 18:52; amended twice before the final build (71b190f, 20:09; 2cea0e9, 20:44, the confirming-test cut) | how the case-report set is built and cut | — | Section 2.2, S3 |
| `exam_plan.md` | draft 644abfe 19:55; final 5ed1379, 2026-11-20 20:46 | v1.1 on MyGene2 and CADA; v2 on the case reports | on each set, agent > model asked directly at first place; Holm over the sets tested (three claims) | held on all three (by identifier) |

**The plan for the three tests, in English (summary of `exam_plan.md`, sections 1–6).** *Sets:* MyGene2 (146 patients with an OMIM diagnosis), the CADA test file (577 patients with an OMIM diagnosis), the case-report test side (at most 240 reports). No system had been run on them and no one had read their cases. *Systems:* v1.1 on MyGene2 and CADA, chosen by the rule of S2; v2 on the case reports; model `deepseek-flash`, reasoning off, temperature 0; code frozen for the duration of the tests. *Primary question, one per set:* does the main system rank the confirmed disease first more often than the same model asked directly on the same findings — two-sided exact sign test on the discordant cases, α = 0.05, Holm-corrected over the number of sets actually tested; a set not built for budget is reported as not tested. *Secondary questions, numbers and intervals only, no claims:* the top ten; against rank-then-check and LIRICAL, and on the case reports against the one-way list v2 starts from; by number of findings (1–2, 3–5, 6–10, 11+) and, for CADA, by source; the two patient sets pooled; MyGene2 beside DeepRare's published figure; name-based judging with DeepRare's prompt (judge `deepseek-flash`); GPT-6.1 asked directly on MyGene2 only. *Scoring:* by identifier with Mondo identity; the primary question by identifier only. *Rules:* each system scored once on each set; cases lost to API failures asked again; a run with incomplete records or a failed leak audit void and repeated without reading its score; no change to a system after its test; every result reported, failures included. Analyses outside this list are marked as unplanned in the paper.

## S8. DeepRare as run here

**Table S8.** How DeepRare [10] was run on the held-out cases, against its published configuration (from `comparison_plan_deeprare.md`, written before the run).

| component | published | here | why |
|---|---|---|---|
| central model | DeepSeek-R1 (reasoning) | `deepseek-flash`, reasoning off — the agent's model | the comparison is of designs on one model; cost |
| text embeddings | OpenAI text-embedding-3-small | the same, through OpenRouter | its case bank was embedded with it |
| case bank | six sources | the public PubMed cases only (about 10,000) [25,30] | the other five are not public |
| web search | Bing, Google or DuckDuckGo | DuckDuckGo | no key required |
| summarising web pages | gpt-4o-mini | `deepseek-flash` | one model for the whole system |
| code | — | one bug fixed (an argument passed in the wrong position in the DuckDuckGo tool); the similar-case search computed in one batch (same results) | it did not run otherwise |

DeepRare searches the web and its case bank and could not be masked. Its reading included a patient's own paper (as a PMC identifier among the similar cases it found) for 3 of the 200 cases, none of which it solved at first place by identifier (judged by name, it solved one); no PubMed identifier, DOI or title of a patient's own paper reached its model. It answered all 200 cases. It took about 27 model calls and a median of 3.2 minutes per case, against the agent's four to eight calls and 13 seconds. These conditions are not those of its publication, and the result does not bear on its published figures.

## S9. Use of an AI assistant

An AI coding and writing assistant (Claude, Anthropic; Claude Code) was used throughout under the authors' direction: it wrote most of the software in the repository, ran the evaluations and analyses, drafted the plans and the manuscript, and checked numbers in the manuscript against the per-case outcome files. Three independent reviews of the manuscript by separate instances of the assistant (methods and statistics, domain, editorial) were used before submission; the changes they led to are in the repository's history. The authors decided the questions, approved each plan before its test, reviewed the code, results and text, and take full responsibility for them. Most numbers in the paper can be recomputed from the per-case files in the repository; those that cannot are recorded in the plan documents: Table 2's nearest-patients row, the simulated-sequencing result (S11), Table S2's development results, the note-reader results (S5), the unmasked development-set figure in Fig. 2, the costs and run times, and the case-report build counts (S3).

## S10. Results by number of findings

**Table S10.** First place, by how many findings the case has, on each prespecified test (secondary analysis named in the plan; p-values unadjusted). Agent: v1.1 on MyGene2 and CADA, v2 on the case reports.

| set | findings | cases | agent | same model, asked directly | agent : model |
|---|---|---|---|---|---|
| MyGene2 | 1–2 | 17 | 17.6% | 0.0% | 3 : 0 (p = 0.25) |
|  | 3–5 | 57 | 66.7% | 12.3% | 33 : 2 (p < 0.001) |
|  | 6–10 | 41 | 39.0% | 7.3% | 15 : 2 (p = 0.002) |
|  | 11 or more | 31 | 61.3% | 3.2% | 18 : 0 (p < 0.001) |
| CADA test | 1–2 | 182 | 12.1% | 9.3% | 7 : 2 (p = 0.18) |
|  | 3–5 | 135 | 23.0% | 18.5% | 12 : 6 (p = 0.24) |
|  | 6–10 | 111 | 27.0% | 15.3% | 19 : 6 (p = 0.015) |
|  | 11 or more | 149 | 35.6% | 17.4% | 35 : 8 (p < 0.001) |
| Case reports | 1–2 | 6 | 16.7% | 0.0% | 1 : 0 (p = 1.00) |
|  | 3–5 | 34 | 17.6% | 5.9% | 5 : 1 (p = 0.22) |
|  | 6–10 | 85 | 17.6% | 8.2% | 10 : 2 (p = 0.039) |
|  | 11 or more | 115 | 21.7% | 10.4% | 14 : 1 (p < 0.001) |

## S11. Further results of v1.0 and of v1.1a

**Table S11.** First place, with 95% Wilson intervals where given; paired counts are cases only the agent named first and only the other system solved (two-sided exact sign test, unadjusted). From `temporal_plan.md` and `external_plan.md`, sections 8–9.

| set | system | top-1 | paired with the agent |
|---|---|---|---|
| Temporal (47; prespecified, v1.0) | v1.0 | 23.4% [13.6–37.2] | |
| | Same model, asked directly | 8.5% [3.4–19.9] | 9 : 2 (p = 0.065) |
| | Fixed pipeline | 21.3% [12.0–34.9] | |
| | LIRICAL | 14.9% [7.4–27.7] | 6 : 2 (p = 0.29) |
| | GPT-6.1, asked directly | 23.4% [13.6–37.2] | 3 : 3 (p = 1.00) |
| | Claude Sonnet 5.5, asked directly | 23.4% [13.6–37.2] | 4 : 4 (p = 1.00) |
| | Gemini 4, asked directly | 23.4% [13.6–37.2] | 4 : 4 (p = 1.00) |
| | DeepRare, by identifier / by name | 10.6% / 21.3% | 10 : 4 (p = 0.18) / 8 : 7 (p = 1.00) |
| Temporal (47; v1.1a, a second test of the set, no prespecified comparison) | v1.1a | 25.5% [15.3–39.5] | against the model asked directly 10 : 2 (p = 0.039); against v1.0 2 : 1; against GPT-6.1, Claude Sonnet 5.5 and Gemini 4 3 : 2, 5 : 4 and 4 : 3 |
| HMS (88; prespecified, v1.0) | v1.0 | 19.3% | |
| | Same model, asked directly | 31.8% [23.0–42.1] | 4 : 15 (p = 0.019) |
| | Fixed pipeline | 12.5% [7.1–21.0] | |
| | LIRICAL | 3.4% [1.2–9.5] | 15 : 1 (p < 0.001) |
| | GPT-6.1, asked directly | 18.2% [11.5–27.5] | 9 : 8 (p = 1.00) |
| | Claude Sonnet 5.5, asked directly | 22.7% [15.2–32.5] | 5 : 8 (p = 0.58) |
| | Gemini 4, asked directly | 14.8% [8.8–23.7] | 13 : 9 (p = 0.52) |
| | DeepRare, by identifier | 15.9% [9.7–25.0] | 11 : 8 (p = 0.65) |
| | DeepRare and v1.0, judged by name | 38.6% and 20.5% | **8 : 24 (p = 0.007)** |
| RAMEDIS (624; prespecified, v1.0) | v1.0 | 24.7% | |
| | Same model, asked directly | 32.7% [29.1–36.5] | 47 : 97 (p < 0.001) |
| | Fixed pipeline | 24.2% [21.0–27.7] | |
| | LIRICAL | 14.3% [11.7–17.2] | 87 : 22 (p < 0.001) |
| RAMEDIS, fixed 200 (DeepRare only) | DeepRare and v1.0, by identifier | 17.5% and 29.0% | 39 : 16 (p = 0.003) |
| | DeepRare and v1.0, judged by name | 34.0% and 30.0% | 19 : 27 (p = 0.30) |
| Held-out, fixed 200 (v1.1a, no prespecified comparison) | v1.1a | 45.0% | against v1.0 (43.0%) 12 : 8 (p = 0.50); against the fixed pipeline 19 : 5 (p = 0.007); against the model asked directly 61 : 1 |
| MME (40; source not given, not masked; no prespecified comparison) | v1.1a | 72.5% [57.2–83.9] | |
| | v1.0 | 80.0% [65.2–89.5] | 1 : 4 (p = 0.38) |
| | Fixed pipeline | 75.0% | 4 : 5 (p = 1.00) |
| | Rank, then check | 60.0% | 7 : 2 (p = 0.18) |
| | LIRICAL | 42.5% | 13 : 1 (p = 0.002) |
| | Same model, asked directly | 5.0% | 28 : 1 (p < 0.001) |

On HMS, judged by name, DeepRare was ahead of v1.0; with the model asked directly on HMS and RAMEDIS, these are the three comparisons in which a comparator was significantly ahead of the agent. On HMS the three frontier models asked directly also scored below `deepseek-flash` asked directly, the reverse of their order on the held-out cases; `deepseek-flash` may have seen the public RareBench, but on MME, also from RareBench, it solved 5%. On RAMEDIS a quarter of the patients (148) have phenylketonuria, so answering phenylketonuria for every patient would score 23.7%; 115 of these 148 are recorded with hypertyrosinaemia, which phenylketonuria does not cause, apparently an error in converting the registry's laboratory records into HPO terms. Every system almost always missed them (the model asked directly solved 0.7%). As the plan required, the set was scored as published.

**Simulated sequencing (held-out cases, v1.0).** With the causal gene among fifty candidates, the other 49 drawn uniformly from known disease genes (a favourable setting), v1.0's ranking merged with the gene ranking (reciprocal-rank fusion, k = 60) reached 65.9% at first place on 839 cases, against 59.5% for the gene ranking without a model.

## S12. Models and dates

`deepseek-flash` was called through DeepSeek's API (api.deepseek.com) with reasoning mode off and temperature 0, between 13 October and 21 November 2026; its training data are reported to end in mid-2025. GPT-6.1 (`openai/gpt-6.1-sol`), Claude Sonnet 5.5 (`anthropic/claude-sonnet-5.5`) and Gemini 4 (`google/gemini-4-argon`) were called through OpenRouter at temperature 0 and the lowest reasoning effort it offers (`minimal`; none of the three allowed reasoning to be switched off): in October 2026 on the held-out, temporal and HMS cases (HMS on 15–16 October) and, for GPT-6.1, on 21 November 2026 on MyGene2. Each run records the model, prompt version, code commit and knowledge release among its MLflow parameters.

## S13. Planned secondary analyses not shown in the main text

- **Top ten, agent against its model asked directly** (first-place results in the main text): held-out cases 304 : 27; HMS 6 : 9; RAMEDIS 31 : 94; MyGene2 64 : 7; CADA 88 : 36; case reports 59 : 3.
- **Held-out cases by year of publication** (`heldout_plan.md`, exploratory): accuracy fell for newer papers for every system, including the phenotype similarity without a model (on answerable cases, from 26.5% at first place for papers before 2010 to 7.3% for papers from 2024); v1.0's lead over the fixed pipeline was 4–8 points in every period.
- **Memory, on the temporal set** (`temporal_plan.md`): taking rank-then-check as the reference, v1.0 led it by 10.5 points on the 819 held-out cases published before June 2025 and by 8.5 on the 47 temporal cases; the model asked directly was 18.2 and 6.4 points below it. The agent's lead shrank by two points; with 47 cases this is weak evidence.
- **Frontier models against LIRICAL** on the fixed 200 held-out cases: none of the three differed significantly from LIRICAL (p from 0.23 to 0.89).
- **Not run, for budget** (stated in the plans): the frontier models on the 200 RAMEDIS cases; on the three later tests, v2 on the patient sets, v1.1 on the case reports, Claude Sonnet 5.5 and Gemini 4, GPT-6.1 beyond MyGene2, and judges from other providers.
