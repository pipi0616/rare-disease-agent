"""The phenotype + genotype track: each case with a simulated sequencing result.

In the clinic a rare-disease patient is usually sequenced; after the standard
filters, the exome leaves tens of candidate genes with rare variants, and one
of them, if any, is causal. Phenopacket Store records the causal gene but not
the rest of the exome, so the rest is simulated:

- the case's causal gene, and 49 decoys drawn from the genes HPO associates
  with an annotated OMIM disease (Mendelian): a filtered exome restricted to known
  disease genes, in order of magnitude;
- no decoy is associated with the case's own disease, so no decoy is right;
- the draw is seeded by the case id: the same list every run;
- the list is sorted by symbol, so its order says nothing.

Simplifications, stated wherever results are reported: genes only (no variant,
zygosity or pathogenicity score), decoys drawn uniformly from disease genes
(a real exome's are biased towards long and variable genes). The track is a
different exam from phenotype alone, and is reported apart from it.
"""

import hashlib
import random

from raredx.data.cases import Case
from raredx.knowledge.hpo import HPO

N_CANDIDATES = 50
SPEC = (
    f"genes-v3: causal + {N_CANDIDATES - 1} decoys "
    "from HPO's Mendelian genes of annotated OMIM diseases"
)


def candidate_genes(case: Case, hpo: HPO, n: int = N_CANDIDATES) -> list[str]:
    """The case's simulated candidate genes: its causal gene and n - 1 decoys, sorted."""
    if case.gene is None:
        raise ValueError(f"{case.id} has no causal gene to sequence")
    excluded = {case.gene, *hpo.genes.get(case.disease_id, ()), *(v.gene for v in case.variants)}
    pool = sorted(g for g in hpo.diseases_of_gene if g not in excluded)
    seed = int.from_bytes(hashlib.sha256(case.id.encode()).digest()[:8], "big")
    decoys = random.Random(seed).sample(pool, n - 1)
    return sorted([case.gene, *decoys])
