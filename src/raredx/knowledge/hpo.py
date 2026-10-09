"""The Human Phenotype Ontology release the phenotype tools read.

Two of its files carry the knowledge:

    hp.obo           the ontology: about 20,000 terms, and which is a more specific
                     form of which ("Sensorineural hearing impairment" is a kind
                     of "Hearing impairment")
    phenotype.hpoa   the disease annotations: which terms each disease shows, how
                     often, its inheritance and onset — every line citing the
                     source it was curated from

hpo3 (MIT licensed; a Rust implementation of PyHPO) parses the release as
published and computes term similarity; it also reads genes_to_phenotype.txt.
The disease annotations are read here from phenotype.hpoa rather than taken
from hpo3, for two reasons: each line keeps its references, so the source of a
test case can be masked (raredx.knowledge.masking); and a line whose frequency
is 0/n — looked for, absent in every patient — says the disease lacks the
feature, where hpo3 would count it as present. Genes come from
genes_to_disease.txt: each disease's Mendelian genes.

hpo3 holds one ontology per process, so load() refuses to put a second release
next to the first.
"""

import csv
import re
from collections import defaultdict
from collections.abc import Iterator
from pathlib import Path
from typing import Any, Literal, NamedTuple

from pyhpo import BasicHPOSet, Ontology

ANNOTATIONS = "phenotype.hpoa"
GENES = "genes_to_disease.txt"

Relation = Literal["same", "more specific", "less specific"]


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


# ── frequencies ─────────────────────────────────────────────────────
#
# phenotype.hpoa writes how often a feature occurs in four ways: counts (3/5),
# a percentage (25%), one of HPO's frequency terms, or nothing at all.

FREQUENCY_TERMS = {  # each term's range, and the middle of it as a fraction of patients
    "HP:0040280": (1.0, "obligate (100%)"),
    "HP:0040281": (0.895, "very frequent (80–99%)"),
    "HP:0040282": (0.545, "frequent (30–79%)"),
    "HP:0040283": (0.17, "occasional (5–29%)"),
    "HP:0040284": (0.025, "very rare (1–4%)"),
    "HP:0040285": (0.0, "excluded (0%)"),
}
_COUNT = re.compile(r"(\d+)/(\d+)")
_PERCENT = re.compile(r"(\d+(?:\.\d+)?)%")


class Frequency(NamedTuple):
    fraction: float | None  # share of patients with the feature; None when no source says
    text: str | None  # for a reader: "4/8", "frequent (30–79%)", "25%"


def absent(frequency: str) -> bool:
    """A frequency of 0/n, 0% or 'Excluded': looked for and not found."""
    return bool(re.fullmatch(r"0/\d+|0(\.0+)?%|HP:0040285", frequency.strip()))


def frequency(written: list[str]) -> Frequency:
    """One feature's frequency, from every line that annotates it.

    Counts are pooled across sources when some source counted patients who had
    it (2/2 and 0/3 make 2/5). Otherwise percentages and frequency terms are
    used, averaged if there are several. When every source looked and found
    none, the frequency is zero (0/5). Otherwise it is unknown.
    """
    counts = [(int(m[1]), int(m[2])) for w in written if (m := _COUNT.fullmatch(w.strip()))]
    counts = [(n, of) for n, of in counts if of > 0]
    if any(n for n, _ in counts):
        n, of = sum(c[0] for c in counts), sum(c[1] for c in counts)
        return Frequency(n / of, f"{n}/{of}")
    others: list[tuple[float, str]] = []
    for w in (w.strip() for w in written):
        if m := _PERCENT.fullmatch(w):
            others.append((float(m[1]) / 100, f"{float(m[1]):g}%"))
        elif w in FREQUENCY_TERMS:
            others.append(FREQUENCY_TERMS[w])
    present = [o for o in others if o[0] > 0]
    if len(present) == 1:
        return Frequency(*present[0])
    if present:
        mean = sum(f for f, _ in present) / len(present)
        return Frequency(mean, f"about {mean:.0%}")
    if written and all(absent(w) for w in written):
        if counts:
            return Frequency(0.0, f"0/{sum(of for _, of in counts)}")
        return Frequency(0.0, others[0][1] if others else written[0].strip())
    return Frequency(None, None)


# ── reading the annotation files ────────────────────────────────────


class Line(NamedTuple):
    """One annotation line of phenotype.hpoa."""

    aspect: str  # P phenotype, I inheritance, C onset and course, M modifier
    term: str
    refs: frozenset[str]  # the sources it was curated from
    frequency: str  # as written


class Feature(NamedTuple):
    """One phenotypic feature of a disease, gathered from every line about it."""

    term: str  # as it stands in this release (an obsolete term's replacement)
    label: str
    information: float  # information content across OMIM diseases: rarer is higher
    frequency: Frequency
    sources: frozenset[str]
    absent: bool  # every source looked for it and found none


def _rows(path: Path) -> Iterator[dict[str, str]]:
    with path.open(newline="") as f:
        yield from csv.DictReader((line for line in f if not line.startswith("#")), delimiter="\t")


def _annotations(path: Path) -> tuple[dict[str, list[Line]], dict[str, str]]:
    lines: dict[str, list[Line]] = defaultdict(list)
    names: dict[str, str] = {}
    for row in _rows(path):
        disease = row["database_id"]
        if not disease.startswith("OMIM:"):
            continue
        names[disease] = row["disease_name"]
        if row["qualifier"] == "NOT":
            continue
        refs = frozenset(r.strip() for r in row["reference"].split(";") if r.strip())
        lines[disease].append(Line(row["aspect"], row["hpo_id"], refs, row["frequency"].strip()))
    return lines, names


def _genes(path: Path) -> dict[str, tuple[str, ...]]:
    genes: dict[str, set[str]] = defaultdict(set)
    for row in _rows(path):
        if row["disease_id"].startswith("OMIM:") and row["association_type"] == "MENDELIAN":
            genes[row["disease_id"]].add(row["gene_symbol"])
    return {disease: tuple(sorted(symbols)) for disease, symbols in genes.items()}


# ── the release in memory ───────────────────────────────────────────


class HPO:
    """One HPO release: every OMIM disease's annotations, name and genes."""

    def __init__(self, folder: Path, release: str) -> None:
        self.release = release
        self._lines, self.names = _annotations(folder / ANNOTATIONS)
        self.genes = _genes(folder / GENES)
        # Each gene's diseases, those with phenotype annotations only: the others have no
        # name or profile here, so nothing can be said or scored about them.
        diseases_of_gene: dict[str, list[str]] = defaultdict(list)
        for disease, symbols in sorted(self.genes.items()):
            if disease not in self.names:
                continue
            for symbol in symbols:
                diseases_of_gene[symbol].append(disease)
        self.diseases_of_gene = {g: tuple(ds) for g, ds in diseases_of_gene.items()}
        self.disease_ids = sorted(self.names)
        self._index = {d: i for i, d in enumerate(self.disease_ids)}
        self._profiles = [self._profile(d) for d in self.disease_ids]
        self._citing: dict[str, set[str]] = defaultdict(set)  # reference -> diseases
        for disease, lines in self._lines.items():
            for line in lines:
                for ref in line.refs:
                    self._citing[ref].add(disease)

    def __repr__(self) -> str:  # how the release appears in a trace
        return f"HPO({self.release}, {len(self.disease_ids)} OMIM diseases)"

    def lines(self, disease: str, aspect: str, masked: frozenset[str] = frozenset()) -> list[Line]:
        """The disease's annotation lines of one aspect, without those resting only on
        masked sources. A line citing a masked source and an unmasked one stays."""
        return [
            line
            for line in self._lines.get(disease, [])
            if line.aspect == aspect and (not line.refs or line.refs - masked)
        ]

    def _profile(self, disease: str, masked: frozenset[str] = frozenset()) -> Any:
        """The disease's phenotype as an hpo3 set: the features some source saw."""
        lines = self.lines(disease, "P", masked)
        return BasicHPOSet.from_queries(sorted({x.term for x in lines if not absent(x.frequency)}))

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
        return {ref for line in self._lines.get(disease, []) for ref in line.refs}

    def known_only_from(self, masked: frozenset[str]) -> set[str]:
        """Diseases citing a masked source with no observed feature left once it is
        masked: what HPO knows of them comes from the masked papers alone. Any other
        description of such a disease likely rests on the same papers."""
        affected: set[str] = set()
        for ref in masked:
            affected |= self._citing.get(ref, set())
        return {
            disease
            for disease in affected
            if not any(not absent(line.frequency) for line in self.lines(disease, "P", masked))
        }

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

    def term(self, hpo_id: str) -> tuple[str, str, float]:
        """A term as it stands in this release: its id (an obsolete term's replacement),
        its name, and its information content across OMIM diseases."""
        term = Ontology.get_hpo_object(hpo_id)
        if term.is_obsolete and term.replaced_by:
            term = Ontology.get_hpo_object(term.replaced_by)
        return str(term.id), str(term.name), float(term.information_content["omim"])

    def features(self, disease: str, masked: frozenset[str] = frozenset()) -> list[Feature]:
        """The disease's phenotypic features, each gathered from all its lines: those
        some source saw, and those every source looked for and found absent. A feature
        kept because another source also reports it does not list the masked one."""
        written: dict[str, list[str]] = {}
        cited: dict[str, set[str]] = {}
        for line in self.lines(disease, "P", masked):
            term = self.term(line.term)[0]
            written.setdefault(term, []).append(line.frequency)
            cited.setdefault(term, set()).update(line.refs - masked)  # never list a masked paper
        features = []
        for term, frequencies in written.items():
            _, label, information = self.term(term)
            features.append(
                Feature(
                    term=term,
                    label=label,
                    information=information,
                    frequency=frequency(frequencies),
                    sources=frozenset(cited[term]),
                    absent=all(absent(w) for w in frequencies),
                )
            )
        return features

    def relation(self, finding: str, feature: str) -> Relation | None:
        """How a patient's finding stands to a disease's feature in the ontology:
        "same"; "more specific" when the finding is a kind of the feature
        (Bilateral sensorineural hearing impairment, of Hearing impairment);
        "less specific" the other way round; None when neither is a kind of the other."""
        if finding == feature:
            return "same"
        a, b = Ontology.get_hpo_object(finding), Ontology.get_hpo_object(feature)
        if a.child_of(b):
            return "more specific"
        if a.parent_of(b):
            return "less specific"
        return None
