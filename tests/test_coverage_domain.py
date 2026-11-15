from datetime import date
import pytest
from pydantic import ValidationError
from claims_agent.domain.coverage import CoveragePeriod

def make_period(start=date(2009,1,1), end=date(2009,12,31))-> CoveragePeriod:
    return CoveragePeriod(tenant_id = "t-1", patient_ref="p-1", start_date=start, end_date=end)

@pytest.mark.parametrize(
    "day, expected",
    [
        (date(2008, 12, 31), False),
        (date(2009, 1, 1), True),
        (date(2009, 6, 15), True),
        (date(2009, 12, 31), True),
        (date(2010, 1, 1), False),
    ],
)

def test_contains_is_inclusive_on_both_ends(day, expected):
    assert make_period().contains(day) is expected


def test_open_ended_period_covers_any_later_date():
    period = make_period(end=None)
    assert period.contains(date(2030, 1, 1)) is True
    assert period.contains(date(2008, 12, 31)) is False


def test_end_before_start_rejected():
    with pytest.raises(ValidationError):
        make_period(start=date(2009, 6, 1), end=date(2009, 5, 31))


def test_single_day_period_is_allowed():
    period = make_period(start=date(2009, 6, 1), end=date(2009, 6, 1))
    assert period.contains(date(2009, 6, 1)) is True