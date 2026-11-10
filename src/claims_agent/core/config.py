from functools import lru_cache
from typing import Literal
from pydantic import SecretStr

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="CLAIMS_", extra="ignore")
    app_name: str = "claims-review-agent"
    environment: Literal["local", "test", "production"] = "local"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    database_url: SecretStr

@lru_cache
def get_settings() -> Settings:
    return Settings()



