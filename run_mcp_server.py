# coding: utf-8
# Launch the OpenManus MCP server.
# Usage:
#   stdio mode (local):  python run_mcp_server.py
#   SSE mode (Railway):  python run_mcp_server.py --transport sse
from app.mcp.server import MCPServer, parse_args


if __name__ == "__main__":
    args = parse_args()

    # Create and run server (maintaining original flow)
    server = MCPServer()
    server.run(transport=args.transport)
