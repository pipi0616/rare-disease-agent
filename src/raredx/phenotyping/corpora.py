"""Public texts annotated with HPO terms by hand: the yardstick for reading a note.

    ID-68        68 clinical notes on families with intellectual disability (Anazi et
                 al., Mol Psychiatry 2017), annotated by PhenoBERT's authors (Feng et
                 al., Brief Bioinform 2022). A mention the note denies is marked
                 negated; one coded with a near term, related. The test set.
    GeneReviews  10 GeneReviews summaries annotated the same way. For development.
    GSC-2024     228 PubMed abstracts on rare diseases (GSC+, Lobo et al. 2017),
                 annotated again against HPO 2024 by Groza et al. (2024). The 22
                 abstracts PhenoTagger set aside for development are ours too; the
                 other 206 are the test set, as in the papers we compare with.

Both are read straight from the archives as downloaded (`raredx data fetch`):
nothing is unpacked, and nothing in them is run. Neither is in git.
"""

import re
import tarfile
import zipfile
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

Kind = Literal["plain", "negated", "related"]
Corpus = Literal["id-68", "genereviews", "gsc-2024-dev", "gsc-2024-test"]
CORPORA: tuple[Corpus, ...] = ("id-68", "genereviews", "gsc-2024-dev", "gsc-2024-test")

# PhenoTagger's development abstracts (its data/corpus/GSC/GSCplus_dev_gold.tsv).
GSC_DEV = frozenset(
    [
        "11312426",
        "11338037",
        "11425952",
        "12900905",
        "14699618",
        "1750770",
        "1789288",
        "18177466",
        "2729353",
        "3799714",
        "3943073",
        "6823972",
        "6829601",
        "712760",
        "7417945",
        "7485365",
        "7802001",
        "7905534",
        "8145850",
        "8352281",
        "8808282",
        "9236523",
    ]
)


class Annotation(BaseModel):
    start: int
    end: int
    text: str
    hpo_id: str  # as the annotators coded it, against the release they used
    kind: Kind = "plain"


class Document(BaseModel):
    id: str
    text: str
    gold: list[Annotation]


_PHENOBERT_KIND: dict[str, Kind] = {"Neg": "negated", "Related": "related"}
_GSC_LINE = re.compile(r"(\d+):(\d+)\t(HP:\d{7})\t(.*)")


def phenobert(archive: Path, folder: Literal["ID-68", "GeneReviews"]) -> list[Document]:
    """One of PhenoBERT's corpora, from its repository's archive: per document, a text
    file under corpus/ and its annotations under ann/, one per line —
    start, end, text, HPO id, and Neg or Related where it applies."""
    documents = []
    with zipfile.ZipFile(archive) as z:
        names = z.namelist()
        corpus = sorted(n for n in names if f"/data/{folder}/corpus/" in n and not n.endswith("/"))
        for name in corpus:
            doc_id = name.rsplit("/", 1)[1]
            text = z.read(name).decode("utf-8")
            gold = []
            for line in z.read(name.replace("/corpus/", "/ann/")).decode("utf-8").splitlines():
                cells = line.rstrip("\n").split("\t")
                if len(cells) < 4:
                    continue
                kind = _PHENOBERT_KIND.get(cells[4].strip(), "plain") if len(cells) > 4 else "plain"
                gold.append(Annotation(start=int(cells[0]), end=int(cells[1]), text=cells[2],
                                       hpo_id=cells[3].strip(), kind=kind))  # fmt: skip
            documents.append(Document(id=doc_id, text=text, gold=gold))
    return documents


def gsc2024(tarball: Path) -> list[Document]:
    """GSC-2024: under GSC_2024/, per abstract a file in Text/ and one in Annotations/,
    one annotation per line — start:end, HPO id, text."""
    texts: dict[str, str] = {}
    annotations: dict[str, str] = {}
    with tarfile.open(tarball, "r:gz") as tar:
        for member in tar.getmembers():
            parts = member.name.split("/")
            if not member.isfile() or len(parts) < 3 or parts[-1].startswith("."):
                continue
            content = tar.extractfile(member)
            if content is None:
                continue
            target = {"Text": texts, "Annotations": annotations}.get(parts[-2])
            if target is not None:
                target[parts[-1]] = content.read().decode("utf-8")
    documents = []
    for doc_id in sorted(texts):
        gold = [
            Annotation(start=int(m[1]), end=int(m[2]), hpo_id=m[3], text=m[4].strip())
            for line in annotations.get(doc_id, "").splitlines()
            if (m := _GSC_LINE.match(line))
        ]
        documents.append(Document(id=doc_id, text=texts[doc_id], gold=gold))
    return documents


def load(corpus: Corpus, phenobert_archive: Path, gsc_tarball: Path) -> list[Document]:
    """The documents of one corpus, or of one part of GSC-2024."""
    if corpus == "id-68":
        return phenobert(phenobert_archive, "ID-68")
    if corpus == "genereviews":
        return phenobert(phenobert_archive, "GeneReviews")
    documents = gsc2024(gsc_tarball)
    dev = corpus == "gsc-2024-dev"
    return [d for d in documents if (d.id in GSC_DEV) == dev]
