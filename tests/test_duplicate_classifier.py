from datetime import date
from decimal import Decimal

import pytest

from claims_agent.db.repositories.in_memory import InMemoryClaimRepository
from claims_agent.domain.claim import ClaimLine
from claims_agent.tools.duplicate_classifier import (
    DuplicateStatus,
    classify_claim_duplicates,
    classify_duplicates,
)


def line(code: str = "99213", amount: str = "100.00", modifier: str | None = None) -> ClaimLine:
    return ClaimLine(
        procedure_code=code,
        diagnosis_code="E119",
        charge_amount=Decimal(amount),
        modifier=modifier,
    )


def test_identical_line_is_an_exact_duplicate(make_claim):
    new = make_claim(claim_id="c-2", place_of_service="11")
    old = make_claim(claim_id="c-1", place_of_service="11")
    report = classify_duplicates(new, [old])
    assert report.status is DuplicateStatus.EXACT
    assert len(report.matches) == 1
    match = report.matches[0]
    assert (match.line_no, match.earlier_claim_id, match.earlier_line_no) == (1, "c-1", 1)
    assert match.kind == "exact"
    assert match.differing_fields == ()


def test_different_charge_makes_it_a_suspect(make_claim):
    new = make_claim(claim_id="c-2", charge_amount=Decimal("100.00"))
    old = make_claim(claim_id="c-1", charge_amount=Decimal("120.00"))
    report = classify_duplicates(new, [old])
    assert report.status is DuplicateStatus.SUSPECT
    assert report.matches[0].differing_fields == ("charge_amount",)


def test_different_place_of_service_makes_it_a_suspect(make_claim):
    new = make_claim(claim_id="c-2", place_of_service="11")
    old = make_claim(claim_id="c-1", place_of_service="22")
    report = classify_duplicates(new, [old])
    assert report.status is DuplicateStatus.SUSPECT
    assert report.matches[0].differing_fields == ("place_of_service",)


def test_both_differences_are_reported_in_a_fixed_order(make_claim):
    new = make_claim(claim_id="c-2", place_of_service="11", charge_amount=Decimal("100.00"))
    old = make_claim(claim_id="c-1", place_of_service="22", charge_amount=Decimal("120.00"))
    report = classify_duplicates(new, [old])
    assert report.matches[0].differing_fields == ("place_of_service", "charge_amount")


@pytest.mark.parametrize(
    "new_modifier, old_modifier", [(None, "LT"), ("LT", "RT"), ("LT", None)]
)
def test_different_modifier_is_not_a_duplicate(make_claim, new_modifier, old_modifier):
    new = make_claim(claim_id="c-2", modifier=new_modifier)
    old = make_claim(claim_id="c-1", modifier=old_modifier)
    report = classify_duplicates(new, [old])
    assert report.status is DuplicateStatus.NONE
    assert report.matches == ()


def test_different_procedure_is_not_a_duplicate(make_claim):
    new = make_claim(claim_id="c-2", procedure_code="99213")
    old = make_claim(claim_id="c-1", procedure_code="85025")
    assert classify_duplicates(new, [old]).status is DuplicateStatus.NONE


@pytest.mark.parametrize(
    "changes",
    [
        {"provider_ref": "pr-2"},
        {"service_date": date(2009, 3, 2)},
        {"patient_ref": "p-2"},
        {"tenant_id": "t-2"},
    ],
)
def test_context_must_match(make_claim, changes):
    new = make_claim(claim_id="c-2")
    old = make_claim(claim_id="c-1", **changes)
    assert classify_duplicates(new, [old]).status is DuplicateStatus.NONE


def test_claim_is_not_its_own_duplicate(make_claim):
    claim = make_claim(claim_id="c-1")
    assert classify_duplicates(claim, [claim]).status is DuplicateStatus.NONE


def test_all_lines_exact_means_exact(make_claim):
    new = make_claim(claim_id="c-2", lines=[line("99213"), line("85025", "20.00")])
    old = make_claim(claim_id="c-1", lines=[line("85025", "20.00"), line("99213")])
    report = classify_duplicates(new, [old])
    assert report.status is DuplicateStatus.EXACT
    assert [(m.line_no, m.earlier_line_no) for m in report.matches] == [(1, 2), (2, 1)]


def test_only_some_lines_matching_makes_it_a_suspect(make_claim):
    new = make_claim(claim_id="c-2", lines=[line("99213"), line("85025", "20.00")])
    old = make_claim(claim_id="c-1", lines=[line("99213")])
    report = classify_duplicates(new, [old])
    assert report.status is DuplicateStatus.SUSPECT
    assert [m.line_no for m in report.matches] == [1]


def test_exact_line_plus_suspect_line_is_a_suspect(make_claim):
    new = make_claim(claim_id="c-2", lines=[line("99213"), line("85025", "20.00")])
    old = make_claim(claim_id="c-1", lines=[line("99213"), line("85025", "25.00")])
    report = classify_duplicates(new, [old])
    assert report.status is DuplicateStatus.SUSPECT
    assert [m.kind for m in report.matches] == ["exact", "suspect"]


def test_matches_are_sorted_whatever_the_history_order(make_claim):
    new = make_claim(claim_id="c-9")
    first = make_claim(claim_id="c-1")
    second = make_claim(claim_id="c-2")
    report = classify_duplicates(new, [second, first])
    assert report.status is DuplicateStatus.EXACT
    assert [m.earlier_claim_id for m in report.matches] == ["c-1", "c-2"]


def test_repository_wrapper_reads_history_for_the_claims_tenant(make_claim):
    repo = InMemoryClaimRepository()
    repo.add(make_claim(claim_id="c-1"))
    repo.add(make_claim(claim_id="c-3", tenant_id="t-2"))
    report = classify_claim_duplicates(repo, make_claim(claim_id="c-2"))
    assert [m.earlier_claim_id for m in report.matches] == ["c-1"]