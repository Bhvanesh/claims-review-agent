from claims_agent.db.models import ClaimLineRow, ClaimRow
from claims_agent.domain.claim import Claim, ClaimLine
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import IntegrityError
from claims_agent.domain.errors import DuplicateClaimError

UNIQUE_VIOLATION = "23505"

def _to_row(claim: Claim) -> ClaimRow:
    return ClaimRow(
        tenant_id=claim.tenant_id,
        claim_id=claim.claim_id,
        patient_ref=claim.patient_ref,
        provider_ref=claim.provider_ref,
        service_date=claim.service_date,
        lines=[
            ClaimLineRow(
                tenant_id=claim.tenant_id,
                claim_id=claim.claim_id,
                line_no=number,
                procedure_code=line.procedure_code,
                diagnosis_code=line.diagnosis_code,
                charge_amount=line.charge_amount,
            )
            for number, line in enumerate(claim.lines, start=1)
        ],
    )


def _to_domain(row: ClaimRow) -> Claim:
    return Claim(
        claim_id=row.claim_id,
        tenant_id=row.tenant_id,
        patient_ref=row.patient_ref,
        provider_ref=row.provider_ref,
        service_date=row.service_date,
        lines=[
            ClaimLine(
                procedure_code=line.procedure_code,
                diagnosis_code=line.diagnosis_code,
                charge_amount=line.charge_amount,
            )
            for line in row.lines
        ],
    )

class PostgresClaimRepository:
    def __init__(self, session: Session) -> None:
        self._session = session
    def add(self, claim: Claim) -> None:
        if self._session.get(ClaimRow, (claim.tenant_id, claim.claim_id)) is not None:
            raise DuplicateClaimError(f"claim {claim.claim_id} already exists for tenant {claim.tenant_id}")
        self._session.add(_to_row(claim))
        try:
            self._session.flush()
        except IntegrityError as e:
            if getattr(exc.orig, "sqlstate", None) == UNIQUE_VIOLATION:
                raise DuplicateClaimError(f"claim {claim.claim_id} already exists for tenant {claim.tenant_id}") from exc
            raise

    def get(self, tenant_id: str, claim_id: str) -> Claim | None:
        row = self._session.get(ClaimRow, (tenant_id, claim_id))
        return _to_domain(row) if row is not None else None

    def list_for_tenant(self, tenant_id: str) -> list[Claim]:
        statement = (
            select(ClaimRow).where(ClaimRow.tenant_id == tenant_id).options(selectinload(ClaimRow.lines)).order_by(ClaimRow.claim_id))
        return [_to_domain(row) for row in self._session.scalars(statement).all()]
        
            

    
