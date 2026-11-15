from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError

from claims_agent.db.models import CoveragePeriodRow
from claims_agent.db.repositories.in_memory import InMemoryCoverageRepository
from claims_agent.db.repositories.postgres import PostgresCoverageRepository
from claims_agent.domain.coverage import EligibilityStatus
from claims_agent.tools.eligibility import check_member_eligibility


@pytest.fixture(params=["memory", "postgres"])
def coverage_repo(request):
    if request.param == "memory":
        return InMemoryCoverageRepository()
    return PostgresCoverageRepository(request.getfixturevalue("pg_session"))


def test_add_and_list_for_patient(coverage_repo, make_period):
    period = make_period()
    coverage_repo.add(period)
    assert coverage_repo.list_for_patient("t-1", "p-1") == [period]


def test_list_only_returns_the_requested_patient(coverage_repo, make_period):
    coverage_repo.add(make_period(patient_ref="p-1"))
    coverage_repo.add(make_period(patient_ref="p-2"))
    assert len(coverage_repo.list_for_patient("t-1", "p-1")) == 1


def test_list_does_not_cross_tenants(coverage_repo, make_period):
    coverage_repo.add(make_period(tenant_id="t-1"))
    assert coverage_repo.list_for_patient("t-2", "p-1") == []


def test_periods_ordered_by_start_then_end_with_open_ended_last(coverage_repo, make_period):
    a = make_period(start=date(2009, 6, 1), end=None)
    d = make_period(start=date(2009, 1, 1), end=None)
    b = make_period(start=date(2009, 1, 1), end=date(2009, 12, 31))
    c = make_period(start=date(2009, 1, 1), end=date(2009, 3, 31))
    for period in (a, d, b, c):
        coverage_repo.add(period)
    assert coverage_repo.list_for_patient("t-1", "p-1") == [c, b, d, a]


def test_check_member_eligibility_uses_the_repository(make_claim, make_period):
    repo = InMemoryCoverageRepository()
    repo.add(make_period())
    repo.add(make_period(tenant_id="t-2"))
    result = check_member_eligibility(repo, make_claim())
    assert result.status is EligibilityStatus.COVERED


def test_database_rejects_end_before_start(pg_session):
    pg_session.add(
        CoveragePeriodRow(
            tenant_id="t-1",
            patient_ref="p-1",
            start_date=date(2009, 6, 1),
            end_date=date(2009, 5, 31),
        )
    )
    with pytest.raises(IntegrityError):
        pg_session.flush()