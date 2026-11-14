from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from claims_agent.db.repositories.postgres import PostgresClaimRepository
from claims_agent.domain.claim import Claim, ClaimLine


def test_claim_round_trips_through_the_database(pg_engine, clean_tables):
    claim = Claim(
        claim_id="c-1",
        tenant_id="t-1",
        patient_ref="p-1",
        provider_ref="pr-1",
        service_date=date(2009, 3, 1),
        lines=[
            ClaimLine(
                procedure_code="99213", diagnosis_code="E119", charge_amount=Decimal("100.50")
            ),
            ClaimLine(
                procedure_code="85025", diagnosis_code="E119", charge_amount=Decimal("20.00")
            ),
        ],
    )
    with Session(pg_engine) as writer:
        PostgresClaimRepository(writer).add(claim)
        writer.commit()
    with Session(pg_engine) as reader:
        loaded = PostgresClaimRepository(reader).get("t-1", "c-1")
    assert loaded == claim


def test_other_tenant_cannot_see_committed_claim(pg_engine, clean_tables, make_claim):
    with Session(pg_engine) as writer:
        PostgresClaimRepository(writer).add(make_claim(tenant_id="t-1"))
        writer.commit()
    with Session(pg_engine) as reader:
        repo = PostgresClaimRepository(reader)
        assert repo.get("t-2", "c-1") is None
        assert repo.list_for_tenant("t-2") == []
        assert len(repo.list_for_tenant("t-1")) == 1