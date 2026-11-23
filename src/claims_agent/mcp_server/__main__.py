from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy.orm import Session

from claims_agent.core.config import get_settings
from claims_agent.db.repositories.postgres import (
    PostgresClaimRepository,
    PostgresCoverageRepository,
)
from claims_agent.db.session import make_engine
from claims_agent.mcp_server.config import McpServerSettings
from claims_agent.mcp_server.server import build_server
from claims_agent.mcp_server.service import ClaimTools

def main() -> None:
    tenant_id = McpServerSettings().tenant_id
    engine = make_engine(get_settings().database_url.get_secret_values())

    @contextmanager
    def open_tools() -> Iterator[ClaimTools]:
        with Session(engine) as session:
            yield ClaimTools(
                tenant_id,
                PostgresClaimRepository(session),
                PostgresCoverageRepository(session),
            )
    server = build_server(open_tools)
    server.run(transport = "streamable-http", host="127.0.0.1", port=8000)

if __name__ == "__main__":
    main()