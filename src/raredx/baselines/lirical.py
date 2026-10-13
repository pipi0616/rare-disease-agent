"""LIRICAL, an established phenotype-driven diagnosis tool, as a system under evaluation.

LIRICAL (Robinson et al., Am J Hum Genet 2020) scores every disease by likelihood
ratios: for each of the patient's findings, how much more often the disease
shows it than diseases in general; their product gives a post-test probability.
It comes from the group that curates HPO, is maintained, and is a different
method from the semantic similarity of tool T2. It is run here in its
phenotype-only mode, with its default settings.

It is an external program — the release as published, a Java command-line tool
fetched through the registry and never kept in git — started once per case.
What makes the comparison fair is what it is given:

- the same question as every system: the observed findings and the sex. No
  negated findings (no system gets them: they leak the answer) and no age;
- the same HPO release: the pinned hp.json and phenotype.hpoa;
- the same mask: for each case LIRICAL reads a phenotype.hpoa written under the
  evaluation's mask (HPO.write_annotations) — no line resting only on the
  case's paper, no disease known only from it. Unmasked, it reads the file as
  published, which is how a benchmark usually runs it;
- the same answer space: only its OMIM diseases count (it also scores a few
  DECIPHER entries, which no case here has).

`setup` prepares a folder once: the release unpacked, the gene and transcript
data LIRICAL downloads for itself, and the pinned ontology. LIRICAL checks that
gene and transcript files exist even in phenotype-only mode; they do not enter
its phenotype ranking (the same ranking came out with a gene file cut to 200
rows). One repair is needed for it to start at all: see drop_repeated_genes.
"""

import csv
import glob
import json
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import Any

import mlflow
from mlflow.entities import SpanType

from raredx.data.sources import sha256_of
from raredx.evals.systems import Candidate, Question
from raredx.knowledge import masking
from raredx.knowledge.hpo import ANNOTATIONS, HPO

RESOURCES = "resources"
BUILD = "build.json"
GENES = "hgnc_complete_set.txt"
ONTOLOGY = "hp.json"
READ = 50  # ranked diseases kept from each run: what is traced, and audited
K = 10
TIMEOUT_SECONDS = 600
# For a run of a few seconds: less compiling, one collector thread. Half the CPU time,
# the same output — what lets several cases run side by side.
JVM = ("-XX:TieredStopAtLevel=1", "-XX:+UseSerialGC")


class JavaNotFound(Exception):
    pass


class LiricalNotSetUp(Exception):
    pass


def find_java(configured: str | None) -> str:
    """A `java` that runs: the configured one, or the one on PATH, or a Homebrew
    OpenJDK (macOS has a `java` on PATH that only says none is installed)."""
    found = [shutil.which("java"), *sorted(glob.glob("/opt/homebrew/opt/openjdk*/bin/java"))]
    for java in [configured] if configured else found:
        try:
            if java and subprocess.run([java, "-version"], capture_output=True).returncode == 0:
                return java
        except OSError:  # no such file, or not a program
            continue
    raise JavaNotFound(
        "LIRICAL needs Java 17 or later: install one (brew install openjdk@17), "
        "or set RAREDX_JAVA to its `java`"
    )


def drop_repeated_genes(path: Path) -> int:
    """Rewrite HGNC's gene table without the rows whose Ensembl id an earlier row
    already has; returns how many were dropped.

    LIRICAL 2.4.1 stops at start-up ("Duplicate key") when two genes share an Ensembl
    id, and HGNC's current table has three such pairs (non-coding RNAs and
    pseudogenes). Gene data does not enter the phenotype-only ranking."""
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    column = lines[0].rstrip("\r\n").split("\t").index("ensembl_gene_id")
    seen: set[str] = set()
    kept = [lines[0]]
    for line in lines[1:]:
        cells = line.rstrip("\r\n").split("\t")
        ensembl = cells[column] if len(cells) > column else ""
        if ensembl and ensembl in seen:
            continue
        seen.add(ensembl)
        kept.append(line)
    path.write_text("".join(kept), encoding="utf-8")
    return len(lines) - len(kept)


def _jar(folder: Path) -> Path:
    jars = sorted(folder.glob("lirical-cli-*/lirical-cli-*.jar"))
    if not jars or not (folder / BUILD).exists():
        raise LiricalNotSetUp(
            f"{folder} has no LIRICAL set up — run `raredx data fetch lirical hpo-json`, "
            "then `raredx data lirical`"
        )
    return jars[0]


def setup(distribution: Path, ontology: Path, folder: Path, java: str) -> dict[str, Any]:
    """Prepare `folder` for runs: unpack the release, let LIRICAL download its gene and
    transcript data, replace its ontology with the pinned one, and repair the gene
    table. Its own phenotype.hpoa is removed: each case gets one, written under the
    mask. Returns what was built, also written to build.json."""
    folder.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(distribution) as z:
        z.extractall(folder)
    jar = sorted(folder.glob("lirical-cli-*/lirical-cli-*.jar"))[0]
    resources = folder / RESOURCES
    subprocess.run([java, "-jar", str(jar), "download", "-d", str(resources)], check=True)
    (resources / ANNOTATIONS).unlink(missing_ok=True)
    shutil.copyfile(ontology, resources / ONTOLOGY)
    info = {
        "lirical": jar.stem.removeprefix("lirical-cli-"),
        "gene_rows_dropped": drop_repeated_genes(resources / GENES),
        "files": {p.name: sha256_of(p) for p in sorted(resources.iterdir())},
    }
    (folder / BUILD).write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")
    return info


class Lirical:
    name = "lirical"

    def __init__(self, hpo: HPO, folder: Path, java: str) -> None:
        """`folder`: what `setup` prepared."""
        self.hpo = hpo
        self.java = java
        self.jar = _jar(folder)
        self.resources = folder / RESOURCES
        self.info: dict[str, Any] = json.loads((folder / BUILD).read_text(encoding="utf-8"))

    def params(self) -> dict[str, str]:
        return {
            "lirical": self.info["lirical"],
            "mode": "phenotype only, default settings",
            "hpo_release": self.hpo.release,
            "annotations": "the pinned phenotype.hpoa, written under the mask for each case",
            "findings": "observed only, cleaned as for the phenotype tools",
            "diseases": "OMIM",
            "gene_rows_dropped": str(self.info["gene_rows_dropped"]),
        }

    @mlflow.trace(name="lirical", span_type=SpanType.TOOL)
    def ranked(self, hpo_ids: list[str], sex: str | None) -> list[dict[str, str]]:
        """LIRICAL's OMIM diseases for these findings, best first, at most READ: what
        the answer is taken from, and what the leak audit reads."""
        patient, _ = self.hpo.patient(hpo_ids)  # obsolete ids replaced, modifiers dropped
        terms = sorted(str(term.id) for term in patient)
        if not terms:
            return []
        masked = masking.current()
        with tempfile.TemporaryDirectory(prefix="lirical-") as tmp:
            data, out = Path(tmp) / "data", Path(tmp) / "out"
            data.mkdir()
            for resource in self.resources.iterdir():
                (data / resource.name).symlink_to(resource.resolve())
            self.hpo.write_annotations(data / ANNOTATIONS, masked)
            command = [self.java, *JVM, "-jar", str(self.jar), "prioritize"]
            command += ["--observed-phenotypes", ",".join(terms)]
            command += ["--sex", sex if sex in ("MALE", "FEMALE") else "UNKNOWN"]
            command += ["--data", str(data), "--output-directory", str(out)]
            command += ["--prefix", "case", "--output-format", "tsv"]
            done = subprocess.run(command, capture_output=True, text=True, timeout=TIMEOUT_SECONDS)
            table = out / "case.tsv"
            if done.returncode != 0 or not table.exists():
                raise RuntimeError(f"LIRICAL failed: {(done.stderr or done.stdout)[-500:]}")
            with table.open(encoding="utf-8", newline="") as f:
                rows = list(
                    csv.DictReader((line for line in f if not line.startswith("!")), delimiter="\t")
                )
        return [
            {
                "disease_id": row["diseaseCurie"],
                "disease_name": row["diseaseName"],
                "posttest_probability": row["posttestprob"],
                "composite_lr": row["compositeLR"],
            }
            for row in rows
            if row["diseaseCurie"].startswith("OMIM:")
        ][:READ]

    def predict(self, question: Question) -> list[Candidate]:
        candidates = []
        for row in self.ranked(question.hpo_ids, question.sex)[:K]:
            genes = self.hpo.genes.get(row["disease_id"], ())
            candidates.append(
                Candidate(
                    disease_name=row["disease_name"],
                    disease_id=row["disease_id"],
                    gene=genes[0] if len(genes) == 1 else None,
                )
            )
        return candidates
