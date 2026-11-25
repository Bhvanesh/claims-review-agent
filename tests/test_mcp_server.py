import asyncio
import json
from contextlib import contextmanager

from mcp import Client

from claims_agent.db.repositories.in_memory import (
    InMemoryClaimRepository,
    InMemoryCoverageRepository,
)
from claims_agent.mcp_server.server import build_server
from claims_agent.mcp_server.service import ClaimTools

CLAIM = {
    "claim_id": "c-2",
    "patient_ref": "p-1",
    "provider_ref": "pr-1",
    "service_date": "2009-03-01",
    "lines": [
        {"procedure_code": "99213", "diagnosis_code": "E119", "charge_amount": "100.00"}
    ],
}


class Harness:
    def __init__(self, tenant_id: str = "t-1") -> None:
        self.claims = InMemoryClaimRepository()
        self.coverage = InMemoryCoverageRepository()
        self.opened = 0
        self.closed = 0
        self._tools = ClaimTools(tenant_id, self.claims, self.coverage)
        self.server = build_server(self._open_tools)

    @contextmanager
    def _open_tools(self):
        self.opened += 1
        try:
            yield self._tools
        finally:
            self.closed += 1

    def call(self, name: str, arguments: dict):
        async def run():
            async with Client(self.server) as client:
                return await client.call_tool(name, arguments)

        return asyncio.run(run())

    def list_tools(self):
        async def run():
            async with Client(self.server) as client:
                return await client.list_tools()

        return asyncio.run(run()).tools


def test_server_lists_exactly_the_two_tools():
    names = {tool.name for tool in Harness().list_tools()}
    assert names == {"check_duplicates", "check_eligibility"}


def test_tool_schemas_do_not_offer_a_tenant_id():
    for tool in Harness().list_tools():
        schema = tool.input_schema
        assert "tenant_id" not in json.dumps(schema), tool.name
        assert schema["$defs"]["ClaimInput"]["additionalProperties"] is False, tool.name


def test_duplicates_through_the_protocol(make_claim):
    harness = Harness("t-1")
    harness.claims.add(make_claim(claim_id="c-1", tenant_id="t-1"))
    result = harness.call("check_duplicates", {"claim": CLAIM})
    assert result.is_error is False
    assert result.structured_content == {
        "possible_duplicates": [{"claim_id": "c-1", "matching_procedure_codes": ["99213"]}]
    }


def test_eligibility_through_the_protocol(make_period):
    harness = Harness("t-1")
    harness.coverage.add(make_period(tenant_id="t-1"))
    result = harness.call("check_eligibility", {"claim": CLAIM})
    assert result.is_error is False
    assert result.structured_content["status"] == "covered"


def test_other_tenants_data_is_invisible_through_the_protocol(make_claim, make_period):
    harness = Harness("t-1")
    harness.claims.add(make_claim(claim_id="c-1", tenant_id="t-2"))
    harness.coverage.add(make_period(tenant_id="t-2"))
    duplicates = harness.call("check_duplicates", {"claim": CLAIM})
    eligibility = harness.call("check_eligibility", {"claim": CLAIM})
    assert duplicates.structured_content == {"possible_duplicates": []}
    assert eligibility.structured_content["status"] == "no_coverage_record"


def test_tenant_id_in_arguments_is_rejected_not_ignored():
    harness = Harness("t-1")
    result = harness.call("check_duplicates", {"claim": {**CLAIM, "tenant_id": "t-2"}})
    assert result.is_error is True
    assert "tenant_id" in result.content[0].text


def test_invalid_claim_is_reported_as_an_error():
    harness = Harness("t-1")
    result = harness.call("check_eligibility", {"claim": {**CLAIM, "lines": []}})
    assert result.is_error is True


def test_every_call_opens_and_closes_its_own_tools():
    harness = Harness("t-1")
    harness.call("check_duplicates", {"claim": CLAIM})
    harness.call("check_eligibility", {"claim": CLAIM})
    assert (harness.opened, harness.closed) == (2, 2)


def test_rejected_arguments_never_open_tools():
    harness = Harness("t-1")
    harness.call("check_duplicates", {"claim": {**CLAIM, "tenant_id": "t-2"}})
    assert harness.opened == 0