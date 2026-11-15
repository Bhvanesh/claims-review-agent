import random
from collections.abc import Callable
from datetime import date, timedelta
from decimal import Decimal

from claims_agent.domain.claim import Claim, ClaimLine
from claims_agent.domain.coverage import CoveragePeriod
from claims_agent.synthetic.cases import EXPECTED_DECISION, LabeledCase, Scenario

TENANT_ID = "t-synth"
PROCEDURE_CODES = ("99213", "99214", "85025", "80053", "71046")
DIAGNOSIS_CODES = ("E119", "I10", "J069", "M545")
YEAR_START = date(2009, 1, 1)


def _random_line(rng: random.Random, procedure_code: str | None = None) -> ClaimLine:
    cents = rng.randrange(2_000, 50_000)
    if procedure_code is None:
        procedure_code = rng.choice(PROCEDURE_CODES)
    return ClaimLine(
        procedure_code=procedure_code,
        diagnosis_code=rng.choice(DIAGNOSIS_CODES),
        charge_amount=Decimal(cents) / 100,
    )


def _base_claim(rng: random.Random, n: int) -> Claim:
    return Claim(
        claim_id=f"clm-{n:04d}",
        tenant_id=TENANT_ID,
        patient_ref=f"p-{n:04d}",
        provider_ref=f"pr-{rng.randrange(1, 21):03d}",
        service_date=YEAR_START + timedelta(days=rng.randrange(365)),
        lines=[_random_line(rng) for _ in range(rng.randrange(1, 4))],
    )


def _covering_period(rng: random.Random, claim: Claim) -> CoveragePeriod:
    shape = rng.choice(("inside", "starts_on_date", "open_ended"))
    if shape == "starts_on_date":
        start = claim.service_date
    else:
        start = claim.service_date - timedelta(days=rng.randrange(1, 300))
    if shape == "open_ended":
        end = None
    else:
        end = claim.service_date + timedelta(days=rng.randrange(1, 300))
    return CoveragePeriod(
        tenant_id=claim.tenant_id,
        patient_ref=claim.patient_ref,
        start_date=start,
        end_date=end,
    )


def _non_covering_period(rng: random.Random, claim: Claim) -> CoveragePeriod:
    gap = timedelta(days=rng.randrange(1, 200))
    length = timedelta(days=rng.randrange(30, 300))
    if rng.choice(("ended_before", "starts_after")) == "ended_before":
        end = claim.service_date - gap
        start = end - length
    else:
        start = claim.service_date + gap
        end = start + length
    return CoveragePeriod(
        tenant_id=claim.tenant_id,
        patient_ref=claim.patient_ref,
        start_date=start,
        end_date=end,
    )


def _near_miss(rng: random.Random, n: int, claim: Claim) -> Claim:
    if rng.choice(("other_provider", "other_date")) == "other_provider":
        provider_ref = claim.provider_ref + "-b"
        service_date = claim.service_date
    else:
        provider_ref = claim.provider_ref
        service_date = claim.service_date - timedelta(days=rng.randrange(1, 60))
    return Claim(
        claim_id=f"clm-{n:04d}-h1",
        tenant_id=claim.tenant_id,
        patient_ref=claim.patient_ref,
        provider_ref=provider_ref,
        service_date=service_date,
        lines=[_random_line(rng, claim.lines[0].procedure_code)],
    )


def _earlier_duplicate(rng: random.Random, n: int, claim: Claim) -> Claim:
    return Claim(
        claim_id=f"clm-{n:04d}-h1",
        tenant_id=claim.tenant_id,
        patient_ref=claim.patient_ref,
        provider_ref=claim.provider_ref,
        service_date=claim.service_date,
        lines=[_random_line(rng, claim.lines[0].procedure_code)],
    )


def _covered_no_duplicate(rng: random.Random, n: int) -> LabeledCase:
    claim = _base_claim(rng, n)
    history = (_near_miss(rng, n, claim),) if rng.random() < 0.5 else ()
    scenario = Scenario.COVERED_NO_DUPLICATE
    return LabeledCase(
        case_id=f"case-{n:04d}",
        scenario=scenario,
        expected_decision=EXPECTED_DECISION[scenario],
        claim=claim,
        history=history,
        coverage=(_covering_period(rng, claim),),
    )


def _duplicate_claim(rng: random.Random, n: int) -> LabeledCase:
    claim = _base_claim(rng, n)
    scenario = Scenario.DUPLICATE_CLAIM
    return LabeledCase(
        case_id=f"case-{n:04d}",
        scenario=scenario,
        expected_decision=EXPECTED_DECISION[scenario],
        claim=claim,
        history=(_earlier_duplicate(rng, n, claim),),
        coverage=(_covering_period(rng, claim),),
    )


def _not_covered_on_date(rng: random.Random, n: int) -> LabeledCase:
    claim = _base_claim(rng, n)
    scenario = Scenario.NOT_COVERED_ON_DATE
    return LabeledCase(
        case_id=f"case-{n:04d}",
        scenario=scenario,
        expected_decision=EXPECTED_DECISION[scenario],
        claim=claim,
        coverage=(_non_covering_period(rng, claim),),
    )


def _no_coverage_record(rng: random.Random, n: int) -> LabeledCase:
    claim = _base_claim(rng, n)
    scenario = Scenario.NO_COVERAGE_RECORD
    return LabeledCase(
        case_id=f"case-{n:04d}",
        scenario=scenario,
        expected_decision=EXPECTED_DECISION[scenario],
        claim=claim,
    )


_BUILDERS: dict[Scenario, Callable[[random.Random, int], LabeledCase]] = {
    Scenario.COVERED_NO_DUPLICATE: _covered_no_duplicate,
    Scenario.DUPLICATE_CLAIM: _duplicate_claim,
    Scenario.NOT_COVERED_ON_DATE: _not_covered_on_date,
    Scenario.NO_COVERAGE_RECORD: _no_coverage_record,
}


def generate_cases(seed: int = 7, per_scenario: int = 25) -> list[LabeledCase]:
    if per_scenario < 1:
        raise ValueError("per_scenario must be at least 1")
    rng = random.Random(seed)
    cases: list[LabeledCase] = []
    number = 0
    for _ in range(per_scenario):
        for scenario in Scenario:
            number += 1
            cases.append(_BUILDERS[scenario](rng, number))
    return cases