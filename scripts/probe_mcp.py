import asyncio
from contextlib import contextmanager
from datetime import date
from decimal import Decimal

from mcp import Client

from claims_agent.db.repositories.in_memory import (
    InMemoryClaimRepository,
    InMemoryCoverageRepository,
)
from claims_agent.domain.claim import Claim, ClaimLine
from claims_agent.domain.coverage import CoveragePeriod
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


async def main() -> None:
    claims = InMemoryClaimRepository()
    coverage = InMemoryCoverageRepository()
    claims.add(
        Claim(
            claim_id="c-1",
            tenant_id="t-1",
            patient_ref="p-1",
            provider_ref="pr-1",
            service_date=date(2009, 3, 1),
            lines=[
                ClaimLine(
                    procedure_code="99213",
                    diagnosis_code="E119",
                    charge_amount=Decimal("100.00"),
                )
            ],
        )
    )
    coverage.add(
        CoveragePeriod(
            tenant_id="t-1", patient_ref="p-1", start_date=date(2009, 1, 1), end_date=None
        )
    )
    tools = ClaimTools("t-1", claims, coverage)

    @contextmanager
    def open_tools():
        yield tools

    server = build_server(open_tools)

    async with Client(server) as client:
        listed = await client.list_tools()
        print("=== list_tools:", type(listed))
        print(listed)

        duplicates = await client.call_tool("check_duplicates", {"claim": CLAIM})
        print("=== check_duplicates:", type(duplicates))
        print(duplicates)

        eligibility = await client.call_tool("check_eligibility", {"claim": CLAIM})
        print("=== check_eligibility:", type(eligibility))
        print(eligibility)

     

asyncio.run(main())