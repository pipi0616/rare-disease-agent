"""RareBench's patients read into cases, on a miniature archive and the test HPO release."""

import json
import zipfile
from pathlib import Path

import pytest

from raredx.data import rarebench as rb
from raredx.knowledge.hpo import HPO

ORPHANET_XML = """<?xml version="1.0" encoding="UTF-8"?>
<JDBOR><DisorderList>
  <Disorder><OrphaCode>3</OrphaCode><Name>Seizure disorder, Orphanet's name</Name>
    <ExternalReferenceList>
      <ExternalReference><Source>OMIM</Source><Reference>690003</Reference>
        <DisorderMappingRelation><Name>E (Exact mapping: the two concepts are equivalent)</Name>
        </DisorderMappingRelation></ExternalReference>
    </ExternalReferenceList></Disorder>
  <Disorder><OrphaCode>81</OrphaCode><Name>Antisynthetase syndrome</Name>
    <ExternalReferenceList/></Disorder>
  <Disorder><OrphaCode>9</OrphaCode><Name>A broader group</Name>
    <ExternalReferenceList>
      <ExternalReference><Source>OMIM</Source><Reference>690005</Reference>
        <DisorderMappingRelation><Name>BTNT (Broader Term maps to a Narrower Term)</Name>
        </DisorderMappingRelation></ExternalReference>
    </ExternalReferenceList></Disorder>
</DisorderList></JDBOR>
"""


@pytest.fixture
def orphanet(tmp_path: Path) -> rb.Orphanet:
    path = tmp_path / "en_product1.xml"
    path.write_text(ORPHANET_XML, encoding="utf-8")
    return rb.Orphanet(path)


def test_every_listed_omim_entry_counts_and_a_known_one_leads(
    hpo: HPO, orphanet: rb.Orphanet
) -> None:
    # OMIM:600000 is not a disease in this release: the known entry leads, it stays accepted
    disease, also, label = rb.diagnosis(["OMIM:600000", "OMIM:690001", "CCRD:1"], hpo, orphanet)
    assert (disease, also) == ("OMIM:690001", ["OMIM:600000"])
    assert label == "Hearing-ovarian syndrome"  # HPO's name for it


def test_an_orphanet_code_brings_its_exact_omim_entry_only(hpo: HPO, orphanet: rb.Orphanet) -> None:
    assert rb.diagnosis(["ORPHA:3"], hpo, orphanet)[:2] == ("OMIM:690003", [])
    # a broader-to-narrower mapping is not the same disease: not accepted
    assert rb.diagnosis(["ORPHA:9"], hpo, orphanet)[:2] == ("ORPHA:9", [])


def test_a_patient_with_no_omim_entry_keeps_its_own_code(hpo: HPO, orphanet: rb.Orphanet) -> None:
    assert rb.diagnosis(["ORPHA:81"], hpo, orphanet) == ("ORPHA:81", [], "Antisynthetase syndrome")


def test_load_reads_every_set_with_current_terms(
    tmp_path: Path, hpo: HPO, orphanet: rb.Orphanet
) -> None:
    archive = tmp_path / rb.ARCHIVE
    hms = [
        # an alternative id, an obsolete term, an id the release does not know, a repeat
        {
            "Phenotype": ["HP:0001730", "HP:0099999", "HP:9999999", "HP:0000365"],
            "RareDisease": ["OMIM:690001", "ORPHA:3"],
            "Department": None,
        },
        {"Phenotype": ["HP:9999999"], "RareDisease": ["OMIM:690001"], "Department": None},
    ]
    ramedis = [{"Phenotype": ["HP:0001250"], "RareDisease": ["ORPHA:3"], "Department": None}]
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr("data/HMS.jsonl", "\n".join(json.dumps(p) for p in hms) + "\n")
        z.writestr("data/RAMEDIS.jsonl", json.dumps(ramedis[0]) + "\n")
        z.writestr("data/MME.jsonl", "")
        z.writestr("data/LIRICAL.jsonl", "")
    cases, dropped = rb.load(archive, hpo, orphanet)
    first, ramedis_case = cases
    assert first.id == "RareBench_HMS_001" and first.cohort == "HMS"
    assert first.hpo_ids == ["HP:0000365", "HP:0000407"]
    assert first.hpo_labels == ["Hearing impairment", "Sensorineural hearing impairment"]
    assert (first.disease_id, first.also_accepted) == ("OMIM:690001", ["OMIM:690003"])
    assert first.pmid is None and first.sex is None and first.gene is None
    assert first.split == "external"
    assert ramedis_case.id == "RareBench_RAMEDIS_001" and ramedis_case.disease_id == "OMIM:690003"
    assert dropped == {"unknown_term": 2, "no_phenotype": 1}
