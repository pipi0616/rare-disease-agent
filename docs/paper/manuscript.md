# A tool-using agent for rare-disease diagnosis, tested where its knowledge cannot leak: held-out reports, reports published after the model's cutoff, and patients from clinics and diagnostic laboratories

*Draft. Sections 3.6–3.7, the abstract's last sentences and the discussion are filled in after the pre-registered tests of `docs/exam_plan.md`.*

## Abstract

*(written last)*

## 1. Introduction

A patient with a rare disease waits years for a diagnosis, and phenotype-driven tools were built to shorten that wait: given the patient's findings as Human Phenotype Ontology (HPO) terms, they rank the diseases whose annotated phenotype fits best [Phenomizer; LIRICAL; Exomiser]. Large language models (LLMs) have since been put to the same question, alone [RareBench; Reese 2026] and as agents that call such tools and search the literature [DeepRare; liteOdyssey; RareAgents].

Three things make the reported accuracy of these systems hard to read.

**Benchmarks leak through the knowledge base.** The public cases come from published reports, and HPO's disease annotations are curated from published reports — often the same ones. A tool that reads the annotations while it is tested on the patient they were written from is reading the answer.

**Models may have read the test.** A public benchmark released before a model's training cutoff can be memorised. A model asked directly then looks stronger than it is, and so does any agent built on it.

**Literature cases are not patients.** A case report is a patient the authors chose and described after the diagnosis was known. Patients as a clinic or a diagnostic laboratory records them have fewer findings, and more of them have the commoner rare diseases.

This paper reports an agent built and tested with each of the three in view. The agent is deliberately plain: one inexpensive general-purpose model (`deepseek-flash`, reasoning mode off), a handful of tools over pinned public knowledge, at most eight model calls a case. What is unusual is how it was measured:

1. Every evaluation hides each case's own source paper from everything the tools read, and audits every tool output afterwards (Section 2.3). We quantify what the mask removes: for a published tool on published cases, half of its score.
2. Every test followed a plan committed to the repository before the run — which cases, which systems, which comparison decides — and each system ran once. Three pre-registered claims failed; they are reported as failures.
3. After a first version lost to its own model on patients curated elsewhere, we found the cause in its traces, revised it, and tested the revision on three sets no system had seen: patients shared by families and clinicians (MyGene2), patients of diagnostic laboratories and clinics (CADA's test set), and case reports first public after the model's training cutoff, cut before the sentence that gives the diagnosis away.

## 2. Methods

### 2.1 Task and scoring

A system is given a patient's findings as HPO terms (and nothing else: no diagnosis, no gene, no source) and answers with up to ten diseases, best first, each with an OMIM or Orphanet identifier. A case is solved at rank *k* when one of the first *k* identifiers is the confirmed diagnosis or an identifier that Mondo (release 2026-09-01) maps to it exactly. Names are not compared. A case with no answer is a miss and stays in the denominator. Rates carry 95% Wilson intervals. Two systems are compared on the same cases by the two-sided exact sign test on the cases where exactly one of them is right.

Systems that name diseases without reliable identifiers (models asked directly, DeepRare) are also scored by name, with DeepRare's own judging prompt and a judge model of another family than the model under test; both scorings are reported side by side, and pre-registered claims are decided by identifiers.

### 2.2 Cases

**Development and held-out cases (Phenopacket Store 0.1.27 [Danis 2025]).** 10,374 published patients with HPO-coded findings and a confirmed OMIM diagnosis, from 1,733 papers (780 diseases). Papers, not patients, were split at the start: 6,014 patients for development (the "design" split, which also fills the bank of similar patients one tool searches), 4,360 patients from 840 papers held out. A development set of 200 cases, one per paper, was used for every design decision; the held-out test takes one case from each of the 840 papers.

**Temporal test.** One case from each paper the store added that first became public on or after 1 June 2025, the reported end of the model's training data: 47 cases.

**Other development sources**, added after the first external test (Section 3.4): RareBench's HMS (88 patients of a clinic), RAMEDIS (624 patients of a metabolic registry) and MME (40 published cases) [RareBench]; 498 case reports from RareArena read into HPO terms; and 300 of CADA's training patients.

**Three tests of the revised agent** (Section 3.6), fixed before any system ran on them:

| test set | cases | source | why it is hard |
|---|---|---|---|
| MyGene2 | 146 | patients shared on mygene2.org by families and clinicians, as preprocessed for SHEPHERD (CC0) | not selected for publication; reported on by DeepRare |
| CADA test | 577 | ClinVar submissions carrying HPO terms, and patients of the CADA authors' collaborating clinics; the authors' own test split, cases with an OMIM diagnosis | patients as a diagnostic laboratory records them: few findings |
| Case reports after the cutoff | *n* | PubMed case reports with open-access full text, first public on or after 1 June 2025 | the model cannot have read them; verbatim text, cut before the diagnosis is given away; no disease shared with the development side |

The case-report set was built by a fixed procedure (`docs/casereports_plan.md`). Candidates (71,351 PubMed case reports in English with open-access full text, entered between 1 June 2025 and 24 October 2026) were put in one random order by a fixed seed and processed in that order. Two independent annotators named each report's diagnosis: PubTator3 from the title and abstract (MeSH identifiers, mapped through Mondo), and the model from the title, abstract and case description. A report was kept only if the title named exactly one rare disease of the knowledge base (one that Orphanet lists) and the model's diagnosis, matched by name, was that disease; disagreements were dropped, not adjudicated. The case description — the paragraphs of the section the PMC BioC service types as the case — was cut before the first sentence that gives the diagnosis away: the sentence the model pointed to, or the first in which a program finds the disease's name, a synonym or its gene, whichever is earlier. Nothing was rewritten. Each disease was assigned to the test side or the development side by a draw that depends only on the disease and the seed, so the two sides share no disease. The kept text was read into HPO terms by the note reader (Section 2.4). The procedure was piloted on reports from before the cutoff; the rules the pilot changed are listed in the plan. No one read the test side before the test.

### 2.3 Knowledge and leakage control

The tools read HPO's disease annotations (release 2026-09-01; 8,478 OMIM diseases) and, in the revised agent, Orphanet's as well, merged by Mondo's exact matches (2,122 Orphanet entries merged into their OMIM disease; 2,233 Orphanet diseases of their own), plus Orphanet's prevalence classes and short disease descriptions (Orphanet, MedlinePlus Genetics).

While a system works on a case, the case's source paper is masked from all of it:

- an annotation line supported only by that paper is removed; a line other papers also support stays, without the masked paper among its sources;
- a disease known only from that paper does not exist for any tool — not in rankings, not by name, not as a similar patient's diagnosis — and a tool asked about it answers exactly as for an identifier that was never assigned;
- patients from that paper are not in the bank of similar patients.

After each run, every tool output recorded in the traces is searched for the case's own paper and for diseases known only from it; a run with a single hit is void. A case with no paper (a clinic's patient) has nothing to mask.

### 2.4 The agent

All versions run on LangChain's `create_agent` (LangGraph) with `deepseek-flash`, reasoning mode off, temperature 0, and at most eight model calls per case; the last call is offered only the final answer. Tools: `rank_diseases` (every disease ranked by phenotype similarity to the patient), `check_match` (the patient's findings against one disease: explained, unexplained, recorded absent, and the disease's frequent features the patient lacks), `lookup_disease`, `find_disease` (an identifier from a name), `find_similar_patients` (the closest published patients of the design split, with their diagnoses), and `search_disease_texts`.

- **v1.0 (seeded agent)** starts from the tools' evidence: the ten best candidates of a no-model ranking (the similarity's top thirty, reordered by findings explained), each with its match report. Its turns go to what the tools cannot do, such as a disease it suspects that they did not propose.
- **v1.1 (hypothesis agent)** first answers from the model's own knowledge, before any tool runs. Each disease it names is found in the knowledge base and checked like the tools' candidates; the first message shows both lists, each candidate with Orphanet's prevalence class, and the prompt asks it to weigh them as equals.
- **v2** is v1.1 with three changes, each measured without a model on the development sources beforehand: Orphanet's diseases merged into the knowledge; the tools' list taken from a one-way similarity (the patient's findings looked for in the disease, not the disease's in the patient), in its own order; and a guard on the final order — when the model's own first answer is a relatively common rare disease (Orphanet: one patient in 100,000 or more) that the tools also rank in their top thirty, it leads.

A clinical note is read into HPO terms by a separate reader before diagnosis: the model lists each finding with the note's words and its status, and never writes an identifier; exact names are coded directly, the rest chosen among candidates from a hybrid search over HPO's names and synonyms.

### 2.5 Comparators

The same model asked once, without tools; a fixed pipeline (the tools' top ten with their evidence, ranked by one model call); the no-model ranking; LIRICAL 2.4.1 given, for each case, its own copy of the annotation file written under the mask; three other providers' current models asked directly with the same prompt (GPT-6.1, Claude Sonnet 5.5, Gemini 4); and DeepRare run from its code on the agent's model.

### 2.6 Plans

Each test followed a plan committed before its first run (`docs/heldout_plan.md`, `comparison_plan*.md`, `temporal_plan.md`, `external_plan.md`, `phenotyping_plan.md`, `exam_plan.md`): the cases, the systems and their frozen version, the one comparison that decides the primary claim, and the rule that each system runs once. Runs that lost cases to model-API failures were completed by asking only those cases again. Every run, with every model call and tool call, is recorded in MLflow.

## 3. Results

### 3.1 An unmasked benchmark of published cases is about half leakage

On 200 development cases the phenotype-similarity tool finds the confirmed disease in its top ten for 82.0% with each case's own paper left in the knowledge, and for 49.0% with it masked. For 153 of the 200 cases, HPO's annotation of the confirmed disease cites the case's own paper. LIRICAL on the 840 held-out cases scores 63.2% at first place unmasked and 30.1% masked; the whole gain comes from the 75% of cases whose disease annotation cites their paper, and on the other 25% the mask changes no answer.

### 3.2 Held-out published cases

*(v1.0, 840 cases, one run per system; primary claim fixed beforehand: the agent against the fixed pipeline at first place.)*

| system | top-1 | top-10 |
|---|---|---|
| **agent (v1.0)** | **42.4%** [39.1–45.8] | **62.0%** [58.7–65.2] |
| fixed pipeline | 36.8% [33.6–40.1] | 51.5% [48.2–54.9] |
| rank, then check (no model) | 32.1% [29.1–35.4] | 51.5% [48.2–54.9] |
| LIRICAL | 30.1% [27.1–33.3] | 48.3% [45.0–51.7] |
| nearest published patients (no model) | 27.9% [24.9–31.0] | 50.2% [46.9–53.6] |
| phenotype similarity alone (no model) | 17.5% [15.1–20.2] | 44.4% [41.1–47.8] |
| the same model asked directly | 14.3% [12.1–16.8] | 29.0% [26.1–32.2] |

The primary claim holds: 57 cases to 10 at first place (p = 4 × 10⁻⁹). Against LIRICAL the agent is right alone on 121 cases and LIRICAL on 18. Under the mask, 122 cases cannot be answered by any tool-using system (their disease is known only from their own paper); on the other 718 the agent reaches 49.6%.

### 3.3 Against frontier models and another agent

On a fixed random 200 of the held-out cases the agent (43.0% at first place) is ahead of GPT-6.1 (33.0%; 37 : 17, p = 0.009), Gemini 4 (27.0%; 46 : 14) and Claude Sonnet 5.5 (23.5%; 52 : 13), each asked directly; the model inside the agent scores 15.0% on its own. DeepRare, run from its code on the same model, scores 8.5% by identifier and 27.5% by its own name-based judging, against the agent's 43.0% and 42.5% (48 : 18 judged, p < 0.001).

By Orphanet's prevalence class (not planned; descriptive), the model alone is level with the agent on the relatively common rare diseases (61.9% against 57.1%, 42 cases) and far behind on the rarest (9.6% against 52.6%, 272 cases).

### 3.4 Outside the curated source, the first version lost to its own model

Two further plans tested the frozen v1.0 once each.

| test | cases | agent (v1.0) | same model asked directly | paired |
|---|---|---|---|---|
| temporal: papers first public after the model's cutoff | 47 | 23.4% | 8.5% | 9 : 2 (p = 0.065) |
| HMS, a clinic's patients | 88 | 19.3% | 31.8% | 4 : 15 (p = 0.019) |
| RAMEDIS, a metabolic registry | 624 | 24.7% | 32.7% | 47 : 97 (p < 0.001) |

Both pre-registered claims failed. Three frontier models asked directly scored below `deepseek-flash` on HMS (14.8–22.7%), the reverse of their order on the held-out cases, which suggests that it has seen the public RareBench; that does not excuse the agent, which runs on the same model and did not use what the model knew.

### 3.5 Why, and what was changed

Read afterwards, the failure was one of ranking, not retrieval: where the model alone was right and the agent wrong, the agent's own top ten held the answer in 12 of 15 HMS cases and 85 of 97 RAMEDIS cases. Every tool scored how well a disease explains the findings and none how common it is; and the knowledge kept only OMIM's annotations, which describe the commoner rare diseases thinly (Behçet disease: 15 findings in OMIM's annotation, 85 in Orphanet's). The held-out set had hidden this: only 42 of its 840 cases have a relatively common diagnosis.

HMS and RAMEDIS, once read, became practice sets. The revised agent (v1.1) beat the model asked directly on the temporal cases, 10 : 2 (p = 0.039; the second version scored on that set), and was not shown better than v1.0 on a fresh external set of 40 published cases (MME: 72.5% against 80.0%, 1 : 4).

### 3.6 Three tests of the revised agent: patients, and reports the model cannot have read

*(to be filled from `docs/exam_plan.md`, section 7)*

### 3.7 Cost

*(to be filled)*

## 4. Discussion

*(to be written with the results)*

## Data and code availability

Code, manifests, plans and per-case outcomes: the project repository. Every dataset is public and pinned by version and checksum in `evals/datasets.toml`. The case-report texts are not redistributed (some licences are non-commercial); the committed table names each paper, the number of sentences kept and the checksum of the kept text.

## References

*(to be completed)*
