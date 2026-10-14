"""LIRICAL as a system, with a stand-in for the Java program: no Java, no download.

The stand-in ranks the diseases of the phenotype.hpoa it is handed by how many of the
observed findings each is annotated with (ties in id order) — enough to see what the
wrapper gives it (the findings, the sex, the annotations under the mask) and what it
takes back.
"""

import json
import zipfile
from pathlib import Path

import pytest

from raredx.baselines import lirical
from raredx.baselines.lirical import JavaNotFound, Lirical, LiricalNotSetUp
from raredx.evals.systems import Question
from raredx.knowledge import masking
from raredx.knowledge.hpo import HPO

SNHL, AMENORRHEA = "HP:0000407", "HP:0000786"

STAND_IN = """#!/usr/bin/env python3
import json, sys
from pathlib import Path
args = sys.argv[1:]
if args == ["-version"]:
    sys.exit(0)
def value(flag):
    return args[args.index(flag) + 1]
with Path(__file__).with_name("calls.jsonl").open("a") as f:
    f.write(json.dumps(args) + "\\n")
if "download" in args:
    data = Path(value("-d"))
    data.mkdir(parents=True)
    (data / "hp.json").write_text("the latest ontology")
    (data / "phenotype.hpoa").write_text("the latest annotations")
    (data / "hg38_refseq.ser").write_text("transcripts")
    (data / "hgnc_complete_set.txt").write_text(
        "hgnc_id\\tsymbol\\tensembl_gene_id\\n"
        "HGNC:1\\tA\\tENSG1\\nHGNC:2\\tB\\tENSG1\\nHGNC:3\\tC\\t\\nHGNC:4\\tD\\t\\n"
    )
elif "prioritize" in args:
    observed = value("--observed-phenotypes").split(",")
    if "HP:0001250" in observed:
        sys.exit("something went wrong inside")
    found = {}
    for line in (Path(value("--data")) / "phenotype.hpoa").read_text().splitlines():
        cells = line.split("\\t")
        if line.startswith("#") or cells[0] == "database_id":
            continue
        name, terms = found.get(cells[0], (cells[1], set()))
        if cells[3] in observed and cells[2] != "NOT":
            terms.add(cells[3])
        found[cells[0]] = (name, terms)
    rows = sorted(found.items(), key=lambda kv: (-len(kv[1][1]), kv[0]))
    out = Path(value("--output-directory"))
    out.mkdir(parents=True)
    lines = ["! LIRICAL TSV Output (stand-in)", "! Sample: subject"]
    lines.append("rank\\tdiseaseName\\tdiseaseCurie\\tpretestprob\\tposttestprob\\tcompositeLR")
    for i, (disease, (name, terms)) in enumerate(rows, 1):
        lines.append(f"{i}\\t{name}\\t{disease}\\t1/6\\t{len(terms)}0%\\t{len(terms)}.5")
    (out / (value("--prefix") + ".tsv")).write_text("\\n".join(lines) + "\\n")
"""


@pytest.fixture
def java(tmp_path: Path) -> str:
    """The stand-in, as an executable. It notes each call beside itself (calls.jsonl)."""
    program = tmp_path / "bin" / "java"
    program.parent.mkdir()
    program.write_text(STAND_IN, encoding="utf-8")
    program.chmod(0o755)
    return str(program)


@pytest.fixture
def folder(tmp_path: Path, java: str) -> Path:
    """A folder set up as `raredx data lirical` sets it up."""
    distribution = tmp_path / "lirical-cli-9.9-distribution.zip"
    with zipfile.ZipFile(distribution, "w") as z:
        z.writestr("lirical-cli-9.9/lirical-cli-9.9.jar", "")
    ontology = tmp_path / "hp.json"
    ontology.write_text("the pinned ontology", encoding="utf-8")
    out = tmp_path / "lirical"
    lirical.setup(distribution, ontology, out, java)
    return out


def calls(java: str) -> list[list[str]]:
    noted = Path(java).with_name("calls.jsonl").read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in noted]


def question(*hpo_ids: str, sex: str | None = None) -> Question:
    return Question(case_id="1", hpo_ids=list(hpo_ids), hpo_labels=list(hpo_ids), sex=sex)


def test_setup_unpacks_downloads_and_puts_the_pinned_release_in(folder: Path) -> None:
    resources = folder / "resources"
    assert (folder / "lirical-cli-9.9" / "lirical-cli-9.9.jar").exists()
    assert (resources / "hp.json").read_text(encoding="utf-8") == "the pinned ontology"
    assert not (resources / "phenotype.hpoa").exists()  # each case gets its own
    # the gene row repeating an Ensembl id is gone; rows without one all stay
    genes = (resources / "hgnc_complete_set.txt").read_text(encoding="utf-8").splitlines()
    assert [g.split("\t")[0] for g in genes[1:]] == ["HGNC:1", "HGNC:3", "HGNC:4"]
    info = json.loads((folder / "build.json").read_text(encoding="utf-8"))
    assert (info["lirical"], info["gene_rows_dropped"]) == ("9.9", 1)
    assert set(info["files"]) == {"hp.json", "hg38_refseq.ser", "hgnc_complete_set.txt"}
    assert all(len(sha) == 64 for sha in info["files"].values())


def test_it_answers_with_liricals_omim_diseases_in_its_order(
    hpo: HPO, folder: Path, java: str
) -> None:
    system = Lirical(hpo, folder, java)
    answers = system.predict(question(SNHL, AMENORRHEA, sex="FEMALE"))
    ids = [c.disease_id for c in answers]
    assert ids[0] == "OMIM:690001"  # annotated with both findings
    assert all(i is not None and i.startswith("OMIM:") for i in ids)  # the ORPHA entry is left out
    assert "OMIM:690004" in ids
    by_id = {c.disease_id: c for c in answers}
    assert by_id["OMIM:690001"].gene == "GENEA"  # its one gene, from HPO
    assert by_id["OMIM:690002"].gene is None  # two genes: none named
    [call] = [c for c in calls(java) if "prioritize" in c]
    assert call[: len(lirical.JVM)] == list(lirical.JVM)
    assert call[call.index("--observed-phenotypes") + 1] == f"{SNHL},{AMENORRHEA}"
    assert call[call.index("--sex") + 1] == "FEMALE"
    assert system.params()["lirical"] == "9.9"


def test_under_the_mask_it_reads_annotations_without_the_masked_paper(
    hpo: HPO, folder: Path, java: str
) -> None:
    system = Lirical(hpo, folder, java)
    patient = question(AMENORRHEA)
    with masking.masked(["PMID:1004"]):  # the only source of OMIM:690004
        hidden = [row["disease_id"] for row in system.ranked(patient.hpo_ids, None)]
    with masking.masked(["PMID:1001"]):  # the only source of OMIM:690001
        other = [row["disease_id"] for row in system.ranked(patient.hpo_ids, None)]
    shown = [row["disease_id"] for row in system.ranked(patient.hpo_ids, None)]
    assert "OMIM:690004" in shown and "OMIM:690004" not in hidden
    assert "OMIM:690001" in shown and "OMIM:690001" not in other
    assert "OMIM:690004" in other  # a mask hides its own paper's knowledge, no more


def test_it_is_given_the_findings_cleaned_as_the_phenotype_tools_clean_them(
    hpo: HPO, folder: Path, java: str
) -> None:
    system = Lirical(hpo, folder, java)
    # an obsolete id (replaced) and an inheritance term (not a finding: dropped)
    system.predict(question("HP:0099999", "HP:0000007", sex="UNKNOWN_SEX"))
    call = calls(java)[-1]
    assert call[call.index("--observed-phenotypes") + 1] == SNHL
    assert call[call.index("--sex") + 1] == "UNKNOWN"
    before = len(calls(java))
    assert system.predict(question("HP:0000007")) == []  # no finding: nothing to run
    assert len(calls(java)) == before


def test_a_failed_run_fails_the_case_with_what_lirical_said(
    hpo: HPO, folder: Path, java: str
) -> None:
    with pytest.raises(RuntimeError, match="LIRICAL failed: .*something went wrong inside"):
        Lirical(hpo, folder, java).predict(question("HP:0001250"))


def test_a_folder_never_set_up_says_what_to_run(hpo: HPO, tmp_path: Path, java: str) -> None:
    with pytest.raises(LiricalNotSetUp, match="raredx data lirical"):
        Lirical(hpo, tmp_path / "nothing", java)


def test_java_is_the_configured_one_or_reported_missing(java: str, tmp_path: Path) -> None:
    assert lirical.find_java(java) == java
    with pytest.raises(JavaNotFound, match="RAREDX_JAVA"):
        lirical.find_java(str(tmp_path / "no-such-java"))
