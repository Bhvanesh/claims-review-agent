from collections import Counter

import pytest
from pydantic import ValidationError

from claims_agent.domain.coverage import EligibilityStatus
from claims_agent.domain.decision import DecisionType
from claims_agent.synthetic.cases import EXPECTED_DECISION, LabeledCase, Scenario
from claims_agent.synthetic.generator import generate_cases
from claims_agent.tools.duplicates import find_possible_duplicates
from claims_agent.tools.eligibility import check_eligibility


def reference_decision(case: LabeledCase) -> DecisionType:
    eligibility = check_eligibility(case.claim, case.coverage)
    if eligibility.status is EligibilityStatus.NO_COVERAGE_RECORD:
        return DecisionType.PEND
    if eligibility.status is EligibilityStatus.NOT_COVERED_ON_DATE:
        return DecisionType.DENY
    if find_possible_duplicates(case.claim, case.history):
        return DecisionType.DENY
    return DecisionType.APPROVE


def test_same_seed_gives_identical_cases():
    assert generate_cases(seed=1, per_scenario=5) == generate_cases(seed=1, per_scenario=5)


def test_different_seed_gives_different_cases():
    assert generate_cases(seed=1, per_scenario=5) != generate_cases(seed=2, per_scenario=5)


def test_each_scenario_appears_the_requested_number_of_times():
    counts = Counter(case.scenario for case in generate_cases(seed=1, per_scenario=6))
    assert counts == {scenario: 6 for scenario in Scenario}


def test_case_ids_and_claim_ids_are_unique():
    cases = generate_cases(seed=3, per_scenario=10)
    case_ids = [c.case_id for c in cases]
    claim_ids = [c.claim.claim_id for c in cases]
    claim_ids += [earlier.claim_id for c in cases for earlier in c.history]
    assert len(set(case_ids)) == len(case_ids)
    assert len(set(claim_ids)) == len(claim_ids)


def test_every_case_has_its_own_patient():
    patients = [c.claim.patient_ref for c in generate_cases(seed=3, per_scenario=10)]
    assert len(set(patients)) == len(patients)


def test_history_and_coverage_belong_to_the_claims_patient():
    for case in generate_cases(seed=4, per_scenario=10):
        for earlier in case.history:
            assert earlier.patient_ref == case.claim.patient_ref, case.case_id
            assert earlier.tenant_id == case.claim.tenant_id, case.case_id
        for period in case.coverage:
            assert period.patient_ref == case.claim.patient_ref, case.case_id
            assert period.tenant_id == case.claim.tenant_id, case.case_id


def test_labels_agree_with_the_rules():
    for case in generate_cases(seed=5, per_scenario=40):
        assert reference_decision(case) is case.expected_decision, case.case_id


def test_duplicate_scenario_has_a_flagged_earlier_claim():
    for case in generate_cases(seed=6, per_scenario=20):
        if case.scenario is Scenario.DUPLICATE_CLAIM:
            assert find_possible_duplicates(case.claim, case.history), case.case_id


def test_expected_decision_must_match_scenario():
    claim = generate_cases(seed=1, per_scenario=1)[0].claim
    with pytest.raises(ValidationError):
        LabeledCase(
            case_id="x",
            scenario=Scenario.NO_COVERAGE_RECORD,
            expected_decision=DecisionType.DENY,
            claim=claim,
        )


def test_every_scenario_has_an_expected_decision():
    assert set(EXPECTED_DECISION) == set(Scenario)