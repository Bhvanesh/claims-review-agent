from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class McpServerSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="CLAIMS_MCP_", extra="ignore")

    tenant_id: str = Field(min_length=1, max_length=64)