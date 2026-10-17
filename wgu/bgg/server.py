"""Compatibility entry point for the single MCP implementation."""
from ..bgg_mcp import create_server as build_server, main

if __name__ == "__main__":
    main()
