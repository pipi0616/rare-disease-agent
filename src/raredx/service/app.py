"""The HTTP layer: FastAPI around a Diagnoser.

    GET  /healthz              the process is up (liveness)
    GET  /readyz               it can answer: which knowledge is loaded (readiness)
    GET  /v1/system            what is serving: model, prompt, tools, knowledge, limits
    GET  /v1/terms?q=          HPO terms by name, for a form's search box
    GET  /v1/examples          published patients to try
    POST /v1/diagnose          one answer, as JSON
    POST /v1/diagnose/stream   the same as server-sent events: each step, then the answer
    GET  /docs                 the interactive reference FastAPI generates from the schemas

What the layer adds to the Diagnoser is what any service in front of a paid
model needs:

- a request is refused before any work when it is malformed, names a term the
  release does not have, or lacks the key (when one is configured);
- at most `max_concurrent` requests are answered at once; one more gets 503 and
  a Retry-After, not a queue of unknown length;
- every request has an id — the caller's X-Request-ID or a new one — returned
  in the answer, the response header and the log line;
- one log line per answer, as JSON, with what an operator needs (mode, seconds,
  tokens, cost, trace id) and none of the patient's findings;
- when a streaming client goes away, the agent stops before its next model call.

Neither health check calls the model: it is a paid, third-party call, and its
failure does not stop the service from answering (see diagnoser.py).
"""

import contextvars
import json
import logging
import queue
import re
import secrets
import threading
from collections.abc import Awaitable, Callable, Iterator, Sequence
from typing import Annotated, Any
from uuid import uuid4

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, Request, Response, Security
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from fastapi.sse import EventSourceResponse, ServerSentEvent

from raredx.service.diagnoser import Diagnoser, NoFinding, UnknownTerms
from raredx.service.schemas import (
    DISCLAIMER,
    DiagnoseRequest,
    DiagnoseResponse,
    Example,
    Problem,
    SystemInfo,
    Term,
)

logger = logging.getLogger("raredx.service")

REQUEST_ID = re.compile(r"[A-Za-z0-9._-]{1,64}")
RETRY_AFTER_SECONDS = 5
key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

DESCRIPTION = f"""\
A rare-disease diagnosis agent: a patient's findings as HPO terms in, up to ten
candidate diseases out — each with the reason it stands where it does and the
evidence it rests on, with sources.

{DISCLAIMER}
"""


def _log(answer: DiagnoseResponse, request: DiagnoseRequest) -> None:
    """One line per answer. Counts and ids only: the findings stay out of the log."""
    logger.info(
        json.dumps(
            {
                "event": "diagnose",
                "request_id": answer.request_id,
                "mode": answer.mode,
                "fallback_reason": answer.fallback_reason,
                "n_findings": len(answer.findings),
                "n_candidate_genes": len(request.candidate_genes or []),
                "n_diagnoses": len(answer.diagnoses),
                **answer.usage.model_dump(),
                "trace_id": answer.trace_id,
            }
        )
    )


def create_app(
    diagnoser: Diagnoser,
    *,
    examples: Sequence[Example] = (),
    api_key: str | None = None,
    max_concurrent: int = 4,
) -> FastAPI:
    system = diagnoser.system()
    app = FastAPI(
        title="raredx",
        version=system.service_version,
        description=DESCRIPTION,
        # MLflow records each request as one trace, rooted at the question (diagnoser.py).
        # FastAPI's own OpenTelemetry spans would wrap that root in an HTTP span, trace
        # every health check, and export wherever OTEL_* variables happen to point.
        telemetry={"tracing": False, "metrics": False, "logs": False, "auto_configure": False},
    )
    slots = threading.BoundedSemaphore(max_concurrent)

    @app.middleware("http")
    async def with_request_id(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        given = request.headers.get("x-request-id", "")
        request.state.request_id = given if REQUEST_ID.fullmatch(given) else uuid4().hex
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response

    @app.exception_handler(Exception)
    async def failed(request: Request, error: Exception) -> JSONResponse:
        """A failure of our own: logged with its request id, and said to be one."""
        request_id = getattr(request.state, "request_id", None)
        logger.error("request %s failed", request_id, exc_info=error)
        problem = Problem(detail="internal error", request_id=request_id)
        return JSONResponse(problem.model_dump(), status_code=500)

    def authorized(key: Annotated[str | None, Security(key_header)] = None) -> None:
        if api_key is not None and not (key and secrets.compare_digest(key, api_key)):
            raise HTTPException(401, "missing or wrong X-API-Key")

    def admitted(body: DiagnoseRequest) -> Iterator[DiagnoseRequest]:
        """A request the service will work on: its terms are known, and there is room.
        The room is given back when the response has ended."""
        try:
            diagnoser.findings(body)
        except (UnknownTerms, NoFinding) as e:
            raise HTTPException(422, str(e)) from e
        if not slots.acquire(blocking=False):
            raise HTTPException(
                503,
                f"busy: {max_concurrent} requests are being answered",
                headers={"Retry-After": str(RETRY_AFTER_SECONDS)},
            )
        try:
            yield body
        finally:
            slots.release()

    @app.get("/healthz", tags=["health"])
    def healthz() -> dict[str, str]:
        """The process is up. Says nothing about whether it can answer."""
        return {"status": "ok"}

    @app.get("/readyz", tags=["health"])
    def readyz() -> dict[str, Any]:
        """The knowledge is loaded: requests can be answered. The model is reported,
        not required — without it the service answers from the tools alone."""
        return {
            "status": "ready",
            "hpo_release": diagnoser.hpo.release,
            "model_available": system.model_available,
        }

    refused: dict[int | str, dict[str, Any]] = {
        401: {"model": Problem, "description": "Missing or wrong X-API-Key"},
        503: {"model": Problem, "description": "Busy: retry after the Retry-After header"},
    }
    v1 = APIRouter(prefix="/v1", dependencies=[Depends(authorized)], responses=refused)

    @v1.get("/system")
    def get_system() -> SystemInfo:
        """What is serving: enough to tie an answer to the version that was evaluated."""
        return system

    @v1.get("/terms")
    def find_terms(
        q: Annotated[str, Query(min_length=2, max_length=60, description="Part of a name")],
        limit: Annotated[int, Query(ge=1, le=50)] = 10,
    ) -> list[Term]:
        """HPO terms for findings whose name contains the text."""
        return [Term(hpo_id=i, label=name) for i, name in diagnoser.hpo.search(q, limit)]

    @v1.get("/examples")
    def get_examples() -> list[Example]:
        """Published patients to try, each with the diagnosis its paper confirmed."""
        return list(examples)

    @v1.post("/diagnose")
    def diagnose(
        body: Annotated[DiagnoseRequest, Depends(admitted)], request: Request
    ) -> DiagnoseResponse:
        """Rank candidate diseases for one patient. Takes about as long as the agent
        works: seconds to a minute. The answer says whether the agent or the fallback
        produced it."""
        answer = diagnoser.diagnose(body, request_id=request.state.request_id)
        _log(answer, body)
        return answer

    @v1.post("/diagnose/stream", response_class=EventSourceResponse)
    def diagnose_stream(
        body: Annotated[DiagnoseRequest, Depends(admitted)], request: Request
    ) -> Iterator[ServerSentEvent]:
        """The same answer as server-sent events: a `step` event (a Step) for each thing
        the system does, as it does it; then one `result` event (the full answer), or
        an `error` event."""
        request_id = request.state.request_id
        events: queue.SimpleQueue[ServerSentEvent | None] = queue.SimpleQueue()
        gone = threading.Event()  # set when nobody is reading any more

        def work() -> None:
            try:
                answer = diagnoser.diagnose(
                    body,
                    request_id=request_id,
                    on_step=lambda step: events.put(ServerSentEvent(event="step", data=step)),
                    cancelled=gone.is_set,
                )
                _log(answer, body)
                events.put(ServerSentEvent(event="result", data=answer))
            except Exception:
                logger.exception("request %s failed", request_id)
                problem = Problem(detail="internal error", request_id=request_id)
                events.put(ServerSentEvent(event="error", data=problem))
            finally:
                events.put(None)

        # The agent's call blocks until it answers, so it runs beside the stream; the
        # copied context carries what the request set (as for any hand-off to a thread).
        worker = threading.Thread(target=contextvars.copy_context().run, args=(work,), daemon=True)
        worker.start()
        try:
            while (event := events.get()) is not None:
                yield event
        finally:
            gone.set()

    app.include_router(v1)
    return app
