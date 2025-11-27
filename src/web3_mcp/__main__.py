"""
Entry point for running MCP server
"""

import os
import sys

from .server import init_server


def main() -> None:
    """Run MCP server"""
    endpoint = os.environ.get("ANKR_ENDPOINT")  # Optional, SDK uses default
    private_key = os.environ.get("ANKR_PRIVATE_KEY") or os.environ.get("ANKR_API_KEY")

    if not private_key:
        print("Error: ANKR_PRIVATE_KEY or ANKR_API_KEY environment variable is not set", file=sys.stderr)
        sys.exit(1)

    mcp = init_server(
        name="Ankr MCP",
        endpoint=endpoint,
        private_key=private_key,
    )
    mcp.run()


if __name__ == "__main__":
    main()
