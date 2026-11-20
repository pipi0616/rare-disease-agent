"""MyGene2's and CADA's patients read into cases, on miniature files and the test HPO release."""

import json
from pathlib import Path

import pytest

from raredx.data import clinical
from raredx.data import rarebench as rb
from raredx.knowledge.hpo import HPO, gene_symbols

ORPHANET_XML = """<?xml version="1.0" encoding="UTF-8"?>
<JDBOR><DisorderList>
  <Disorder><OrphaCode>3</OrphaCode><Name>Seizure disorder, Orphanet's name</Name>
    <ExternalReferenceList>
      <ExternalReference><Source>OMIM</Source><Reference>690003</Reference>
        <DisorderMappingRelation><Name>E (Exact mapping: the two concepts are equivalent)</Name>
        </DisorderMappingRelation></ExternalReference>
    </ExternalReferenceList></Disorder>
</DisorderList></JDBOR>
"""

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


@pytest.fixture
def orphanet(tmp_path: Path) -> rb.Orphanet:
    path = tmp_path / "en_product1.xml"
    path.write_text(ORPHANET_XML, encoding="utf-8")
    return rb.Orphanet(path)


def patient(**fields: object) -> str:
    base: dict[str, object] = {
        "id": "family_1",
        "positive_phenotypes": ["HP:0000365"],
        "true_genes": ["ENSG00000000001"],
        "omim": "690001",
        "disease_name": "A name the file gives",
        "pubmed_id": None,
        "orpha_id": None,
    }
    return json.dumps(base | fields)


def test_mygene2_reads_the_diagnosis_by_rarebenchs_rules(
    tmp_path: Path, hpo: HPO, orphanet: rb.Orphanet
) -> None:
    path = tmp_path / "mygene2.txt"
    lines = [
        # an obsolete term and a repeat; an Orphanet code whose exact OMIM entry counts too;
        # a paper, written as the file writes it (a float)
        patient(
            positive_phenotypes=["HP:0099999", "HP:0000407", "HP:0000365"],
            orpha_id=[3],
            pubmed_id=12345678.0,
        ),
        patient(id="family_2", positive_phenotypes=["HP:9999999"]),  # no term left: dropped
        patient(id="family_3", omim="not a number"),  # no diagnosis to score: dropped
        patient(id="family_4", omim="600000"),  # an OMIM entry HPO does not annotate
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    cases, dropped = clinical.load_mygene2(path, hpo, orphanet)
    first, unknown = cases
    assert first.id == "MyGene2_family_1" and first.cohort == "MyGene2"
    assert first.hpo_ids == ["HP:0000407", "HP:0000365"]
    assert (first.disease_id, first.also_accepted) == ("OMIM:690001", ["OMIM:690003"])
    assert first.pmid == "PMID:12345678" and first.gene is None and first.split == "external"
    # a diagnosis nothing here names keeps its number, and the file's name for it
    assert (unknown.disease_id, unknown.disease_label) == ("OMIM:600000", "A name the file gives")
    assert unknown.pmid is None
    assert dropped == {"unknown_term": 1, "no_phenotype": 1, "no_omim": 1}


def row(patient_id: str, disease: str, gene: str, terms: str, origin: str = "clinvar") -> str:
    return "\t".join([patient_id, disease, gene, terms, "A laboratory", origin, "1", "2", "3", "4"])


def test_cada_keeps_the_authors_split_and_leaves_out_unknown_diagnoses(
    tmp_path: Path, hpo: HPO
) -> None:
    train = [
        row("Patient:144383", "OMIM:690001", "Entrez:1", "HP:0001730,HP:0000365,HP:0001250"),
        row("Patient:tubingen534", "unknown", "Entrez:2", "HP:0000365", "tubingen"),
        row("Patient:9", "OMIM:690003", "Entrez:4", "HP:9999999"),
    ]
    test = [row("Patient:F2G_7", "OMIM:690002", "Entrez:999", "HP:0000510", "f2g")]
    (tmp_path / "cases_train.tsv").write_text("\n".join(train) + "\n", encoding="utf-8")
    (tmp_path / "cases_test.tsv").write_text("\n".join(test) + "\n", encoding="utf-8")
    # the validation file is never opened: it need not even exist
    cases, dropped = clinical.load_cada(tmp_path, hpo, gene_symbols(FIXTURES / "hpo"))
    developed, tested = cases
    assert developed.id == "CADA_train_144383" and developed.cohort == "clinvar"
    assert developed.hpo_ids == ["HP:0000365", "HP:0001250"]  # the alternative id is the same term
    assert (developed.disease_id, developed.gene) == ("OMIM:690001", "GENEA")
    assert developed.disease_label == "Hearing-ovarian syndrome"
    assert tested.id == "CADA_test_F2G-7" and tested.cohort == "f2g"
    assert tested.gene is None  # a gene the release's table lacks: scored on the disease alone
    assert dropped == {
        "train:no_disease": 1,
        "unknown_term": 1,
        "train:no_phenotype": 1,
        "test:gene_not_in_hpo": 1,
    }


def test_cada_refuses_a_patient_id_listed_twice(tmp_path: Path, hpo: HPO) -> None:
    line = row("Patient:1", "OMIM:690001", "Entrez:1", "HP:0000365")
    (tmp_path / "cases_train.tsv").write_text(f"{line}\n{line}\n", encoding="utf-8")
    (tmp_path / "cases_test.tsv").write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="not unique"):
        clinical.load_cada(tmp_path, hpo, {})


def test_gene_symbols_skip_an_entry_without_a_symbol() -> None:
    symbols = gene_symbols(FIXTURES / "hpo")
    assert symbols["1"] == "GENEA" and "8" not in symbols
