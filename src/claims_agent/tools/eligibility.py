from collections.abc import Sequence

from claims_agent.domain.claim import Claim
from claims_agent.domain.coverage import (
    CoveragePeriod,
    EligibilityResult,
    EligibilityStatus,
)
def check_eligibility(claim: Claim, periods: Sequence[CoveragePeriod]) -> EligibilityResult:
    relevant = [p 
                for p in periods 
                if p.tenant_id == claim.tenant_id and p.patient_ref == claim.patient_ref]
    if not relevant:
        return EligibilityResult(status=EligibilityStatus.NO_COVERAGE_RECORD)
    covering = [p for p in relevant if p.contains(claim.service_date)]
    if not covering:
        return EligibilityResult(status=EligibilityStatus.NOT_COVERED_ON_DATE)
    return EligibilityResult(status=EligibilityStatus.COVERED, covering_period=min(covering, key=lambda p: p.start_date))
