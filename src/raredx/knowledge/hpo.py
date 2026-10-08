"""The Human Phenotype Ontology release the phenotype tools read.

Two of its files carry the knowledge:

    hp.obo           the ontology: about 20,000 terms, and which is a more specific
                     form of which ("Sensorineural hearing impairment" is a kind
                     of "Hearing impairment")
    phenotype.hpoa   the disease annotations: which terms each disease shows, every
                     line citing the source it was curated from

hpo3 (MIT licensed; a Rust implementation of PyHPO) parses the release as
published and computes term similarity; it also reads genes_to_phenotype.txt.
The disease profiles are built here from phenotype.hpoa rather than taken from
hpo3, for two reasons: each line keeps its references, so the source of a test
case can be masked (raredx.knowledge.masking); and lines whose frequency is
0/n — looked for, absent in every patient — are left out, where hpo3 would
count them as present. Genes come from genes_to_disease.txt: each disease's
Mendelian genes.

hpo3 holds one ontology per process, so load() refuses to put a second release
next to the first.
"""

import csv
import re
from collections import defaultdict
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from pyhpo import BasicHPOSet, Ontology

ANNOTATIONS = "phenotype.hpoa"
GENES = "genes_to_disease.txt"


class WrongRelease(Exception):
    """This process already holds a different HPO release."""


def release_of(folder: Path) -> str:
    """The release date hp.obo declares, e.g. 2026-09-01."""
    with (folder / "hp.obo").open() as f:
        for line in f:
            if line.startswith("data-version:"):
                return line.split("/")[-1].strip()
            if line.startswith("[Term]"):
                break
    raise ValueError(f"{folder / 'hp.obo'} declares no data-version")


def _loaded_release() -> str | None:
    try:
        return str(Ontology.version())
    except NameError:  # hpo3: nothing loaded yet
        return None


def load(folder: Path) -> "HPO":
    """The release in folder, loaded into this process if it is not already."""
    release = release_of(folder)
    loaded = _loaded_release()
    if loaded is None:
        Ontology(str(folder))
    elif loaded != release:
        raise WrongRelease(f"HPO {loaded} is loaded in this process; cannot also load {release}")
    return HPO(folder, release)


# ── reading the annotation files ────────────────────────────────────


def _rows(path: Path) -> Iterator[dict[str, str]]:
    with path.open(newline="") as f:
        yield from csv.DictReader((line for line in f if not line.startswith("#")), delimiter="\t")


def _absent(frequency: str) -> bool:
    """A frequency of 0/n, 0% or 'Excluded': looked for and not found."""
    return bool(re.fullmatch(r"0/\d+|0(\.0+)?%|HP:0040285", frequency.strip()))


Annotation = tuple[str, frozenset[str]]  # (HPO term, the references it was curated from)


def _annotations(path: Path) -> tuple[dict[str, list[Annotation]], dict[str, str]]:
    lines: dict[str, list[Annotation]] = defaultdict(list)
    names: dict[str, str] = {}
    for row in _rows(path):
        disease = row["database_id"]
        if not disease.startswith("OMIM:") or row["aspect"] != "P":
            continue  # OMIM diseases' phenotypes; not onset, inheritance or modifiers
        names[disease] = row["disease_name"]
        if row["qualifier"] == "NOT" or _absent(row["frequency"]):
            continue
        refs = frozenset(r.strip() for r in row["reference"].split(";") if r.strip())
        lines[disease].append((row["hpo_id"], refs))
    return lines, names


def _genes(path: Path) -> dict[str, tuple[str, ...]]:
    genes: dict[str, set[str]] = defaultdict(set)
    for row in _rows(path):
        if row["disease_id"].startswith("OMIM:") and row["association_type"] == "MENDELIAN":
            genes[row["disease_id"]].add(row["gene_symbol"])
    return {disease: tuple(sorted(symbols)) for disease, symbols in genes.items()}


# ── the release in memory ───────────────────────────────────────────


class HPO:
    """One HPO release: every OMIM disease's phenotype profile, name and genes."""

    def __init__(self, folder: Path, release: str) -> None:
        self.release = release
        self._lines, self.names = _annotations(folder / ANNOTATIONS)
        self.genes = _genes(folder / GENES)
        self.disease_ids = sorted(self.names)
        self._index = {d: i for i, d in enumerate(self.disease_ids)}
        self._profiles = [self._profile(d) for d in self.disease_ids]
        self._citing: dict[str, set[str]] = defaultdict(set)  # reference -> diseases
        for disease, annotations in self._lines.items():
            for _, refs in annotations:
                for ref in refs:
                    self._citing[ref].add(disease)

    def __repr__(self) -> str:  # how the release appears in a trace
        return f"HPO({self.release}, {len(self.disease_ids)} OMIM diseases)"

    def _profile(self, disease: str, masked: frozenset[str] = frozenset()) -> Any:
        """The disease's phenotype as an hpo3 set, without what rests only on masked sources.

        A term stays if any line supporting it cites an unmasked source.
        """
        terms = sorted({t for t, refs in self._lines.get(disease, []) if not refs or refs - masked})
        return BasicHPOSet.from_queries(terms)

    def profiles(self, masked: frozenset[str] = frozenset()) -> list[Any]:
        """Every disease's profile, in disease_ids order. Only diseases citing a masked
        reference are rebuilt."""
        if not masked:
            return self._profiles
        affected: set[str] = set()
        for ref in masked:
            affected |= self._citing.get(ref, set())
        profiles = list(self._profiles)
        for disease in affected:
            profiles[self._index[disease]] = self._profile(disease, masked)
        return profiles

    def references(self, disease: str) -> set[str]:
        """The sources HPO's annotation of the disease was curated from."""
        return {ref for _, refs in self._lines.get(disease, []) for ref in refs}

    def cites(self, disease: str, reference: str) -> bool:
        """Whether HPO's annotation of the disease cites this reference."""
        return disease in self._citing.get(reference, set())

    def patient(self, hpo_ids: list[str]) -> tuple[Any, list[str]]:
        """A patient's terms as an hpo3 set, and the ids this release does not know.

        The set is cleaned the standard way (hpo3's BasicHPOSet): obsolete terms
        replaced, modifiers dropped, and a term dropped when a more specific one
        below it is also present.
        """
        known, unknown = [], []
        for hpo_id in hpo_ids:
            try:
                Ontology.get_hpo_object(hpo_id)
            except RuntimeError:  # hpo3: unknown term
                unknown.append(hpo_id)
            else:
                known.append(hpo_id)
        return BasicHPOSet.from_queries(known), unknown
