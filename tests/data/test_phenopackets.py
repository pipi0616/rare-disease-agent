"""The loader on a three-case store built in memory: no network, no 19 MB archive."""

import json
import zipfile
from pathlib import Path
from typing import Any

import pytest

from raredx.data import phenopackets as pp


def packet(
    case_id: str,
    pmid: str,
    *,
    features: list[tuple[str, str, bool]],
    disease: tuple[str, str] | None = ("OMIM:620371", "ESAM-related disorder"),
    gene: str | None = "ESAM",
) -> dict[str, Any]:
    """A phenopacket with only the parts the loader reads. (id, label, excluded) per feature."""
    diagnosis: dict[str, Any] = {}
    if disease:
        diagnosis["disease"] = {"id": disease[0], "label": disease[1]}
        if gene:
            diagnosis["genomicInterpretations"] = [
                {
                    "variantInterpretation": {
                        "variationDescriptor": {
                            "geneContext": {"valueId": "HGNC:17474", "symbol": gene},
                            "expressions": [
                                {"syntax": "hgvs.c", "value": "NM_138961.3:c.35T>A"},
                                {"syntax": "hgvs.p", "value": "NP_620411.2:p.(Leu12Ter)"},
                            ],
                            "allelicState": {"id": "GENO:0000136", "label": "Homozygous"},
                        }
                    }
                }
            ]
    return {
        "id": case_id,
        "subject": {"id": "Individual 1", "sex": "FEMALE"},
        "phenotypicFeatures": [
            {"type": {"id": hpo, "label": label}, "excluded": excluded}
            for hpo, label, excluded in features
        ],
        "interpretations": [{"id": "x", "diagnosis": diagnosis}] if disease else [],
        "metaData": {"externalReferences": [{"id": pmid}]},
    }


@pytest.fixture
def archive(tmp_path: Path) -> Path:
    path = tmp_path / "all_phenopackets.zip"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(
            "0.1.27/ESAM/complete.json",
            json.dumps(
                packet(
                    "complete",
                    "PMID:1",
                    features=[
                        ("HP:0001250", "Seizure", False),
                        ("HP:0000319", "Smooth philtrum", True),
                        ("HP:0001263", "Global developmental delay", False),
                    ],
                )
            ),
        )
        z.writestr(
            "0.1.27/ESAM/all_excluded.json",
            json.dumps(
                packet("all_excluded", "PMID:1", features=[("HP:0001250", "Seizure", True)])
            ),
        )
        z.writestr(
            "0.1.27/22q11/no_gene.json",
            json.dumps(
                packet(
                    "no_gene",
                    "PMID:2",
                    features=[("HP:0001250", "Seizure", False)],
                    disease=("OMIM:188400", "DiGeorge syndrome"),
                    gene=None,
                )
            ),
        )
        z.writestr("0.1.27/README.md", "not a case")
    return path


def test_load_keeps_observed_features_and_reads_every_field(archive: Path) -> None:
    cases, skipped = pp.load(archive)
    by_id = {c.id: c for c in cases}
    c = by_id["complete"]
    assert c.hpo_ids == ["HP:0001250", "HP:0001263"]  # the excluded feature is gone
    assert c.hpo_labels == ["Seizure", "Global developmental delay"]
    assert (c.disease_id, c.disease_label) == ("OMIM:620371", "ESAM-related disorder")
    assert c.gene == "ESAM" and c.cohort == "ESAM" and c.pmid == "PMID:1" and c.sex == "FEMALE"
    assert c.variants[0].hgvs_p == "NP_620411.2:p.(Leu12Ter)"
    assert c.variants[0].zygosity == "homozygous"
    assert skipped == {"no_phenotype": 1}


def test_case_without_a_gene_is_kept(archive: Path) -> None:
    cases, _ = pp.load(archive)
    no_gene = next(c for c in cases if c.id == "no_gene")
    assert no_gene.gene is None and no_gene.variants == []
    assert no_gene.disease_id == "OMIM:188400"


def test_split_is_by_pmid_and_fixed() -> None:
    assert pp.split_of("PMID:36996813") == pp.split_of("PMID:36996813")
    assert {pp.split_of(f"PMID:{i}") for i in range(200)} == {"design", "heldout"}


def test_design_and_heldout_partition_the_cases(archive: Path) -> None:
    cases, _ = pp.load(archive)
    assert sorted(c.id for c in pp.design(cases) + pp.heldout(cases)) == sorted(c.id for c in cases)
    assert all(c.split == pp.split_of(c.pmid) for c in cases)
