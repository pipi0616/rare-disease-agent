"""Keeping a clinical note out of the traces.

A note is the one piece of free text the service takes, and the most sensitive:
it may name the patient, a date, a place. It is sent to the model provider —
that is how it is read — but it must not be kept here. Every request is traced
(MLflow), and a trace records what each span was given and what it gave back:
the reader's input, each model call's messages and reply, each search's query.

So while a note is read, every span that ends has its inputs and outputs
replaced before it is recorded: a span processor, MLflow's hook for masking
data in traces. The trace keeps its shape — which steps ran, how long each
took, the tokens each model call used — and the request's own span records
the HPO terms found and how many characters were read: codes and counts.

Whether a span belongs to a note's reading is told by a context variable, set
around the reading: span processors run as the span ends, in the thread that
ends it, so the variable is the one the reading set.
"""

import contextvars
from collections.abc import Iterator
from contextlib import contextmanager
from typing import TYPE_CHECKING

import mlflow

if TYPE_CHECKING:
    from mlflow.entities import LiveSpan

REDACTED = "[not recorded: a clinical note was being read]"

_reading_note: contextvars.ContextVar[bool] = contextvars.ContextVar("reading_note", default=False)


def redact(span: "LiveSpan") -> None:
    """The span processor: a span ended while a note is read records nothing it saw."""
    if _reading_note.get():
        span.set_inputs(REDACTED)
        span.set_outputs(REDACTED)


@contextmanager
def private() -> Iterator[None]:
    """Spans ending inside this block are redacted."""
    token = _reading_note.set(True)
    try:
        yield
    finally:
        _reading_note.reset(token)


def install() -> None:
    """Add the redaction to this process's tracing, keeping any processor already set."""
    from mlflow.tracing.config import get_config

    processors = list(get_config().span_processors)
    if redact not in processors:
        mlflow.tracing.configure(span_processors=[*processors, redact])
