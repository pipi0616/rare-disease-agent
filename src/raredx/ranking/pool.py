"""The candidate pool and its evidence: stages ① and ② of v2.0, computed offline.

Every disease any route names for a case — the model's own answer, the phenotype
ranking, the nearest published patients — gets one row of evidence: where each
route put it, how much of the patient it explains, what its sources found absent,
how much HPO says about it, how common Orphanet says it is.

Nothing here calls a model. The model's answer is read back from a recorded run of
the single-call baseline (llm-direct), the same question the hypothesis agent asks
first, and resolved to HPO's diseases the way the agent resolves it. So ways of
scoring the rows can be tried on every source at no cost, before one is built into
the agent (chapter 30).

Rows are computed under the case's mask, as the tools run during evaluation: a
disease known only from the case's own paper does not exist, and annotations
resting only on it are not counted.
"""

import math
from collections.abc import Iterable

from pydantic import BaseModel

from raredx.baselines.similar_patients import SimilarPatientsRank
from raredx.data.cases import Case
from raredx.evals.scoring import normalize_disease
from raredx.evals.systems import Candidate, question_of
from raredx.knowledge import masking
from raredx.knowledge.prevalence import Band
from raredx.tools.check_match import CheckMatch
from raredx.tools.find_disease import FindDisease, resolve
from raredx.tools.rank_diseases import RankDiseases

# How far down each route's list the pool reaches.
DEPTH = {"model": 10, "phenotype": 20, "patients": 10}
ROUTES = tuple(DEPTH)
# Orphanet's prevalence bands as features; a disease of unknown prevalence has none of them.
BANDS: dict[Band, str] = {
    "1 in 100,000 or more": "common",
    "1–9 in 1,000,000": "uncommon",
    "under 1 in 1,000,000": "rarest",
}
FEATURES = (
    *ROUTES,  # 1 / its place in that route's list; 0 when the route did not name it
    "routes",  # how many routes named it
    "explained",  # share of the patient's findings it explains
    "contradicted",  # findings its sources looked for and found absent
    "missing",  # log(1 + its frequent features the patient lacks)
    "annotations",  # log(1 + phenotypic features HPO lists for it)
    *BANDS.values(),
)


class Row(BaseModel):
    source: str  # the manifest the case comes from, e.g. rarebench-hms
    case_id: str
    disease_id: str
    correct: bool
    features: dict[str, float]


def accepted(case: Case) -> set[str]:
    """The OMIM entries that count as the case's diagnosis."""
    return {d for d in map(normalize_disease, (case.disease_id, *case.also_accepted)) if d}


def reciprocal(ranked: list[str], disease: str) -> float:
    """1 for a route's first disease, 1/2 for its second, …; 0 when it did not name it."""
    return 1 / (ranked.index(disease) + 1) if disease in ranked else 0.0


def unique(diseases: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(diseases))


class Pool:
    """A case's candidates from every route, each with its row of evidence."""

    def __init__(
        self,
        ranker: RankDiseases,
        check: CheckMatch,
        patients: SimilarPatientsRank,
        bands: dict[str, Band],
    ) -> None:
        self.hpo = ranker.hpo
        self.ranker, self.check, self.patients, self.bands = ranker, check, patients, bands
        self.find = FindDisease(self.hpo)

    def routes(self, case: Case, guesses: list[Candidate]) -> dict[str, list[str]]:
        """Each route's diseases, best first, each named once. Call under the case's mask.

        Only diseases HPO annotates can be checked: a published patient's diagnosis
        HPO has no entry for is left out, as is one the mask hides."""
        hidden = self.hpo.known_only_from(masking.current())
        model = unique(
            d for g in guesses if (d := resolve(g.disease_id, g.disease_name, self.find))
        )
        phenotype = self.ranker(case.hpo_ids, top_k=DEPTH["phenotype"]).matches
        nearest = [
            c.disease_id
            for c in self.patients.predict(question_of(case))
            if c.disease_id in self.hpo.names and c.disease_id not in hidden
        ]
        return {
            "model": model[: DEPTH["model"]],
            "phenotype": [m.disease_id for m in phenotype],
            "patients": unique(nearest)[: DEPTH["patients"]],
        }

    def rows(
        self,
        source: str,
        case: Case,
        guesses: list[Candidate],
        extra: dict[str, list[str]] | None = None,
    ) -> list[Row]:
        """One row per candidate. `extra` adds a feature per named list (a recorded
        agent's answer, say): 1 / the candidate's place in it, as for a route."""
        truth = accepted(case)
        with masking.masked([case.pmid] if case.pmid else []):
            routes = self.routes(case, guesses)
            rows = []
            for disease in unique(d for ranked in routes.values() for d in ranked):
                report = self.check(case.hpo_ids, disease)
                features = {route: reciprocal(ranked, disease) for route, ranked in routes.items()}
                features["routes"] = float(sum(disease in ranked for ranked in routes.values()))
                features["explained"] = len(report.explained) / max(report.n_findings, 1)
                features["contradicted"] = float(len(report.contradicted))
                features["missing"] = math.log1p(report.n_missing)
                annotated = self.hpo.features(disease, masking.current())
                features["annotations"] = math.log1p(len(annotated))
                band = self.bands.get(disease)
                features |= {name: float(band == b) for b, name in BANDS.items()}
                features |= {
                    name: reciprocal(ranked, disease) for name, ranked in (extra or {}).items()
                }
                rows.append(
                    Row(
                        source=source,
                        case_id=case.id,
                        disease_id=disease,
                        correct=disease in truth,
                        features=features,
                    )
                )
        return rows
