import pytest

from claims_agent.db.saftey import require_test_database


def test_accepts_database_ending_in_test():
    require_test_database("postgresql+psycopg://u:p@localhost:5432/claims_test")


def test_rejects_other_database_name():
    with pytest.raises(RuntimeError):
        require_test_database("postgresql+psycopg://u:p@localhost:5432/claims_agent")


def test_rejects_url_without_database_name():
    with pytest.raises(RuntimeError):
        require_test_database("postgresql+psycopg://u:p@localhost:5432")