from datetime import date
from decimal import Decimal
from collections.abc import Iterator

import pytest
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import Engine, text
from claims_agent.domain.claim import Claim, ClaimLine
from sqlalchemy.orm import Session

from claims_agent.db.models import Base
from claims_agent.db.saftey import require_test_database
from claims_agent.db.session import make_engine
from claims_agent.domain.claim import Claim, ClaimLine 
from claims_agent.domain.coverage import CoveragePeriod


class IntegrationDbSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix = "CLAIMS_", extra="ignore")

    test_database_url: SecretStr | None = None

@pytest.fixture(autouse=True)
def _default_env(monkeypatch):
    monkeypatch.setenv("CLAIMS_DATABASE_URL", "postgresql+psycopg://user:pass@localhost:5432/unused")


@pytest.fixture
def make_claim():
    def _make(
        claim_id: str = "c-1",
        tenant_id: str = "t-1",
        patient_ref: str = "p-1",
        provider_ref: str = "pr-1",
        service_date: date = date(2009, 3, 1),
        procedure_code: str = "99213",
        place_of_service: str | None = None,
        modifier: str | None = None,
        charge_amount: Decimal = Decimal("100.00"),
        lines: list[ClaimLine] | None = None,
    ) -> Claim:
        if lines is None:
            lines = [
                ClaimLine(
                    procedure_code = procedure_code,
                    diagnosis_code ="E119",
                    charge_amount = charge_amount,
                    modifier = modifier,
                )
            ]
        return Claim(
            claim_id=claim_id,
            tenant_id=tenant_id,
            patient_ref=patient_ref,
            provider_ref=provider_ref,
            service_date=service_date,
            place_of_service=place_of_service,
            lines=lines,
        )

    return _make

@pytest.fixture
def make_period():
    def _make(
            tenant_id: str = "t-1",
            patient_ref: str = "p-1",
            start: date = date(2009, 1, 1),
            end: date | None = date(2009,12,31)) -> CoveragePeriod: 
        return CoveragePeriod(tenant_id=tenant_id, patient_ref=patient_ref, start_date=start, end_date=end)
    return _make

def _truncate(engine: Engine) -> None:
    names = ", ".join(table.name for table in Base.metadata.sorted_tables)
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE TABLE {names}"))

@pytest.fixture(scope="session")
def pg_engine() -> Iterator[Engine]:
    url = IntegrationDbSettings().test_database_url
    if url is None:
        pytest.skip("CLAIMS_TEST_DATABASE_URL is not set")
    secret = url.get_secret_value()
    require_test_database(secret)
    engine = make_engine(secret)

    Base.metadata.drop_all(engine)

    Base.metadata.create_all(engine)
    
    yield engine
    engine.dispose()

@pytest.fixture
def clean_tables(pg_engine:Engine) -> Iterator[None]:
    _truncate(pg_engine)
    yield
    _truncate(pg_engine)

@pytest.fixture
def pg_session(pg_engine: Engine, clean_tables: None) -> Iterator[Session]:
    with Session(pg_engine) as session:
        yield session
        session.rollback()

