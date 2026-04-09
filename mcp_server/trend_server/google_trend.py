import os
from dotenv import load_dotenv
import json
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from integrations_api.google_trend import SerpAPIClient
from mcp_server.trend_server.helpers import format_trends_output, format_trending_now_output


base_path = Path(__file__).resolve()
working_dir = base_path.parent

# Load SERP_API_KEY
load_dotenv()
serp_api_key = os.getenv("SERP_API_KEY", "")
serp_client = SerpAPIClient(api_key=serp_api_key)
mcp = FastMCP("GoogleTrend")

# Define tools
@mcp.tool()
def search_term(query: str, data_type: str):
    result = serp_client.search(
        query = query,
        engine = "google_trends",
        data_type = data_type,
        geo = "VN"
        )
    result = format_trends_output(
        result,
        data_type
    )
    return result

@mcp.tool()
def get_trends(category_id: int, location: str = "VN", hours: int = 24):
    result = serp_client.search_trend(
          engine = "google_trends_trending_now",
          location = location,
          hours = hours,
          category_id = category_id
     )
    result = format_trending_now_output(result)
    return result

@mcp.tool()
def list_categories() -> dict[str, int]:
    category_map = {
    "Autos and Vehicles": 1,
    "Beauty and Fashion": 2,
    "Business and Finance": 3,
    "Climate": 20,
    "Entertainment": 4,
    "Food and Drink": 5,
    "Games": 6,
    "Health": 7,
    "Hobbies and Leisure": 8,
    "Jobs and Education": 9,
    "Law and Government": 10,
    "Other": 11,
    "Pets and Animals": 13,
    "Politics": 14,
    "Science": 15,
    "Shopping": 16,
    "Sports": 17,
    "Technology": 18,
    "Travel and Transportation": 19
    }
    return category_map

if __name__ == "__main__":
    mcp.run()
