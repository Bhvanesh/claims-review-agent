from typing import Any

from claims_agent.domain.repositories import ClaimRepository, CoverageRepository
from claims_agent.mcp_server.schemas import ClaimInput
from claims_agent.tools.duplicates import check_duplicates as run_duplicate_check
from claims_agent.tools.eligibility import check_member_eligibility as run_eligibility_check


class ClaimTools:
    def __init__(
        self, tenant_id: str, claims: ClaimRepository, coverage: CoverageRepository
    ) -> None:
        if not tenant_id:
            raise ValueError("tenant_id is required")
        self._tenant_id = tenant_id
        self._claims = claims
        self._coverage = coverage

    def check_duplicates(self, claim: ClaimInput) -> dict[str, Any]:
        matches = run_duplicate_check(self._claims, claim.to_claim(self._tenant_id))
        return {"possible_duplicates": [m.model_dump(mode="json") for m in matches]}

    def check_eligibility(self, claim: ClaimInput) -> dict[str, Any]:
        result = run_eligibility_check(self._coverage, claim.to_claim(self._tenant_id))
        return result.model_dump(mode="json")