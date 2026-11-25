from decimal import Decimal

import pytest 
from pydantic import ValidationError
from claims_agent.domain.claim import ClaimLine

def make_line(modifier: str | None) -> ClaimLine:
    return ClaimLine(
        procedure_code = "99213",
        diagnosis_code = "E119",
        charge_amount = Decimal("1.00"),
        modifier = modifier,
    )

def test_new_fields_default_to_none(make_claim):
    claim = make_claim()
    assert claim.place_of_service is None
    assert claim.lines[0].modifier is None

def test_modifier_is_uppercased():
    assert make_line("lt").modifier == "LT"

@pytest.mark.parametrize("bad", ["", "ABC"])
def test_invalid_modifier_rejected(bad):
    with pytest.raises(ValidationError):
        make_line(bad)

@pytest.mark.parametrize("bad", ["", "111"])
def test_invalid_place_of_service_rejected(make_claim, bad):
    with pytest.raises(ValidationError):
        make_claim(place_of_service=bad)