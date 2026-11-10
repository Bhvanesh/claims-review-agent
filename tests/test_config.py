import pytest
from pydantic import ValidationError

from claims_agent.core.config import Settings

def test_defaults():
    settings = Settings(_env_file=None)
    assert settings.environment == "local"
    assert settings.log_level == "INFO"

def test_env_override(monkeypatch):
    monkeypatch.setenv("CLAIMS_ENVIRONMENT", "production")
    settings = Settings(_env_file = None)
    assert settings.environment == "production"

def test_invalid_value_rejected(monkeypatch):
    monkeypatch.setenv("CLAIMS_ENVIRONMENT", "staging")
    with pytest.raises(ValidationError):
        Settings(_env_file=None)
        