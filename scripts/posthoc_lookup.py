"""Post hoc, no model calls: the model asked directly, with its answers looked up in the
knowledge base the way the agent looks up the model's own hypotheses (find_disease.resolve:
the id it wrote if the knowledge knows it, else the closest name at WRatio >= 90; a disease
the mask hides is unknown). Also a name-only lookup. Scored by identifier with Mondo
identity, like every run. Writes one TSV per test: case_id, direct@k as recorded,
lookup@k, name-only@k."""

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from raredx import cli  # noqa: E402
from raredx.config import settings  # noqa: E402
from raredx.evals import splits  # noqa: E402
from raredx.evals.harness import candidates_of  # noqa: E402
from raredx.evals.scoring import found, ranks  # noqa: E402
from raredx.evals.systems import Candidate  # noqa: E402
from raredx.knowledge import masking  # noqa: E402
from raredx.tools.find_disease import NAME_MATCH, FindDisease, resolve  # noqa: E402

TESTS = [
    ("mygene2", "9dbbb071be304c5ea31ef8788958e44b", False),
    ("cada-test", "ee81cf3c457047fd97d2f62b9dfd9b69", False),
    ("casereports-exam", "b80d3dfc7618464689ded610b77142c6", True),
]
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "docs"
data_dir, evals_dir = settings.data_dir, settings.evals_dir
identity = cli._identity(evals_dir, data_dir)
harness = cli._harness()
knowledge = {}
for split, run_id, merged in TESTS:
    if merged not in knowledge:
        knowledge[merged] = cli._knowledge(evals_dir, data_dir, orphanet=merged)
    hpo = knowledge[merged]
    find = FindDisease(hpo)
    _, pool = cli._processed(data_dir, evals_dir, splits.dataset_of(split, cli.DATASET))
    by_id = {c.id: c for c in pool}
    cases = [by_id[i] for i, _ in splits.read(cli._manifest(evals_dir, split))]
    answers = {
        t.data.spans[0].inputs["question"]["case_id"]: candidates_of(t.data.spans[0].outputs)
        for t in harness.answers(run_id)
    }
    rows = []
    for case in cases:
        given = answers.get(case.id, [])
        with masking.masked([case.pmid] if case.pmid else []):
            looked = []
            named = []
            for c in given:
                looked.append(
                    Candidate(
                        disease_name=c.disease_name,
                        disease_id=resolve(c.disease_id, c.disease_name, find),
                    )
                )
                hit = (
                    find(c.disease_name, limit=1).matches
                    if len(c.disease_name.strip()) >= 3
                    else []
                )
                named.append(
                    Candidate(
                        disease_name=c.disease_name,
                        disease_id=hit[0].disease_id
                        if hit and hit[0].similarity >= NAME_MATCH
                        else None,
                    )
                )
        row = {"case_id": case.id}
        for label, cands in (("direct", given), ("lookup", looked), ("name-only", named)):
            r, _ = ranks(cands, case.disease_id, None, case.also_accepted, identity.same)
            for k in (1, 3, 5, 10):
                row[f"{label}@{k}"] = int(found(r, k))
        rows.append(row)
    path = OUT / f"posthoc_lookup_{split}.tsv"
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter="\t")
        w.writeheader()
        w.writerows(rows)
    n = len(rows)
    print(
        split,
        n,
        {
            k: f"{100 * sum(r[f'{k}@1'] for r in rows) / n:.1f}%"
            for k in ("direct", "lookup", "name-only")
        },
        flush=True,
    )
