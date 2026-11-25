from collections.abc import Sequence
from enum import StrEnum
from typing import Literal
from pydantic import BaseModel, ConfigDict
from claims_agent.domain.claim import Claim
from claims_agent.domain.repositories import ClaimRepository

class DuplicateStatus(StrEnum):
    NONE = "none"
    SUSPECT = "suspect"
    EXACT = "exact"

class LineMatch(BaseModel):
    model_config = ConfigDict(frozen=True)

    line_no : int
    earlier_claim_id: str
    earlier_line_no: int
    procedure_code: str
    kind: Literal["exact", "suspect"]
    differing_fields: tuple[str, ...] = ()

class DuplicateReport(BaseModel):
    model_config = ConfigDict(frozen = True)

    status : DuplicateStatus
    matches: tuple[LineMatch, ...] = ()

def _same_context(claim: Claim, other: Claim) -> bool:
    return (
        other.claim_id != claim.claim_id
        and other.tenant_id == claim.tenant_id
        and other.patient_ref == claim.patient_ref
        and other.provider_ref == claim.provider_ref
        and other.service_date == claim.service_date
    )

def classify_duplicates(claim: Claim, history: Sequence[Claim]) -> DuplicateReport:
    matches: list[LineMatch] = []
    for other in history:
        if not _same_context(claim, other):
            continue
        for number, line in enumerate(claim.lines, start=1):
            for other_number, other_line in enumerate(other.lines, start=1):
                if line.procedure_code != other_line.procedure_code:
                    continue
                if line.modifier != other_line.modifier:
                    continue
                differing: list[str] = []
                if claim.place_of_service != other.place_of_service:
                    differing.append("place_of_service")
                if line.charge_amount != other_line.charge_amount:
                    differing.append("charge_amount")
                matches.append(
                    LineMatch(
                        line_no = number,
                        earlier_claim_id = other.claim_id,
                        earlier_line_no = other_number,
                        procedure_code = line.procedure_code,
                        kind = "suspect" if differing else "exact",
                        differing_fields = tuple(differing)
                    )
                )
    matches.sort(key=lambda m: (m.line_no, m.earlier_claim_id, m.earlier_line_no))

    flagged = {m.line_no for m in matches}
    exact = {m.line_no for m in matches if m.kind == "exact"}
    if not flagged:
        status = DuplicateStatus.NONE
    elif exact == set(range(1, len(claim.lines) + 1)):
        status = DuplicateStatus.EXACT
    else:
        status = DuplicateStatus.SUSPECT
    return DuplicateReport(status = status, matches = tuple(matches))

def classify_claim_duplicates(repo: ClaimRepository, claim: Claim) -> DuplicateReport:
    history = repo.list_for_patient(claim.tenant_id, claim.patient_ref)
    return classify_duplicates(claim, history)


