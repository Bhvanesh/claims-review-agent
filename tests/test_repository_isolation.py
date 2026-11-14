import pytest
from datetime import date
from claims_agent.db.repositories.in_memory import InMemoryClaimRepository
from claims_agent.domain.errors import DuplicateClaimError
from claims_agent.db.repositories.postgres import PostgresClaimRepository

@pytest.fixture(params=["memory", "postgres"])
def repo(request):
    if request.param == "memory":
        return InMemoryClaimRepository()
    return PostgresClaimRepository(request.getfixturevalue("pg_session"))


def test_add_and_get(repo, make_claim):
    claim = make_claim()
    repo.add(claim)
    assert repo.get("t-1", "c-1") == claim


def test_get_missing_returns_none(repo):
    assert repo.get("t-1", "nope") is None


def test_other_tenant_cannot_read_claim(repo, make_claim):
    repo.add(make_claim(tenant_id="t-1"))
    assert repo.get("t-2", "c-1") is None


def test_list_returns_only_own_tenant(repo, make_claim):
    repo.add(make_claim(claim_id="c-1", tenant_id="t-1"))
    repo.add(make_claim(claim_id="c-2", tenant_id="t-2"))
    assert [c.claim_id for c in repo.list_for_tenant("t-1")] == ["c-1"]


def test_same_claim_id_allowed_in_different_tenants(repo, make_claim):
    repo.add(make_claim(tenant_id="t-1"))
    repo.add(make_claim(tenant_id="t-2"))
    assert repo.get("t-1", "c-1") is not None
    assert repo.get("t-2", "c-1") is not None


def test_duplicate_in_same_tenant_rejected(repo, make_claim):
    repo.add(make_claim())
    with pytest.raises(DuplicateClaimError):
        repo.add(make_claim())

def test_list_for_patient_filters_and_orders(repo, make_claim):
    repo.add(make_claim(claim_id="c-2", patient_ref="p-1", service_date=date(2009, 5, 1)))
    repo.add(make_claim(claim_id="c-1", patient_ref="p-1", service_date=date(2009, 3, 1)))
    repo.add(make_claim(claim_id="c-3", patient_ref="p-2", service_date=date(2009, 4, 1)))
    assert [c.claim_id for c in repo.list_for_patient("t-1", "p-1")] == ["c-1", "c-2"]


def test_list_for_patient_does_not_cross_tenants(repo, make_claim):
    repo.add(make_claim(claim_id="c-1", tenant_id="t-1", patient_ref="p-1"))
    assert repo.list_for_patient("t-2", "p-1") == []    