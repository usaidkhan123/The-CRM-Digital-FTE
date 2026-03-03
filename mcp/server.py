"""
MCP Server for the Customer Success agent.
Exposes all tools via a JSON-based protocol over stdin/stdout.
"""

import json
import sys
from mcp.tools import TOOL_REGISTRY


def handle_request(request: dict) -> dict:
    """Process an MCP tool call request."""
    method = request.get("method")

    if method == "tools/list":
        tools = []
        for name, tool_def in TOOL_REGISTRY.items():
            tools.append({
                "name": name,
                "description": tool_def["description"],
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        param_name: {
                            "type": param_def["type"],
                            "description": param_def["description"],
                        }
                        for param_name, param_def in tool_def["parameters"].items()
                    },
                    "required": [
                        param_name
                        for param_name, param_def in tool_def["parameters"].items()
                        if param_def.get("required", False)
                    ],
                },
            })
        return {"result": {"tools": tools}}

    elif method == "tools/call":
        tool_name = request.get("params", {}).get("name")
        arguments = request.get("params", {}).get("arguments", {})

        if tool_name not in TOOL_REGISTRY:
            return {"error": {"code": -32601, "message": f"Unknown tool: {tool_name}"}}

        tool_fn = TOOL_REGISTRY[tool_name]["function"]
        try:
            result = tool_fn(**arguments)
            return {"result": {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}}
        except TypeError as e:
            return {"error": {"code": -32602, "message": f"Invalid parameters: {e}"}}
        except Exception as e:
            return {"error": {"code": -32603, "message": f"Tool execution error: {e}"}}

    elif method == "initialize":
        return {
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {
                    "name": "taskflow-pro-cs-agent",
                    "version": "1.0.0",
                },
            }
        }

    else:
        return {"error": {"code": -32601, "message": f"Unknown method: {method}"}}


def run_server():
    """Run the MCP server reading JSON-RPC from stdin, writing to stdout."""
    print(json.dumps({"jsonrpc": "2.0", "info": "TaskFlow Pro CS Agent MCP Server started"}), flush=True)

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            response = {"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}}
            print(json.dumps(response), flush=True)
            continue

        request_id = request.get("id")
        result = handle_request(request)
        result["jsonrpc"] = "2.0"
        if request_id is not None:
            result["id"] = request_id

        print(json.dumps(result), flush=True)


if __name__ == "__main__":
    run_server()
