Completed TRIPOD+AI checklist (Collins GS, Moons KGM, Dhiman P, et al. BMJ 2024;385:e078378) for this study. The study evaluates a diagnostic agent: a pretrained language model with fixed prompts and tools that ranks candidate diagnoses from a patient's phenotype findings. Nothing was fitted to test data; the agent's revisions were built on development sets only. Items that TRIPOD+AI applies only to model development (9a, 12a–c, 15, 22, 27a–b) are answered for the agent's design where they apply. Checklist items are abridged; section names refer to the main manuscript, and "{S}" is the supplementary methods and results.

| Section | Item | Checklist item (abridged) | Where reported / response |
|---|---|---|---|
| Title | 1 | Identify the study as developing or evaluating a prediction model, the target population and the outcome | Title: tests of a diagnostic agent for rare disease diagnosis. |
| Abstract | 2 | See TRIPOD+AI for Abstracts | Abstract: objectives, data, the agent and its main comparator, primary outcome with point estimates for each prespecified test, conclusion. |
| Background | 3a | Healthcare context (diagnostic or prognostic), rationale, existing models | Introduction: phenotype-driven diagnosis of rare diseases; existing tools and language-model agents, with references. |
| | 3b | Target population, intended purpose and users | Patients with a suspected rare disease whose findings are recorded as Human Phenotype Ontology terms; the intended use is support in ranking candidate diagnoses (Introduction). Intended users are not named in the manuscript, and use by clinicians was not tested (Discussion, Limitations). |
| | 3c | Known health inequalities between sociodemographic groups | Not addressed: the public data sets record at most the patient's sex. |
| Objectives | 4 | Objectives; development or validation | Introduction, last paragraph: evaluation of the agent, including three prespecified tests on cases never used in its development. |
| Data | 5a | Sources of data for development and evaluation; rationale; representativeness | Methods, Cases; Table 1; {S}, S1 and S3: published patients (Phenopacket Store), a clinic's and a metabolic registry's patients (RareBench HMS and RAMEDIS), patients shared by families and clinicians (MyGene2), diagnostic laboratories and clinics (CADA), and PubMed case reports. Published cases differ from patients as clinics record them (Introduction). |
| | 5b | Dates of the data | Phenopacket Store release 0.1.27; temporal cases first public on or after 1 June 2025; case reports that entered PubMed between 1 June 2025 and 24 October 2026; every data set pinned by version ({S}, S1, S3). |
| Participants | 6a | Setting; number and location of centres | Table 1 and Methods, Cases: one clinic (HMS), one metabolic registry (RAMEDIS), ClinVar submissions, seven collaborating cohorts and the PEDIA cohort (CADA), families and clinicians (MyGene2), published cases. |
| | 6b | Eligibility criteria | Methods, Cases: a confirmed OMIM diagnosis (Phenopacket Store, MyGene2, CADA); the case-report inclusion rule ({S}, S3). |
| | 6c | Treatments | Not applicable. |
| Data preparation | 7 | Pre-processing and quality checking | Findings as HPO terms; findings recorded as absent withheld (Task and scoring); case-report text cut before the diagnosis and read into HPO terms by the note reader, with an audit of 30 development-side reports (Cases; {S}, S3, S5). |
| Outcome | 8a | Definition of the outcome; how and when assessed | Methods, Task and scoring: the confirmed diagnosis within the first k answers (k = 1, 3, 5, 10), matched by identifier, including exact Mondo mappings; also judged by name. |
| | 8b | Qualifications of outcome assessors if subjective | Identifier scoring is automatic. Name judging used a language model (`deepseek-flash`), not a clinician (Discussion, Limitations). |
| | 8c | Blinding of outcome assessment | Systems are not given the diagnosis, though in an audit of 30 development-side case reports it remained readable in 3 (Cases; Discussion, Limitations); scoring against the recorded diagnosis is automatic; each case's known source paper is masked from the tools (Knowledge and masking). |
| Predictors | 9a | Choice of initial predictors | Not applicable: no predictors were selected or fitted. |
| | 9b | Definition of predictors | The case's HPO terms recorded as present, and sex where recorded (Task and scoring). |
| | 9c | Qualifications of predictor assessors if subjective | HPO terms were recorded by each data source; for the case reports, by the note reader, a language model ({S}, S3, S5). |
| Sample size | 10 | How the study size was arrived at | Each set as fixed in its plan (Table 1): the held-out and temporal sets take one case per paper, and the case-report test side stopped at its planned 240 reports, taken in a seeded random order ({S}, S3). No sample-size calculation was made; precision is shown by 95% Wilson intervals. |
| Missing data | 11 | Handling of missing data | A case without an answer counts as a miss (Task and scoring); runs with incomplete records were void and repeated without their score being read ({S}, S6). |
| Analytical methods | 12a | How the data were used; partitioning | Papers split before any development into a design split and held-out papers; development and test sets in Table 1 (Cases). |
| | 12b | Handling of predictors | Not applicable (no fitted model). |
| | 12c | Type of model, building steps, tuning, internal validation | A tool-using agent on a pretrained language model (`deepseek-flash`, temperature 0) with fixed prompts and tools; versions built on development sets only (The agent; {S}, S2, S4). |
| | 12d | Heterogeneity across clusters | CADA by source cohort, and results by number of findings (Results, What the lead is made of; {S}, S10). |
| | 12e | Performance measures and model comparison | Top-1, 3, 5 and 10 accuracy with Wilson intervals; paired exact sign tests; Holm adjustment of the three primary tests; Wald intervals for paired differences (Task and scoring). ROC and calibration measures do not apply to a ranked list of diseases. |
| | 12f | Model updating after evaluation | The agent was revised after the first version failed on the external patient sets (Results; The agent); the revisions were built on development sets, which by then included those external sets. No system was changed during a prespecified test. |
| | 12g | How predictions were calculated in evaluation | By running the agent's code from the project repository against the model's API; model identifiers and dates in {S}, S12. |
| Class imbalance | 13 | Class imbalance methods | Not applicable. |
| Fairness | 14 | Approaches to model fairness | Not assessed: sociodemographic data are largely absent from the public sets. |
| Model output | 15 | Output of the model; thresholds | A ranked list of up to ten diseases with OMIM or Orphanet identifiers; no thresholds (Task and scoring). |
| Training versus evaluation | 16 | Differences between development and evaluation data | Table 1 and Cases: published cases against patients of clinics, registries, families and laboratories; the CADA test file comes from a source that also supplied a development set (Discussion, Limitations). |
| Ethical approval | 17 | Ethics committee approval or waiver | Not applicable: only public, de-identified data were used and the study was not submitted for ethics review ({DECL}). |
| Open science | 18a | Funding | No specific funding ({DECL}). |
| | 18b | Conflicts of interest | None ({DECL}). |
| | 18c | Protocol | Each test's plan was committed to the project repository before its run ({S}, S7). |
| | 18d | Registration | Not registered in a study registry; the plans are timed by git commits ({S}, S7). |
| | 18e | Data sharing | Data availability statement ({DECL}); every data set is public and pinned by version. |
| | 18f | Code sharing | Project repository ({DECL}). |
| Patient and public involvement | 19 | Patient and public involvement | None: patients and the public were not involved in this study, which used public data only. |
| Participants (results) | 20a | Flow of participants | Table 1; {S}, S1 (cases per set) and S3 (case-report build counts). |
| | 20b | Characteristics of each data source | Cases; Table 1; {S}, S10 (findings per case). |
| | 20c | Comparison with the development data | Not compared formally; the share of relatively common diseases in the held-out set (42 of 840) and the number of findings per set are reported (Cases; Results; {S}, S10). |
| Model development | 21 | Numbers of participants in each analysis | Table 1; Results; tables. |
| Model specification | 22 | Details of the full model to allow predictions in new individuals | Code, prompts and tool definitions in the project repository and {S}, S4; the agent calls the publicly available `deepseek-flash` API. |
| Model performance | 23a | Performance estimates with confidence intervals, including subgroups | Results; tables and figures; CADA by cohort; by number of findings ({S}, S10). |
| | 23b | Heterogeneity across clusters | CADA by source cohort (descriptive). |
| Model updating | 24 | Results of model updating | Results, Prespecified tests of the revised agent. |
| Interpretation | 25 | Overall interpretation | Discussion. |
| Limitations | 26 | Limitations | Discussion, Limitations. |
| Usability | 27a | Handling of poor-quality or unavailable input data | The agent answers from whatever findings are given; sparse records (CADA, median five findings) are discussed in Results. |
| | 27b | User interaction and expertise | Input is a list of HPO terms, or a clinical note read by the note reader; use by clinicians was not tested. |
| | 27c | Next steps | Not given as a separate section; the Limitations state what was not tested (clinicians, prospective use, other models on the new sets). |
