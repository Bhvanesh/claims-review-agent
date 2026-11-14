from sqlalchemy.engine import make_url

def require_test_database(url: str) -> None:
    name = make_url(url).database or ""
    if not name.endswith("_test"):
        raise RuntimeError(f"refusing to run: database '{name}' does not end with '_test'")