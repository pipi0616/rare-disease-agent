"""Stage ③ of v2.0, offline: score the pool's rows with weights learned from cases, and
check whether the weights carry over to a source they were not learned on.

The scorer is a logistic regression (scikit-learn): each feature gets one weight, a
candidate's score is their weighted sum, and the weights can be read — on
standardized features, so their sizes compare. Each feature enters twice: as it is,
and as its distance from the best value among the case's candidates, since a
candidate is chosen against the others of its case (the within-case view of
learning to rank). It is fitted on candidates labelled right or wrong, every source
weighing the same whatever its number of candidates, so the largest source cannot
set the weights alone.

Two ways of judging it:
- other sources: the weights are learned on every source but one and judged on that
  one, in turn for each. This is the test — a way of scoring that works only where it
  learned fails here.
- same source: five folds of cases within each source. Optimistic (a source's
  diseases recur across its folds); it shows what the features can do at best.
"""

from collections import Counter, defaultdict

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import StandardScaler

from raredx.ranking.pool import Row

FOLDS = 5


def columns(features: tuple[str, ...]) -> tuple[str, ...]:
    """The model's inputs: each feature, then each feature against the case's best."""
    return (*features, *(f"{f} vs best" for f in features))


def _arrays(rows: list[Row], features: tuple[str, ...]) -> tuple[np.ndarray, np.ndarray]:
    raw = np.array([[r.features[f] for f in features] for r in rows], dtype=float)
    best = np.empty_like(raw)
    of_case: dict[str, list[int]] = defaultdict(list)
    for i, r in enumerate(rows):
        of_case[r.case_id].append(i)
    for indices in of_case.values():
        best[indices] = raw[indices].max(axis=0)
    y = np.array([r.correct for r in rows], dtype=int)
    return np.hstack([raw, raw - best]), y


def fit(rows: list[Row], features: tuple[str, ...]) -> Pipeline:
    """Weights learned on these rows, each source weighing the same."""
    per_source = Counter(r.source for r in rows)
    weight = np.array([1 / per_source[r.source] for r in rows])
    x, y = _arrays(rows, features)
    model = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000))
    model.fit(x, y, logisticregression__sample_weight=weight * len(rows) / len(per_source))
    return model


def ranked(model: Pipeline, rows: list[Row], features: tuple[str, ...]) -> dict[str, list[str]]:
    """Each case's candidates, best score first (ties in disease-id order)."""
    if not rows:
        return {}
    scores = model.decision_function(_arrays(rows, features)[0])
    by_case: dict[str, list[tuple[float, str]]] = defaultdict(list)
    for row, score in zip(rows, scores, strict=True):
        by_case[row.case_id].append((-score, row.disease_id))
    return {case: [d for _, d in sorted(pairs)] for case, pairs in by_case.items()}


def other_sources(rows: list[Row], features: tuple[str, ...]) -> dict[str, list[str]]:
    """Each case's ranking by weights learned on the other sources only."""
    out: dict[str, list[str]] = {}
    for source in sorted({r.source for r in rows}):
        model = fit([r for r in rows if r.source != source], features)
        out |= ranked(model, [r for r in rows if r.source == source], features)
    return out


def same_source(rows: list[Row], features: tuple[str, ...]) -> dict[str, list[str]]:
    """Each case's ranking by weights learned on the other folds of its own source."""
    out: dict[str, list[str]] = {}
    for source in sorted({r.source for r in rows}):
        mine = [r for r in rows if r.source == source]
        cases = sorted({r.case_id for r in mine})
        for _, test in GroupKFold(min(FOLDS, len(cases))).split(cases, groups=cases):
            held = {cases[i] for i in test}
            model = fit([r for r in mine if r.case_id not in held], features)
            out |= ranked(model, [r for r in mine if r.case_id in held], features)
    return out


def weights(model: Pipeline, features: tuple[str, ...]) -> dict[str, float]:
    """Each input's weight, per standard deviation of the input."""
    coefficients = model.named_steps["logisticregression"].coef_[0]
    return dict(zip(columns(features), (float(c) for c in coefficients), strict=True))
