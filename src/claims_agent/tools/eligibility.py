from collections.abc import Sequence

from claims_agent.domain.claim import Claim
from claims_agent.domain.coverage import (CoveragePeriod, EligibilityResult, EligibilityStatus)
from claims_agent.domain.repositories import CoverageRepository

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

def check_member_eligibility(repo: CoverageRepository, claim: Claim) -> EligibilityResult:
    periods = repo.list_for_patient(claim.tenant_id, claim.patient_ref)
    return check_eligibility(claim, periods)
