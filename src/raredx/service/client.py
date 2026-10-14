"""A typed client for the service: what the demo page uses, and any script can.

The API is plain HTTP and JSON; this client only spares its callers the URLs
and the parsing. An answer comes back as the same pydantic models the server
sent, so a field renamed on one side fails loudly on the other.

Built on httpx2, the HTTP client the model SDK and the MCP SDK already bring in.
"""

import json
from collections.abc import Iterator
from typing import Any

import httpx2
from pydantic import TypeAdapter

from raredx.service.schemas import (
    DiagnoseRequest,
    DiagnoseResponse,
    Example,
    Step,
    SystemInfo,
    Term,
)

_terms = TypeAdapter(list[Term])
_examples = TypeAdapter(list[Example])


class ServiceError(Exception):
    """The service refused or failed the request."""

    def __init__(self, status_code: int, detail: Any) -> None:
        super().__init__(f"{status_code}: {detail}")
        self.status_code = status_code
        self.detail = detail


def _detail(response: httpx2.Response) -> Any:
    try:
        return response.json().get("detail", response.text)
    except (ValueError, AttributeError):
        return response.text


class Client:
    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8000",
        *,
        api_key: str | None = None,
        http: httpx2.Client | None = None,
        timeout: float = 180.0,
    ) -> None:
        """`http`: an httpx2 client to use instead of a new one (the tests pass FastAPI's
        test client, which is one)."""
        self.http = http or httpx2.Client(base_url=base_url, timeout=timeout)
        self.headers = {"X-API-Key": api_key} if api_key else {}

    def _get(self, path: str, **params: Any) -> httpx2.Response:
        response = self.http.get(path, params=params, headers=self.headers)
        if response.status_code != 200:
            raise ServiceError(response.status_code, _detail(response))
        return response

    def ready(self) -> dict[str, Any]:
        ready: dict[str, Any] = self.http.get("/readyz").raise_for_status().json()
        return ready

    def system(self) -> SystemInfo:
        return SystemInfo.model_validate_json(self._get("/v1/system").content)

    def terms(self, q: str, limit: int = 10) -> list[Term]:
        return _terms.validate_json(self._get("/v1/terms", q=q, limit=limit).content)

    def examples(self) -> list[Example]:
        return _examples.validate_json(self._get("/v1/examples").content)

    def diagnose(self, request: DiagnoseRequest) -> DiagnoseResponse:
        response = self.http.post(
            "/v1/diagnose", json=request.model_dump(exclude_none=True), headers=self.headers
        )
        if response.status_code != 200:
            raise ServiceError(response.status_code, _detail(response))
        return DiagnoseResponse.model_validate_json(response.content)

    def stream(self, request: DiagnoseRequest) -> Iterator[Step | DiagnoseResponse]:
        """Each Step as the service takes it, then the DiagnoseResponse."""
        with self.http.stream(
            "POST",
            "/v1/diagnose/stream",
            json=request.model_dump(exclude_none=True),
            headers=self.headers,
        ) as response:
            if response.status_code != 200:
                response.read()
                raise ServiceError(response.status_code, _detail(response))
            for event, data in _events(response.iter_lines()):
                if event == "step":
                    yield Step.model_validate_json(data)
                elif event == "result":
                    yield DiagnoseResponse.model_validate_json(data)
                elif event == "error":
                    raise ServiceError(500, json.loads(data).get("detail"))


def _events(lines: Iterator[str]) -> Iterator[tuple[str, str]]:
    """Server-sent events as (event, data). An event ends at an empty line; a line
    starting with a colon is a comment (the server's keep-alive)."""
    event: str = "message"
    data: list[str] = []
    for line in lines:
        if not line:
            if data:
                yield event, "\n".join(data)
            event, data = "message", []
        elif line.startswith("event:"):
            event = line[6:].strip()
        elif line.startswith("data:"):
            data.append(line[5:].removeprefix(" "))
    if data:
        yield event, "\n".join(data)
