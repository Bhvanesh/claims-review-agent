import pytest
from sqlalchemy.orm import Session

from claims_agent.db.repositories.in_memory import (
    InMemoryClaimRepository,
    InMemoryCoverageRepository,
)
from claims_agent.db.repositories.postgres import (
    PostgresClaimRepository,
    PostgresCoverageRepository,
)
from claims_agent.domain.coverage import EligibilityStatus
from claims_agent.domain.decision import DecisionType
from claims_agent.synthetic.cases import LabeledCase, Scenario
from claims_agent.synthetic.generator import TENANT_ID, generate_cases
from claims_agent.synthetic.loader import load_cases, reset_synthetic_tenant
from claims_agent.tools.duplicates import check_duplicates
from claims_agent.tools.eligibility import check_member_eligibility


@pytest.fixture(params=["memory", "postgres"])
def repos(request):
    if request.param == "memory":
        return InMemoryClaimRepository(), InMemoryCoverageRepository()
    session = request.getfixturevalue("pg_session")
    return PostgresClaimRepository(session), PostgresCoverageRepository(session)


def decide(case: LabeledCase, claims, coverage) -> DecisionType:
    eligibility = check_member_eligibility(coverage, case.claim)
    if eligibility.status is EligibilityStatus.NO_COVERAGE_RECORD:
        return DecisionType.PEND
    if eligibility.status is EligibilityStatus.NOT_COVERED_ON_DATE:
        return DecisionType.DENY
    if check_duplicates(claims, case.claim):
        return DecisionType.DENY
    return DecisionType.APPROVE


def test_summary_counts_match_the_cases(repos):
    claims, coverage = repos
    cases = generate_cases(seed=1, per_scenario=5)
    summary = load_cases(cases, claims, coverage)
    assert summary.claims == sum(len(c.history) for c in cases)
    assert summary.coverage_periods == sum(len(c.coverage) for c in cases)


def test_claim_under_review_is_not_loaded(repos):
    claims, coverage = repos
    cases = generate_cases(seed=1, per_scenario=3)
    load_cases(cases, claims, coverage)
    for case in cases:
        assert claims.get(TENANT_ID, case.claim.claim_id) is None, case.case_id


def test_tools_reproduce_every_label_from_loaded_data(repos):
    claims, coverage = repos
    cases = generate_cases(seed=2, per_scenario=10)
    load_cases(cases, claims, coverage)
    for case in cases:
        assert decide(case, claims, coverage) is case.expected_decision, case.case_id


def test_other_tenants_are_rejected_before_anything_is_inserted(repos, make_period):
    claims, coverage = repos
    cases = generate_cases(seed=1, per_scenario=1)
    good = cases[0]
    bad = cases[1].model_copy(update={"coverage": (make_period(tenant_id="t-other"),)})
    with pytest.raises(ValueError):
        load_cases([good, bad], claims, coverage)
    assert coverage.list_for_patient(TENANT_ID, good.claim.patient_ref) == []


def test_reset_removes_only_the_synthetic_tenant(pg_engine, clean_tables, make_claim, make_period):
    cases = generate_cases(seed=1, per_scenario=3)
    duplicate_case = next(c for c in cases if c.scenario is Scenario.DUPLICATE_CLAIM)
    with Session(pg_engine) as writer:
        claims = PostgresClaimRepository(writer)
        coverage = PostgresCoverageRepository(writer)
        load_cases(cases, claims, coverage)
        claims.add(make_claim(tenant_id="t-other"))
        coverage.add(make_period(tenant_id="t-other"))
        writer.commit()
    with Session(pg_engine) as resetter:
        reset_synthetic_tenant(resetter)
        resetter.commit()
    with Session(pg_engine) as reader:
        claims = PostgresClaimRepository(reader)
        coverage = PostgresCoverageRepository(reader)
        patient = duplicate_case.claim.patient_ref
        assert claims.list_for_patient(TENANT_ID, patient) == []
        assert coverage.list_for_patient(TENANT_ID, patient) == []
        assert len(claims.list_for_patient("t-other", "p-1")) == 1
        assert len(coverage.list_for_patient("t-other", "p-1")) == 1


def test_loading_twice_replaces_instead_of_duplicating(pg_engine, clean_tables):
    cases = generate_cases(seed=1, per_scenario=3)
    for _ in range(2):
        with Session(pg_engine) as session:
            reset_synthetic_tenant(session)
            load_cases(
                cases, PostgresClaimRepository(session), PostgresCoverageRepository(session)
            )
            session.commit()
    covered_case = next(c for c in cases if c.scenario is Scenario.COVERED_NO_DUPLICATE)
    with Session(pg_engine) as reader:
        periods = PostgresCoverageRepository(reader).list_for_patient(
            TENANT_ID, covered_case.claim.patient_ref
        )
    assert len(periods) == len(covered_case.coverage)