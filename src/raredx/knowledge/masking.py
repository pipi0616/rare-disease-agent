"""Masking: hiding a test case's own source paper from the knowledge the tools read.

Phenopacket Store's cases come from published papers, and HPO curates its
disease annotations partly from the same papers. A tool scored on a case while
reading annotations drawn from that case's paper would be reading the answer.

During evaluation the harness masks each case's paper while the system works on
it; knowledge lookups then leave out whatever rests only on a masked reference.
Outside evaluation nothing is masked. The mask lives in a context variable, so
neither the system nor a model it calls sees it, or that it exists.

A context variable follows the code that set it, including into asyncio tasks;
code that hands work to its own threads must carry it across with
contextvars.copy_context() — as it must for MLflow's tracing context.
"""

from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar

_masked: ContextVar[frozenset[str]] = ContextVar("masked_references", default=frozenset())


@contextmanager
def masked(references: Iterable[str]) -> Iterator[None]:
    """Within this block, knowledge resting only on these references is hidden."""
    token = _masked.set(frozenset(references))
    try:
        yield
    finally:
        _masked.reset(token)


def current() -> frozenset[str]:
    """The references masked here; empty outside evaluation."""
    return _masked.get()
