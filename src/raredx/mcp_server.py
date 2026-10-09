"""The tools as an MCP server: the standard way AI applications call tools.

MCP (Model Context Protocol) is the open protocol hosts — Claude Code, Claude
Desktop, IDEs, agent frameworks such as LangGraph — use to find and call tools.
A host launches `raredx mcp` and talks to it over stdin and stdout: it lists
the tools, with descriptions and JSON Schemas generated from the tools' own
signatures and docstrings, and calls them with JSON arguments.

The server adds no logic. Each tool is registered as it is, with two things
settled at the boundary: an error the model can act on (an unknown disease id)
reaches it as a tool error with its message, not as an anonymous crash; and
every tool is marked read-only and closed-world — it changes nothing and reads
nothing beyond the pinned knowledge.

Nothing is masked here; masking belongs to evaluation, which calls the tools
in its own process.
"""

import functools
import inspect
from collections.abc import Callable
from typing import Any

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations

from raredx.knowledge.hpo import HPO
from raredx.tools.check_match import CheckMatch
from raredx.tools.find_disease import FindDisease
from raredx.tools.find_similar_patients import FindSimilarPatients
from raredx.tools.ids import UnknownDisease
from raredx.tools.lookup_disease import LookupDisease
from raredx.tools.rank_diseases import RankDiseases

INSTRUCTIONS = """\
Tools for diagnosing rare diseases from a patient's phenotype, coded as HPO terms
(Human Phenotype Ontology). Start with rank_diseases on the patient's terms, and
find_similar_patients beside it when it is served; then weigh candidates with
check_match and read them with lookup_disease; find_disease gives the id of a
disease known by name. Answers cite the sources they rest on."""

READ_ONLY = ToolAnnotations(read_only_hint=True, open_world_hint=False)


def build(hpo: HPO, similar: FindSimilarPatients | None = None) -> MCPServer:
    """The MCP server over one HPO release, and over a bank of published patients when
    one is given."""
    server = MCPServer("raredx", instructions=INSTRUCTIONS)
    tools: list[Any] = [RankDiseases(hpo), LookupDisease(hpo), CheckMatch(hpo), FindDisease(hpo)]
    if similar is not None:
        tools.append(similar)
    for tool in tools:
        server.add_tool(
            _as_mcp_tool(tool.__call__, tool.name),
            name=tool.name,
            title=tool.title,
            annotations=READ_ONLY,
        )
    return server


def _as_mcp_tool(call: Callable[..., Any], name: str) -> Callable[..., Any]:
    """The tool as the SDK should read it: the bound method's signature (no self) and
    docstring, and an unknown disease raised as a ToolError, whose message the model
    sees and can act on."""

    @functools.wraps(call)
    def tool(*args: Any, **kwargs: Any) -> Any:
        try:
            return call(*args, **kwargs)
        except UnknownDisease as e:
            raise ToolError(str(e)) from e

    tool.__signature__ = inspect.signature(call)  # type: ignore[attr-defined]
    tool.__name__ = name
    return tool
