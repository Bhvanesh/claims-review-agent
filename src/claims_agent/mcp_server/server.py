from collections.abc import Callable
from contextlib import AbstractContextManager
from typing import Any

from mcp.server.mcpserver import MCPServer

from claims_agent.mcp_server.schemas import ClaimInput
from claims_agent.mcp_server.service import ClaimTools

ToolsProvider = Callable[[], AbstractContextManager[ClaimTools]]


def build_server(open_tools: ToolsProvider) -> MCPServer:
    mcp = MCPServer("claims-tools")

    @mcp.tool()
    def check_duplicates(claim: ClaimInput) -> dict[str, Any]:
        """Find earlier claims for the same patient that look like duplicates of this claim.

        Two claims count as possible duplicates when they share patient, provider,
        service date and at least one procedure code.
        """
        with open_tools() as tools:
            return tools.check_duplicates(claim)

    @mcp.tool()
    def check_eligibility(claim: ClaimInput) -> dict[str, Any]:
        """Check whether the patient had coverage on the claim's service date.

        Returns covered, not_covered_on_date, or no_coverage_record.
        """
        with open_tools() as tools:
            return tools.check_eligibility(claim)

    return mcp