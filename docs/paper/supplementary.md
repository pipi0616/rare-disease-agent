---
title: "Supplementary material"
subtitle: "A tool-using agent for rare-disease diagnosis, tested where its knowledge cannot leak"
---

## S1. Datasets and how each was used

**Table S1.** Every set of cases, its source and its role. "Test" sets were run on once by each system, under a plan committed before the first run.

| set | cases | source | role |
|---|---|---|---|
| Design split | 6,014 patients (893 papers) | Phenopacket Store 0.1.27 | development; bank of similar patients |
| dev-200 | 200 (one per paper) | design split | development: every design decision |
| Held-out | 840 (one per paper) | Phenopacket Store 0.1.27, papers disjoint from the design split | test of v1.0; a fixed 200 for systems billed per case |
| Temporal | 47 (one per paper) | papers first public on or after 2025-06-01 | test of v1.0, then of v1.1 |
| HMS | 88 | RareBench (a clinic's patients) | test of v1.0; development afterwards |
| RAMEDIS | 624 | RareBench (a metabolic registry) | test of v1.0; development afterwards |
| MME | 40 | RareBench (published cases) | test of v1.0 and v1.1; development afterwards |
| RareArena sample | 498 | case reports read into HPO terms | development |
| CADA development | 300 | CADA training file, fixed random sample | development |
| **MyGene2** | 146 | patients shared by families and clinicians | **test of v1.1** |
| **CADA test** | 577 | CADA test file, patients with an OMIM diagnosis | **test of v1.1** |
| **Case reports after the cutoff** | 240 built ([[CR-N]] with findings read) | PubMed case reports first public on or after 2025-06-01 | **test of v2** (development side: 300, not used here) |

Data that were considered and not used: the 75 Peking Union Medical College Hospital cases of RareBench (withdrawn from the public archive by its authors in December 2024); MIMIC-IV-Rare (requires credentialed access, and its use policy excludes services whose data handling cannot be verified); the Xinhua and Hunan hospital cohorts of DeepRare (controlled access); the Undiagnosed Diseases Network (controlled access); RareBench's LIRICAL subset (its file names no source papers, so the cases cannot be masked).

## S2. Choosing between the two revisions

**Table S2.** Agent v2 against v1.1 on the development sets, first place; paired counts are cases only the first-named system solved against cases only the second solved (two-sided exact sign test).

| development set | cases | v2, top-1 / top-10 | v1.1, top-1 / top-10 | v2 : v1.1 | v2 : model asked directly |
|---|---|---|---|---|---|
| CADA development | 300 | 22.3% / 49.0% | 23.7% / 49.3% | 13 : 17 (p = 0.59) | 29 : 10 (p = 0.003) |
| HMS | 88 | 39.8% / 65.9% | 37.5% / 56.8% | 9 : 7 (p = 0.80) | 9 : 2 (p = 0.065) |
| MME | 40 | 70.0% / 90.0% | 72.5% / 87.5% | 2 : 3 (p = 1.00) | 27 : 1 (p < 0.001) |
| dev-200 | 200 | 38.5% / 61.5% | 41.5% / 64.0% | 10 : 16 (p = 0.33) | 49 : 1 (p < 0.001) |
| RAMEDIS (200) | 200 | not run | — | — | — |

The rule, written before v2's development results were seen: v2 is the system to test if it is significantly worse than v1.1 on no development set and solves at least as many cases in total; otherwise v1.1. Pooled over the four sets that were run, v2 solved 207 cases and v1.1 216 (paired 34 : 43), so v1.1 was tested on MyGene2 and CADA. The fifth set was not run, for cost; the guard in v2 was expected to help most there, so the comparison is, if anything, unfavourable to v2. On the same CADA development cases v1.1 solved 23.7%, the model asked directly 16.0%, the no-model ranking 14.0% and LIRICAL 13.3% (v1.1 against the model: 35 : 12, p = 0.001).

Before v2 was built, eighteen combinations of similarity, ordering and knowledge were compared without a model on six development sets, against a rule fixed beforehand (no set significantly worse at first place or in the top ten, at least two significantly better). One passed: the one-way similarity in its own order on the knowledge with Orphanet merged in.

## S3. The case-report set

**Procedure** (rules committed before any report from after the cutoff was read; see `docs/casereports_plan.md` in the repository, with its history).

1. *Candidates.* PubMed: publication type "Case Reports", English, open-access full text in PMC, entered between 2025-06-01 and 2026-10-24 (71,351 records). One random order by a fixed seed (20261025); processed in that order.
2. *Annotator A.* PubTator3 on the title and abstract; disease mentions as MeSH identifiers; each mapped to a Mondo class by Mondo's exact matches, and through it to OMIM and Orphanet identifiers. A "rare disease of the knowledge base" is a class that matches an Orphanet entry and has a disease in the merged knowledge base.
3. *First rules, on A alone.* The paper is not used elsewhere in the project; it first became public on or after the cutoff; its title names exactly one rare disease of the knowledge base; the side that disease belongs to still has room (at most three reports per disease; at least a third of each side relatively common diseases).
4. *Full text.* The paragraphs of the section that the PMC BioC service types as the case. Section titles, tables and figure captions are not read.
5. *Annotator B.* The model (temperature 0, fixed prompt, below) reads the title, the abstract and the numbered sentences of the case description and returns the final diagnosis, the number of patients, whether the description begins before the diagnosis was known, and the number of the first sentence that gives the diagnosis away.
6. *Agreement.* B's diagnosis is matched by name (the matching of the agent's `find_disease` tool: rapidfuzz WRatio at least 90) against every form of every disease's name — each part of its name in the knowledge base, its Mondo name and Mondo's exact synonyms — and must be the disease A found in the title. A written diagnosis more than 2.2 times as long as the form it matches does not count. A report is kept only on agreement; nothing is adjudicated by a person.
7. *Further rules.* One patient; the description begins before the diagnosis was known; at least 60 words remain after the cut.
8. *The cut.* Everything from the first revealing sentence on is dropped. That sentence is the earliest of: B's sentence; the first sentence in which a program finds a name, synonym or abbreviation of the disease (also the name without the type it ends in) or one of its genes; the first sentence that mentions a confirming test (biopsy, histology, immunohistochemistry, cytology, bone marrow, culture, PCR, sequencing, karyotype, FISH, mutation, zygosity, serology, antibody, antigen). Nothing is rewritten.
9. *Sides.* A disease is on the test side with probability 240/540 by a draw that depends only on the disease and the seed.
10. *Reading.* The kept text is read into HPO terms by the note reader; only findings stated as present are used.

**Annotator B's prompt (version casereport-key-v3).**

> You read one published case report and answer four questions about it. Reply with a json object and nothing else: {"diagnosis": "...", "patients": 1, "diagnostic": true, "reveal": 7}
>
> - "diagnosis": the patient's final diagnosis, the disease the report is about: the disease's name alone, as the authors write it in full — no site, cause, complication or circumstance around it, not an abbreviation alone, not a group of diseases when they give the specific one. If what looked like one disease turned out to be another thing (a foreign body, a drug reaction), name what it turned out to be.
> - "patients": how many patients the report describes.
> - "diagnostic": true if the case description begins before the diagnosis was known and tells how it was reached; false if the diagnosis is already known where the description begins (a report about treating or following a known disease).
> - "reveal": the number of the first sentence of the case description from which a reader would know the diagnosis, or null if there is none. It is the first sentence that does any of these: (a) names the disease, a synonym or its abbreviation, or says it is suspected, considered or to be ruled out; (b) names its causal gene, a variant, or the organism that causes it; (c) reports the result of a test done to establish it — genetic or molecular testing; a biopsy, histopathology, cytology or bone-marrow examination; a culture, PCR, antigen test or serology for the organism; an antibody or enzyme assay specific to the disease — or says that such a test for this disease was ordered; (d) names a treatment used only for this disease. Symptoms, signs, routine blood tests and imaging findings do not give it away, unless the sentence also names the disease.

**Pilot.** On 783 case reports entered in the first week of March 2025 (before the cutoff; never used as cases), the first 368 in the fixed order gave 120 that annotator A let through and 18 accepted reports. The pilot changed four rules before any report from after the cutoff was read: disagreements are dropped rather than adjudicated by a person (the builder is also the developer, and would otherwise read test cases); a written diagnosis far longer than the name it matches does not count (a title — "a forgotten foreign body presenting as allergic bronchopulmonary aspergillosis" — had matched the disease it was mistaken for); names are matched against synonyms too; and only diseases that Orphanet lists are kept (osteoporosis had been accepted through an OMIM susceptibility entry).

**First build and audit.** A first build under these rules stopped at 154 accepted reports (58 test side, 96 development side) of 6,177 processed. Of the 2,286 that annotator A let through, 865 named the disease only in the abstract, 491 had no full text in the BioC service (about half of the papers from 2026), 325 had first become public before the cutoff, 181 failed on B's diagnosis (133 not found in the knowledge base, 48 disagreeing with A), 90 had no case section, 87 named more than one rare disease in the title, 61 were not a single patient or began with the diagnosis known, 18 kept fewer than 60 words, and 14 exceeded three reports per disease. Thirty development-side reports, drawn by a fixed seed, were read by one of us; the test side was not read. The answer key matched the title and B's diagnosis in all 30 (in seven, a subtype or site had been mapped to the disease itself). In about six of the 30 the diagnosis could still be read from the kept text: a confirming test's result (39% blasts in the marrow for acute myeloid leukaemia, twice; amyloid in a renal biopsy; specific IgE to *Aspergillus*), a test for the disease being ordered (an *SS18* break-apart probe), or the disease's name inside a sentence that the splitter had joined to the next. The cut was therefore made stricter — the confirming-test rule, a splitter that handles a missing space, the name without its type — and the set rebuilt from the start of the same order, with annotator B asked again under the stricter prompt.

**Final build.** Under the stricter cut both sides were filled after 35,895 of the 71,351 candidates: 240 test reports (142 diseases; 130 with a relatively common diagnosis) and 300 development reports (188 diseases; 135 relatively common), sharing no disease, first public between 1 June 2025 and 13 July 2026. The kept text has a median of 186 words on either side (interquartile range 130–301 and 121–274). Of the 13,605 papers that annotator A let through, 5,071 named the disease only in the abstract, 1,988 had first become public before the cutoff, 1,939 had no full text in the BioC service, 1,133 belonged to the development side after it was full, 948 exceeded three reports per disease, 696 failed on annotator B's diagnosis (478 not found in the knowledge base, 218 disagreeing with A), 495 named more than one rare disease in the title, 356 had no case section, 349 were not a single patient or began with the diagnosis known, 83 kept fewer than 60 words, and 7 were used elsewhere in the project. Annotator B was asked 1,668 times (US$0.79 at list price).

**Second audit.** Thirty development-side reports of the final build, drawn by a fixed seed, were read by one of us; the test side was not read. The answer key was right in 29; in one, a report of liquorice-induced apparent mineralocorticoid excess had been keyed to the inherited disease of the same name. In three the diagnosis could still be read from the kept text: the opening pressure at lumbar puncture (idiopathic intracranial hypertension), the words "pulmonary hypertension" in a sentence about what had not been investigated (pulmonary arterial hypertension), and an abbreviation that Mondo does not list (SOS, for sinusoidal obstruction syndrome). The rules were left as they were, as fixed beforehand; about one test report in ten can therefore be expected to give its diagnosis away in the text. Every system is given the same terms read from that text.

## S4. Prompts

**The model asked directly** (also the agent's first answer; version direct-v2).

> You are a clinical geneticist. You will be given the phenotype of a patient with a suspected rare disease, as Human Phenotype Ontology (HPO) terms. List the 10 most likely diagnoses, most likely first. For each, give: disease_name: the name of the disease; disease_id: its OMIM phenotype number, written OMIM:nnnnnn (six digits); for a disease with no OMIM entry, its Orphanet code, written ORPHA:n; gene: the HGNC symbol of the causal gene, if it has one. Answer with a json object only, in exactly this format: {"candidates": [{"disease_name": "...", "disease_id": "OMIM:123456", "gene": "ABC1"}]}

The user message lists the patient's sex, when known, and each finding as "label (HPO id)".

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

The pre-registered primary claim — better than both baselines on the clinical notes — failed: paired per note, the reader beat the model writing identifiers (58 notes to 5, p < 0.001) but not the dictionary (29 to 38, p = 0.33). On the abstracts it beat both (122 to 31; 160 to 11).

## S6. Runs that were void

A run whose records were incomplete was void and repeated without its score being read. During the tests of Section 3.6 this happened to: the no-model ranking on MyGene2 once (11 of 146 records lost to a locked database; the tests were thereafter recorded in a store of their own); the model asked directly on MyGene2 twice and agent v1.1 on MyGene2 [[PENDING — count]] times (the process was killed with the session, by a kernel panic of the shared machine, or stopped to protect it from memory exhaustion); LIRICAL on MyGene2 once (stopped: too many parallel Java processes). No score of a void run was computed or seen. [[PENDING — final list]]
