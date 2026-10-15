"""Published patients to try the service on.

A short list of cases from the held-out set (examples.tsv, beside this file),
chosen to show different outcomes of the evaluation: an easy case, one the
agent rescued, two that sequencing settles, and one nobody can answer. Each is
offered as the request the evaluation made for it: its own paper left out of
the knowledge, and — optionally — the simulated sequencing of the genotype
track. With the patient bank of the evaluation, the service then answers an
example under the conditions it was measured in.

Two examples also come as a clinical note (notes/, beside this file), written
for the demo from the patient's published findings in the words a clinician
might use — not a real note — to try reading a note into terms.
"""

from importlib.resources import files

from raredx.data.cases import Case
from raredx.evals import candidates
from raredx.knowledge.hpo import HPO
from raredx.service.schemas import DiagnoseRequest, Example, Finding, Sex

LISTED = "examples.tsv"
NOTES = "notes"
SEX: dict[str | None, Sex] = {"FEMALE": "female", "MALE": "male"}


def listed() -> list[tuple[str, str, str]]:
    """The listed examples as (case id, title, what the evaluation recorded)."""
    text = files("raredx.service").joinpath(LISTED).read_text(encoding="utf-8")
    rows = [line.split("\t") for line in text.splitlines() if line and not line.startswith("#")]
    return [(case_id, title, note) for case_id, title, note in rows[1:]]  # rows[0]: the header


def load(cases: list[Case], hpo: HPO) -> list[Example]:
    """The listed cases found among `cases`, as examples."""
    by_id = {c.id: c for c in cases}
    examples = []
    for case_id, title, note in listed():
        case = by_id.get(case_id)
        if case is None or case.pmid is None:  # examples are published cases
            continue
        written = files("raredx.service").joinpath(NOTES, f"{case.id}.txt")
        examples.append(
            Example(
                id=case.id,
                title=title,
                note=written.read_text(encoding="utf-8") if written.is_file() else None,
                request=DiagnoseRequest(
                    hpo_ids=case.hpo_ids,
                    sex=SEX.get(case.sex, "unknown"),
                    exclude_sources=[case.pmid],
                ),
                findings=[
                    Finding(hpo_id=i, label=label)
                    for i, label in zip(case.hpo_ids, case.hpo_labels, strict=True)
                ],
                candidate_genes=candidates.candidate_genes(case, hpo) if case.gene else None,
                confirmed_disease_id=case.disease_id,
                confirmed_disease_name=case.disease_label,
                confirmed_gene=case.gene,
                source=case.pmid,
                in_evaluation=note,
            )
        )
    return examples
