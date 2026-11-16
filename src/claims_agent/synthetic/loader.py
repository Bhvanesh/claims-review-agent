from collections.abc import Sequence
from pydantic import BaseModel, ConfigDict
from sqlalchemy import delete
from sqlalchemy.orm import Session

from claims_agent.db.models import ClaimLineRow, ClaimRow, CoveragePeriodRow
from claims_agent.domain.repositories import ClaimRepository, CoverageRepository
from claims_agent.synthetic.cases import LabeledCase
from claims_agent.synthetic.generator import TENANT_ID


from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict
from sqlalchemy import delete
from sqlalchemy.orm import Session

from claims_agent.db.models import ClaimLineRow, ClaimRow, CoveragePeriodRow
from claims_agent.domain.repositories import ClaimRepository, CoverageRepository
from claims_agent.synthetic.cases import LabeledCase
from claims_agent.synthetic.generator import TENANT_ID


class LoadSummary(BaseModel):
    model_config = ConfigDict(frozen=True)

    claims: int
    coverage_periods: int


def _require_synthetic_tenant(case: LabeledCase) -> None:
    tenant_ids = {case.claim.tenant_id}
    tenant_ids |= {earlier.tenant_id for earlier in case.history}
    tenant_ids |= {period.tenant_id for period in case.coverage}
    if tenant_ids != {TENANT_ID}:
        raise ValueError(f"{case.case_id}: every record must belong to tenant {TENANT_ID}")


def load_cases(
    cases: Sequence[LabeledCase], claims: ClaimRepository, coverage: CoverageRepository
) -> LoadSummary:
    for case in cases:
        _require_synthetic_tenant(case)

    claim_count = 0
    period_count = 0
    for case in cases:
        for earlier in case.history:
            claims.add(earlier)
            claim_count += 1
        for period in case.coverage:
            coverage.add(period)
            period_count += 1
    return LoadSummary(claims=claim_count, coverage_periods=period_count)


def reset_synthetic_tenant(session: Session) -> None:
    session.execute(delete(ClaimLineRow).where(ClaimLineRow.tenant_id == TENANT_ID))
    session.execute(delete(ClaimRow).where(ClaimRow.tenant_id == TENANT_ID))
    session.execute(delete(CoveragePeriodRow).where(CoveragePeriodRow.tenant_id == TENANT_ID))