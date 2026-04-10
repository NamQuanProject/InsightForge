import os
from dotenv import load_dotenv

from mcp.server.fastmcp import FastMCP
from integrations_api.google_trend import SerpAPIClient
from mcp_servers.trends_servers.helpers import format_trends_output, format_trending_now_output

# Load SERP_API_KEY
load_dotenv()
serp_api_key = os.getenv("SERP_API_KEY", "")
serp_client = SerpAPIClient(api_key=serp_api_key)
mcp = FastMCP("GoogleTrend")

# Define tools
@mcp.tool()
def search_term(query: str, data_type: str, date: str):
    """
    Query is a Search Term for its trending.
    Data_Type is of those values:
    - TIMESERIES: Interest over time.
    - GEO_MAP: Compared break down for each region.
    - GEO_MAP_0: Interest over region.
    - RELATED_QUERIES - Related queries (Topics)
    Date if of those values:
    - now 1-H - Past hour
    - now 4-H - Past 4 hours
    - now 1-d - Past day
    - now 7-d - Past 7 days
    - today 1-m - Past 30 days
    - today 3-m - Past 90 days
    - today 12-m - Past 12 months
    - today 5-y - Past 5 years
    - all - 2004 - present
    """
    # Logic: If data is missing, the agent should try widening the 'date' 
    # or setting 'geo' to empty (Worldwide).
    result = serp_client.search_for_term(
        query = query,
        engine = "google_trends",
        data_type = data_type,
        geo = "VN",
        date = date
        )
    result = format_trends_output(
        result,
        data_type
    )
    return result

@mcp.tool()
def get_trends(category_id: int, location: str = "VN", hours: int = 24):
    """
    This tool is used to get trending search now in Hours.
    Hours can be: 
    - 4 (Past 4 hours)
    - 24 (Past 24 hours)
    - 48 (Past 48 hours)
    - 168 (Past 7 days).
    """
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
    """
    List of categories mapped into Category ID for searching parameters.
    """
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
    mcp.run(transport = "stdio")