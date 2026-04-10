import os
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from integrations_api.google_trend import SerpAPIClient
from mcp_servers.trends_servers.helpers import format_trends_output, format_trending_now_output


mcp = FastMCP("Tools")

@mcp.tool()
def get_all_tools_informations():
    """
    This tool is used to get all tools information in the MCP server.
    """
    list_of_tools = ["controlling_planning", "fetch_trends", "find_healthcare_providers"]
    return list_of_tools





