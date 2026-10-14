"""An agent's model calls and tool calls, relayed as they happen.

The agent is not changed to be watched. LangChain attaches a callback handler
held in a registered context variable to every run started in that context —
the way its own usage counters and tracers are attached. The service sets one
around its call to Agent.predict, so the code that answers a request is the
code that was evaluated, to the line.

The watcher is also where a run is stopped. Before each model call it checks
the request's deadline, and whether the caller has gone away: a run that should
not go on stops there, between two steps — a thread cannot be killed in the
middle of one, and the next model call is where the next cost would be.
"""

import json
import logging
import threading
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, NamedTuple
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.tracers.context import register_configure_hook

logger = logging.getLogger(__name__)


class DeadlineExceeded(Exception):
    """The request's deadline passed before the agent's next model call."""


class Cancelled(Exception):
    """The caller went away before the agent's next model call."""


class ModelTurn(NamedTuple):
    turn: int
    calls: list[tuple[str, dict[str, Any]]]  # the tools the model asked for, with arguments


class ToolResult(NamedTuple):
    tool: str
    arguments: dict[str, Any]
    output: Any  # the tool's answer as parsed JSON; None when it failed
    error: str | None


Event = ModelTurn | ToolResult


class Watcher(BaseCallbackHandler):
    """Relays one agent run's events to `on_event`, counts its tokens, and stops it
    when its deadline has passed or `cancelled()` says the caller is gone."""

    raise_error = True  # so that stopping a run works; nothing else is raised from here

    def __init__(
        self,
        on_event: Callable[[Event], None],
        deadline: float,
        cancelled: Callable[[], bool] | None = None,
    ) -> None:
        self.on_event = on_event
        self.deadline = deadline  # on time.monotonic()'s clock
        self.cancelled = cancelled
        self.model_calls = 0
        self.input_tokens = 0
        self.cached_input_tokens = 0
        self.output_tokens = 0
        self._lock = threading.Lock()  # a turn's tool calls run in parallel threads
        self._running: dict[UUID, tuple[str, dict[str, Any]]] = {}

    def on_chat_model_start(self, serialized: Any, messages: Any, **kwargs: Any) -> None:
        if self.cancelled is not None and self.cancelled():
            raise Cancelled
        if time.monotonic() > self.deadline:
            raise DeadlineExceeded
        with self._lock:
            self.model_calls += 1

    def on_llm_end(self, response: Any, **kwargs: Any) -> None:
        with self._relaying():
            message = response.generations[0][0].message
            usage = getattr(message, "usage_metadata", None) or {}
            with self._lock:
                self.input_tokens += usage.get("input_tokens", 0)
                self.output_tokens += usage.get("output_tokens", 0)
                details = usage.get("input_token_details") or {}
                self.cached_input_tokens += details.get("cache_read", 0) or 0
                turn = self.model_calls
            calls = [(c["name"], dict(c["args"])) for c in getattr(message, "tool_calls", [])]
            self.on_event(ModelTurn(turn, calls))

    def on_tool_start(
        self,
        serialized: Any,
        input_str: str,
        *,
        run_id: UUID,
        inputs: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        with self._relaying():
            name = (serialized or {}).get("name") or kwargs.get("name") or "tool"
            with self._lock:
                self._running[run_id] = (str(name), dict(inputs or {}))

    def on_tool_end(self, output: Any, *, run_id: UUID, **kwargs: Any) -> None:
        with self._relaying():
            name, arguments = self._finished(run_id)
            content = getattr(output, "content", output)
            try:
                parsed = json.loads(content) if isinstance(content, str) else content
            except ValueError:
                parsed = None
            self.on_event(ToolResult(name, arguments, parsed, None))

    def on_tool_error(self, error: BaseException, *, run_id: UUID, **kwargs: Any) -> None:
        with self._relaying():
            name, arguments = self._finished(run_id)
            self.on_event(ToolResult(name, arguments, None, str(error)))

    def _finished(self, run_id: UUID) -> tuple[str, dict[str, Any]]:
        with self._lock:
            return self._running.pop(run_id, ("tool", {}))

    @contextmanager
    def _relaying(self) -> Iterator[None]:
        """Watching must never break what is watched: a failure to relay is logged."""
        try:
            yield
        except Exception:
            logger.exception("could not relay an agent event")


_watcher: ContextVar[Watcher | None] = ContextVar("raredx_watcher", default=None)
register_configure_hook(_watcher, inheritable=True)


@contextmanager
def watching(watcher: Watcher) -> Iterator[None]:
    """Within this block, every LangChain run started here reports to the watcher."""
    token = _watcher.set(watcher)
    try:
        yield
    finally:
        _watcher.reset(token)
