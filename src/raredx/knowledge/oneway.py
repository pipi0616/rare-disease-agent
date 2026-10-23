"""One-directional phenotype similarity: how well a disease explains the patient.

hpo3's set similarities average two directions (funSimAvg): each patient finding's best
match among the disease's features, and each disease feature's best match among the
patient's findings. The second direction counts the disease's features the patient does
not have against it, so a disease annotated at length scores lower for a patient with
few findings: on RAMEDIS (median nine findings) merging Orphanet's annotations cost
rank-then-check fifteen points of top-ten recall (chapter 31). Phenomizer's original
form used the first direction only (Köhler et al. 2009); Exomiser's PhenoDigm scorer
moved towards it ("semi-symmetric", 2015); Phen2Disease's ablation found it best
(25.0% top-1, against 21.1% averaged and 1.6% for the second direction alone).

Resnik's similarity of two terms is the information content of their most informative
common ancestor. A finding's best match in a disease is therefore the most informative
of the finding's ancestors (itself included) that is also an ancestor of one of the
disease's features. Each disease's ancestor closure is indexed once, term to diseases;
a query walks each finding's ancestors from the most informative down. Diseases whose
annotation the mask touches are scored apart, from their masked features.
"""

from collections import defaultdict
from typing import Any

import numpy as np

from raredx.knowledge.hpo import HPO


class OneWayResnik:
    """Patient-to-disease Resnik similarity over every disease of a release."""

    def __init__(self, hpo: HPO) -> None:
        self.hpo = hpo
        self._lineages: dict[str, tuple[str, ...]] = {}  # term -> it and its ancestors
        self._ic: dict[str, float] = {}
        diseases_of: dict[str, list[int]] = defaultdict(list)
        for i, profile in enumerate(hpo.profiles()):
            for term in self._closure(profile):
                diseases_of[term].append(i)
        self._diseases_of = {t: np.array(ix, dtype=np.int64) for t, ix in diseases_of.items()}

    def _lineage(self, term: Any) -> tuple[str, ...]:
        """The term and its ancestors, the most informative first."""
        key = str(term.id)
        if key not in self._lineages:
            lineage = sorted(
                [term, *term.all_parents], key=lambda t: -float(t.information_content["omim"])
            )
            for t in lineage:
                self._ic.setdefault(str(t.id), float(t.information_content["omim"]))
            self._lineages[key] = tuple(str(t.id) for t in lineage)
        return self._lineages[key]

    def _closure(self, profile: Any) -> set[str]:
        return {ancestor for term in profile for ancestor in self._lineage(term)}

    def _best(self, lineage: tuple[str, ...], closure: set[str]) -> float:
        return next((self._ic[a] for a in lineage if a in closure), 0.0)

    def scores(self, patient: Any, masked: frozenset[str] = frozenset()) -> np.ndarray:
        """Each disease's score, in the order of hpo.disease_ids: the mean, over the
        patient's findings, of each finding's best Resnik match in the disease."""
        n = len(self.hpo.disease_ids)
        lineages = [self._lineage(term) for term in patient]
        if not lineages:
            return np.zeros(n)
        total = np.zeros(n)
        for lineage in lineages:
            best = np.zeros(n)
            for ancestor in lineage:
                found = self._diseases_of.get(ancestor)
                if found is not None:
                    best[found] = np.maximum(best[found], self._ic[ancestor])
            total += best
        scores = total / len(lineages)
        if masked:
            profiles = self.hpo.profiles(masked)
            for disease in self.hpo.citing(masked):
                i = self.hpo.index(disease)
                closure = self._closure(profiles[i])
                scores[i] = sum(self._best(lin, closure) for lin in lineages) / len(lineages)
        return scores
