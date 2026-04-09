import json
from pathlib import Path
from mcp.server.fastmcp import FastMCP

# Initialize the server
mcp = FastMCP("doctorserver")

# Load Data safely
try:
    doctors: list = json.loads(Path("./data/doctors.json").read_text())
except FileNotFoundError:
    doctors = []  # Fallback if the data file isn't found

@mcp.tool()
def list_doctors(state: str | None = None, city: str | None = None) -> list[dict]:
    """
    Returns a list of doctors practicing in a specific location.
    The search is case-insensitive.
    """
    if not state and not city:
        return [{"error": "Please provide a state or a city."}]

    target_state = state.strip().lower() if state else None
    target_city = city.strip().lower() if city else None

    return [
        doc for doc in doctors
        if (not target_state or doc.get("address", {}).get("state", "").lower() == target_state) and
           (not target_city or doc.get("address", {}).get("city", "").lower() == target_city)
    ]

if __name__ == "__main__":
    mcp.run(transport="stdio")