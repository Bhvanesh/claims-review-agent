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


class IntegrationDbSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix = "CLAIMS_", extra="ignore")

    test_database_url: SecretStr | None = None

@pytest.fixture(autouse=True)
def _default_env(monkeypatch):
    monkeypatch.setenv("CLAIMS_DATABASE_URL", "postgresql+psycopg://user:pass@localhost:5432/unused")


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

def _truncate(engine: Engine) -> None:
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE claim_lines, claims"))


@pytest.fixture(scope="session")
def pg_engine() -> Iterator[Engine]:
    url = IntegrationDbSettings().test_database_url
    if url is None:
        pytest.skip("CLAIMS_TEST_DATABASE_URL is not set")
    secret = url.get_secret_value()
    require_test_database(secret)
    engine = make_engine(secret)
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

