import json

import pytest
from pydantic import ValidationError

from claims_agent.db.repositories.in_memory import (
    InMemoryClaimRepository,
    InMemoryCoverageRepository,
)
from claims_agent.mcp_server.schemas import ClaimInput
from claims_agent.mcp_server.service import ClaimTools


def make_input(claim_id: str = "c-2", **overrides) -> ClaimInput:
    data = {
        "claim_id": claim_id,
        "patient_ref": "p-1",
        "provider_ref": "pr-1",
        "service_date": "2009-03-01",
        "lines": [
            {"procedure_code": "99213", "diagnosis_code": "E119", "charge_amount": "100.00"}
        ],
    }
    data.update(overrides)
    return ClaimInput.model_validate(data)


def make_tools(tenant_id: str = "t-1"):
    claims = InMemoryClaimRepository()
    coverage = InMemoryCoverageRepository()
    return ClaimTools(tenant_id, claims, coverage), claims, coverage


def test_input_schema_has_no_tenant_field():
    assert "tenant_id" not in ClaimInput.model_fields


def test_tenant_id_in_input_is_rejected():
    with pytest.raises(ValidationError):
        make_input(tenant_id="t-2")


def test_empty_server_tenant_is_rejected():
    with pytest.raises(ValueError):
        ClaimTools("", InMemoryClaimRepository(), InMemoryCoverageRepository())


def test_duplicates_are_found_within_the_servers_tenant(make_claim):
    tools, claims, _ = make_tools("t-1")
    claims.add(make_claim(claim_id="c-1", tenant_id="t-1"))
    result = tools.check_duplicates(make_input())
    assert result == {
        "possible_duplicates": [{"claim_id": "c-1", "matching_procedure_codes": ["99213"]}]
    }


def test_other_tenants_claims_are_invisible(make_claim):
    tools, claims, _ = make_tools("t-1")
    claims.add(make_claim(claim_id="c-1", tenant_id="t-2"))
    assert tools.check_duplicates(make_input()) == {"possible_duplicates": []}


def test_eligibility_uses_the_servers_tenants_coverage(make_period):
    tools, _, coverage = make_tools("t-1")
    coverage.add(make_period(tenant_id="t-1"))
    result = tools.check_eligibility(make_input())
    assert result["status"] == "covered"
    assert result["covering_period"]["patient_ref"] == "p-1"


def test_other_tenants_coverage_is_ignored(make_period):
    tools, _, coverage = make_tools("t-1")
    coverage.add(make_period(tenant_id="t-2"))
    result = tools.check_eligibility(make_input())
    assert result["status"] == "no_coverage_record"


def test_results_are_json_serializable(make_claim, make_period):
    tools, claims, coverage = make_tools("t-1")
    claims.add(make_claim(claim_id="c-1", tenant_id="t-1"))
    coverage.add(make_period(tenant_id="t-1"))
    json.dumps(tools.check_duplicates(make_input()))
    json.dumps(tools.check_eligibility(make_input()))