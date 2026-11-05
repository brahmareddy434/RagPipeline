"""Independent SDK consumer: proves reuse without importing this app's agent/registry."""
import asyncio
import json
import sys
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    params = StdioServerParameters(command=sys.executable, args=["-m", "mcp_servers.policy"],
                                   cwd=str(Path(__file__).resolve().parents[1]))
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as client:
            await client.initialize()
            tools = await client.list_tools()
            result = await client.call_tool("search_policy_documents", {"query": "vehicle damage"})
            print(json.dumps({"consumer": "independent SDK client, not a second human's agent",
                              "tools_list": tools.model_dump(mode="json", by_alias=True),
                              "result": result.model_dump(mode="json", by_alias=True)}, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
