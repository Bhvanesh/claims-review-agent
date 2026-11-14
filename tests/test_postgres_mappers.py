from datetime import date
from decimal import Decimal

from claims_agent.db.repositories.postgres import _to_domain, _to_row
from claims_agent.domain.claim import Claim, ClaimLine


def test_claim_survives_row_conversion(make_claim):
    claim = make_claim()
    assert _to_domain(_to_row(claim)) == claim


def test_multiple_lines_keep_order_and_numbers():
    claim = Claim(
        claim_id="c-1",
        tenant_id="t-1",
        patient_ref="p-1",
        provider_ref="pr-1",
        service_date=date(2009, 3, 1),
        lines=[
            ClaimLine(
                procedure_code="99213", diagnosis_code="E119", charge_amount=Decimal("100.50")
            ),
            ClaimLine(
                procedure_code="85025", diagnosis_code="E119", charge_amount=Decimal("20.00")
            ),
        ],
    )
    row = _to_row(claim)
    assert [line.line_no for line in row.lines] == [1, 2]
    assert _to_domain(row) == claim