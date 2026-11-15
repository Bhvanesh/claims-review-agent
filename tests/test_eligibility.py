from datetime import date

from claims_agent.domain.coverage import CoveragePeriod, EligibilityStatus
from claims_agent.tools.eligibility import check_eligibility


def make_period(
    tenant_id="t-1",
    patient_ref="p-1",
    start=date(2009, 1, 1),
    end=date(2009, 12, 31),
) -> CoveragePeriod:
    return CoveragePeriod(
        tenant_id=tenant_id, patient_ref=patient_ref, start_date=start, end_date=end
    )


def test_covered_when_a_period_contains_the_service_date(make_claim):
    result = check_eligibility(make_claim(), [make_period()])
    assert result.status is EligibilityStatus.COVERED
    assert result.covering_period == make_period()


def test_not_covered_when_records_exist_but_none_contain_the_date(make_claim):
    claim = make_claim(service_date=date(2010, 6, 1))
    result = check_eligibility(claim, [make_period()])
    assert result.status is EligibilityStatus.NOT_COVERED_ON_DATE
    assert result.covering_period is None


def test_no_record_when_there_are_no_periods(make_claim):
    result = check_eligibility(make_claim(), [])
    assert result.status is EligibilityStatus.NO_COVERAGE_RECORD


def test_other_patients_periods_do_not_count(make_claim):
    result = check_eligibility(make_claim(), [make_period(patient_ref="p-2")])
    assert result.status is EligibilityStatus.NO_COVERAGE_RECORD


def test_other_tenants_periods_do_not_count(make_claim):
    result = check_eligibility(make_claim(), [make_period(tenant_id="t-2")])
    assert result.status is EligibilityStatus.NO_COVERAGE_RECORD


def test_any_period_can_provide_coverage(make_claim):
    periods = [
        make_period(start=date(2008, 1, 1), end=date(2008, 12, 31)),
        make_period(start=date(2009, 1, 1), end=date(2009, 6, 30)),
    ]
    result = check_eligibility(make_claim(), periods)
    assert result.status is EligibilityStatus.COVERED


def test_earliest_covering_period_is_reported(make_claim):
    later = make_period(start=date(2009, 2, 1), end=None)
    earlier = make_period(start=date(2009, 1, 1), end=date(2009, 12, 31))
    result = check_eligibility(make_claim(), [later, earlier])
    assert result.covering_period == earlier