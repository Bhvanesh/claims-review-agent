import pytest

from claims_agent.db.repositories.in_memory import InMemoryClaimRepository
from claims_agent.domain.errors import DuplicateClaimError


def test_add_and_get(make_claim):
    repo = InMemoryClaimRepository()
    claim = make_claim()
    repo.add(claim)
    assert repo.get("t-1", "c-1") == claim


def test_get_missing_returns_none():
    assert InMemoryClaimRepository().get("t-1", "nope") is None


def test_other_tenant_cannot_read_claim(make_claim):
    repo = InMemoryClaimRepository()
    repo.add(make_claim(tenant_id="t-1"))
    assert repo.get("t-2", "c-1") is None


def test_list_returns_only_own_tenant(make_claim):
    repo = InMemoryClaimRepository()
    repo.add(make_claim(claim_id="c-1", tenant_id="t-1"))
    repo.add(make_claim(claim_id="c-2", tenant_id="t-2"))
    assert [c.claim_id for c in repo.list_for_tenant("t-1")] == ["c-1"]


def test_same_claim_id_allowed_in_different_tenants(make_claim):
    repo = InMemoryClaimRepository()
    repo.add(make_claim(tenant_id="t-1"))
    repo.add(make_claim(tenant_id="t-2"))
    assert repo.get("t-1", "c-1") is not None
    assert repo.get("t-2", "c-1") is not None


def test_duplicate_in_same_tenant_rejected(make_claim):
    repo = InMemoryClaimRepository()
    repo.add(make_claim())
    with pytest.raises(DuplicateClaimError):
        repo.add(make_claim())