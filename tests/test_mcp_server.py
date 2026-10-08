"""The MCP server, end to end in memory: what a host lists, and what a call returns.

The SDK's Client talks to the server object directly, through the whole
protocol, without a subprocess or a port.
"""

from collections.abc import AsyncIterator
from typing import Any

import pytest
from mcp import Client
from mcp.types import TextContent

from raredx.knowledge.hpo import HPO
from raredx.mcp_server import build
from raredx.tools.check_match import CheckMatch
from raredx.tools.lookup_disease import LookupDisease
from raredx.tools.rank_diseases import RankDiseases


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
async def client(hpo: HPO) -> AsyncIterator[Client]:
    async with Client(build(hpo), raise_exceptions=True) as c:
        yield c


def text(result: Any) -> str:
    [content] = result.content
    assert isinstance(content, TextContent)
    return content.text


@pytest.mark.anyio
async def test_a_host_finds_three_read_only_tools_described_for_a_model(client: Client) -> None:
    tools = {t.name: t for t in (await client.list_tools()).tools}
    assert set(tools) == {"rank_diseases", "lookup_disease", "check_match"}
    rank = tools["rank_diseases"]
    assert rank.title == "Rank diseases by phenotype"
    assert (rank.description or "").startswith("Rank every OMIM disease")
    assert rank.annotations is not None
    assert rank.annotations.read_only_hint is True and rank.annotations.open_world_hint is False
    # The input schema comes from the tool's signature: names, descriptions, limits.
    schema = rank.input_schema
    assert schema["required"] == ["hpo_ids"]
    assert schema["properties"]["hpo_ids"]["items"]["pattern"] == r"^HP:\d{7}$"
    assert (
        schema["properties"]["hpo_ids"]["description"] == "The patient's phenotype as HPO term ids"
    )
    assert (schema["properties"]["top_k"]["minimum"], schema["properties"]["top_k"]["maximum"]) == (
        1,
        50,
    )
    assert rank.output_schema is not None
    assert set(rank.output_schema["properties"]) == {"matches", "unrecognized", "hpo_release"}


@pytest.mark.anyio
async def test_a_call_over_mcp_returns_exactly_what_the_tool_returns(
    client: Client, hpo: HPO
) -> None:
    patient = ["HP:0000407", "HP:0000786"]
    calls: list[tuple[str, dict[str, Any], Any]] = [
        ("rank_diseases", {"hpo_ids": patient}, RankDiseases(hpo)(patient)),
        ("lookup_disease", {"disease_id": "OMIM:690005"}, LookupDisease(hpo)("OMIM:690005")),
        (
            "check_match",
            {"hpo_ids": patient, "disease_id": "OMIM:690001"},
            CheckMatch(hpo)(patient, "OMIM:690001"),
        ),
    ]
    for name, arguments, direct in calls:
        result = await client.call_tool(name, arguments)
        assert not result.is_error, name
        assert result.structured_content == direct.model_dump(mode="json"), name


@pytest.mark.anyio
async def test_an_unknown_disease_reaches_the_model_as_an_error_it_can_act_on(
    client: Client,
) -> None:
    result = await client.call_tool("lookup_disease", {"disease_id": "OMIM:999999"})
    assert result.is_error
    assert "OMIM:999999 is not a disease" in text(result) and "rank_diseases" in text(result)


@pytest.mark.anyio
async def test_malformed_arguments_are_refused_before_the_tool_runs(client: Client) -> None:
    result = await client.call_tool("rank_diseases", {"hpo_ids": ["deafness"]})
    assert result.is_error and "should match pattern" in text(result)
