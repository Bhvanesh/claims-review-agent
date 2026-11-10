from claims_agent.domain.claim import Claim
from claims_agent.domain.errors import DuplicateClaimError

class InMemoryClaimRepository:
    def __init__(self) -> None:
        self._claims: dict[tuple[str, str], Claim] = {}
    def add(self, claim:Claim) -> None:
        key = (claim.tenant_id, claim.claim_id)
        if key in self._claims:
            raise DuplicateClaimError(f"claim {claim.claim_id} already exists for tenant {claim.tenant_id}")
        self._claims[key] = claim
    def get(self, tenant_id: str, claim_id:str) -> Claim |None:
        return self._claims.get((tenant_id, claim_id))
    def list_for_tenant(self, tenant_id:str) -> list[Claim]:
        return[c for (t, _), c in self._claims.items() if t == tenant_id]
