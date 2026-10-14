"""The annotated corpora, read from archives built like the real downloads."""

import io
import tarfile
import zipfile
from pathlib import Path

from raredx.phenotyping import corpora


def phenobert_archive(path: Path) -> Path:
    root = "PhenoBERT-195d5df/phenobert/data"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(f"{root}/ID-68/corpus/N1", "Floppy baby. No tears. Seizures.")
        # The last line has no newline, as in the real files.
        z.writestr(
            f"{root}/ID-68/ann/N1",
            "0\t6\tFloppy\tHP:0001252\n16\t21\ttears\tHP:0009926\tNeg\n23\t31\tSeizures\tHP:0001250",
        )
        z.writestr(f"{root}/GeneReviews/corpus/NBK1", "Hearing loss.")
        z.writestr(f"{root}/GeneReviews/ann/NBK1", "0\t12\tHearing loss\tHP:0000365\tRelated\n")
    return path


def gsc_tarball(path: Path) -> Path:
    files = {
        "GSC_2024/Text/11312426": "Nevoid basal cell carcinoma syndrome.",
        "GSC_2024/Annotations/11312426": "0:6\tHP:0003764\tNevoid\n",
        "GSC_2024/Text/999": "Seizures.",
        "GSC_2024/Annotations/999": "0:8\tHP:0001250\tSeizures",
        "GSC_2024/.DS_Store": "junk",
    }
    with tarfile.open(path, "w:gz") as tar:
        for name, content in files.items():
            data = content.encode()
            info = tarfile.TarInfo(name)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    return path


def test_id68_reads_each_note_with_its_annotations_and_their_kinds(tmp_path: Path) -> None:
    [note] = corpora.phenobert(phenobert_archive(tmp_path / "a.zip"), "ID-68")
    assert note.id == "N1" and note.text.startswith("Floppy")
    assert [(a.hpo_id, a.kind) for a in note.gold] == [
        ("HP:0001252", "plain"),
        ("HP:0009926", "negated"),
        ("HP:0001250", "plain"),
    ]
    assert note.text[note.gold[2].start : note.gold[2].end] == "Seizures"


def test_genereviews_is_read_from_the_same_archive(tmp_path: Path) -> None:
    [summary] = corpora.phenobert(phenobert_archive(tmp_path / "a.zip"), "GeneReviews")
    assert summary.gold[0].kind == "related"


def test_gsc_is_split_as_phenotagger_split_it(tmp_path: Path) -> None:
    archive, tarball = phenobert_archive(tmp_path / "a.zip"), gsc_tarball(tmp_path / "g.tar.gz")
    [dev] = corpora.load("gsc-2024-dev", archive, tarball)
    [test] = corpora.load("gsc-2024-test", archive, tarball)
    assert dev.id == "11312426" and dev.gold[0].hpo_id == "HP:0003764"
    assert test.id == "999" and test.gold[0].text == "Seizures"
