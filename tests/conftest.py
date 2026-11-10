from datetime import date
from decimal import Decimal

import pytest

from claims_agent.domain.claim import Claim, ClaimLine

@pytest.fixture
def make_claim():
    def _make(claim_id: str = "c-1", tenant_id: str = "t-1") -> Claim:
        return Claim(
            claim_id = claim_id,
            tenant_id = tenant_id,
            patient_ref = "p-1",
            provider_ref = "pr_1",
            service_date = date(2009, 3, 1),
            lines=[
                ClaimLine(
                    procedure_code="99213",
                    diagnosis_code="E119",
                    charge_amount=Decimal("100.00"),
            )],
        )
    return _make

@pytest.fixture(autouse=True)
def _default_env(monkeypatch):
    monkeypatch.setenv(
        "CLAIMS_DATABASE_URL", "postgresql+psycopg://user:pass@localhost:5432/unused"
    )