from claims_agent.db.session import check_connection, make_engine

def test_check_connection_succeeds_on_working_engine():
    assert check_connection(make_engine("sqlite://")) is True

def test_check_connection_fails_on_unreachable_database():
    engine = make_engine("postgresql+psycopg://u:p@127.0.0.1:1/none?connect_timeout=2")
    assert check_connection(engine) is False
