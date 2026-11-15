from datetime import date

import pytest

from claims_agent.db.repositories.in_memory import InMemoryClaimRepository
from claims_agent.tools.duplicates import check_duplicates, find_possible_duplicates


def test_same_patient_provider_date_and_procedure_is_flagged(make_claim):
    new = make_claim(claim_id="c-2")
    old = make_claim(claim_id="c-1")
    matches = find_possible_duplicates(new, [old])
    assert [m.claim_id for m in matches] == ["c-1"]
    assert matches[0].matching_procedure_codes == ("99213",)


@pytest.mark.parametrize(
    "changes",
    [
        {"provider_ref": "pr-2"},
        {"service_date": date(2009, 3, 2)},
        {"procedure_code": "85025"},
        {"patient_ref": "p-2"},
    ],
)
def test_any_difference_means_not_a_duplicate(make_claim, changes):
    new = make_claim(claim_id="c-2")
    old = make_claim(claim_id="c-1", **changes)
    assert find_possible_duplicates(new, [old]) == []


def test_claim_is_not_its_own_duplicate(make_claim):
    claim = make_claim(claim_id="c-1")
    assert find_possible_duplicates(claim, [claim]) == []


def test_other_tenant_history_is_ignored(make_claim):
    new = make_claim(claim_id="c-2", tenant_id="t-1")
    other = make_claim(claim_id="c-1", tenant_id="t-2")
    assert find_possible_duplicates(new, [other]) == []


def test_check_duplicates_reads_history_from_repository(make_claim):
    repo = InMemoryClaimRepository()
    repo.add(make_claim(claim_id="c-1"))
    repo.add(make_claim(claim_id="c-3", tenant_id="t-2"))
    matches = check_duplicates(repo, make_claim(claim_id="c-2"))
    assert [m.claim_id for m in matches] == ["c-1"]