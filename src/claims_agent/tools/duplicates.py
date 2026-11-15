from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict

from claims_agent.domain.claim import Claim
from claims_agent.domain.repositories import ClaimRepository


class DuplicateMatch(BaseModel):
    model_config = ConfigDict(frozen=True)

    claim_id: str
    matching_procedure_codes: tuple[str, ...]


def find_possible_duplicates(claim: Claim, history: Sequence[Claim]) -> list[DuplicateMatch]:
    codes = {line.procedure_code for line in claim.lines}
    matches: list[DuplicateMatch] = []
    for other in history:
        if other.claim_id == claim.claim_id or other.tenant_id != claim.tenant_id:
            continue
        if other.patient_ref != claim.patient_ref:
            continue
        if other.provider_ref != claim.provider_ref or other.service_date != claim.service_date:
            continue
        shared = codes & {line.procedure_code for line in other.lines}
        if shared:
            matches.append(
                DuplicateMatch(
                    claim_id=other.claim_id,
                    matching_procedure_codes=tuple(sorted(shared)),
                )
            )
    return sorted(matches, key=lambda m: m.claim_id)


def check_duplicates(repo: ClaimRepository, claim: Claim) -> list[DuplicateMatch]:
    history = repo.list_for_patient(claim.tenant_id, claim.patient_ref)
    return find_possible_duplicates(claim, history)