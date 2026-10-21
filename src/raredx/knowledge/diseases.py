"""Disease identity: which OMIM and Orphanet ids name the same disease.

OMIM and Orphanet are two catalogues of rare diseases, each with its own ids, and
HPO annotates diseases under both. Behçet disease is OMIM:109650 there, with 15
features, and ORPHA:117, with 85. Mondo (the Monarch Disease Ontology) is the
standard bridge between such catalogues: each of its classes lists the ids of other
catalogues it matches exactly (skos:exactMatch in its SSSOM mapping file). Two ids
matched exactly to the same Mondo class name the same disease.

Orphanet's own mapping to OMIM is narrower: it maps systemic lupus erythematosus
(ORPHA:536) only to two OMIM susceptibility loci, not to OMIM:152700; Mondo matches
ORPHA:536 and OMIM:152700 to one class. Only exact matches are read: a broader or
narrower match is a different disease.
"""

from collections import defaultdict
from pathlib import Path

MAPPINGS = "mondo.sssom.tsv"
EXACT = "skos:exactMatch"
PREFIXES = {"OMIM": "OMIM", "Orphanet": "ORPHA"}  # Mondo's prefix -> the one used here


class Identity:
    """Mondo's exact matches between OMIM and Orphanet ids."""

    def __init__(self, path: Path) -> None:
        self._mondo: dict[str, str] = {}  # OMIM or ORPHA id -> its Mondo class
        members: dict[str, set[str]] = defaultdict(set)
        with path.open(encoding="utf-8") as f:
            for line in f:
                if line.startswith("#") or line.startswith("subject_id"):
                    continue
                subject, _, predicate, target = line.split("\t", 4)[:4]
                prefix, _, local = target.partition(":")
                if predicate != EXACT or prefix not in PREFIXES:
                    continue
                disease = f"{PREFIXES[prefix]}:{local}"
                self._mondo[disease] = subject
                members[subject].add(disease)
        self._members = {m: frozenset(ids) for m, ids in members.items()}

    def mondo(self, disease: str) -> str | None:
        """The Mondo class an OMIM or ORPHA id matches exactly, if any."""
        return self._mondo.get(disease)

    def same(self, disease: str) -> frozenset[str]:
        """Every OMIM and ORPHA id naming the same disease, itself included."""
        mondo = self._mondo.get(disease)
        return self._members[mondo] if mondo else frozenset({disease})
