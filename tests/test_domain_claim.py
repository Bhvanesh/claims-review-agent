from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from claims_agent.domain.claim import Claim, ClaimLine

def make_line(amount: str = "100.00") -> ClaimLine:
    return ClaimLine(procedure_code="99213", diagnosis_code="E119", charge_amount=Decimal(amount))
def make_claim(lines: list[ClaimLine] | None = None) -> Claim:
    return Claim(
        claim_id="c-1",
        tenant_id="t-1",
        patient_ref="p-1",
        provider_ref="pr-1",
        service_date=date(2009, 3, 1),
        lines=lines if lines is not None else [make_line()],
    )

def test_total_charge_sums_lines():
    claim = make_claim([make_line("100.00"), make_line("50.25")])
    assert claim.total_charge == Decimal("150.25")

def test_claim_requires_at_least_one_line():
    with pytest.raises(ValidationError):
        make_claim(lines=[])

def test_negative_charge_rejected():
    with pytest.raises(ValidationError):
        make_line("-1.00")

def test_claim_is_immutable():
    claim = make_claim()
    with pytest.raises(ValidationError):
        claim.claim_id = "other"

