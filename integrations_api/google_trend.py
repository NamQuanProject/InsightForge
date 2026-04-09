import os
import serpapi
from dotenv import load_dotenv
from typing import List, Dict, Optional
import json
from pathlib import Path

base_path = Path(__file__).resolve()
working_dir = base_path.parent

class SerpAPIClient():
    def __init__(self, api_key):
        self.api_key = api_key
        # Initialize a SerpAPI client
        self.client = serpapi.Client(api_key=self.api_key)
    
    def search(self, query: str = "", engine = "google_trends", data_type: str = "",  geo: str = None):
        allowed_data_type = {
            "TIMESERIES" : "interest_over_time",
            "GEO_MAP": "compared_breakdown_by_region",
            "GEO_MAP_0": "interest_by_region",
            "RELATED_TOPICS": "related_topics",
            "RELATED_QUERIES": "related_queries"
        }
        if data_type not in allowed_data_type:
            print(f"Data Type not supported")
            return []
        params = {
            "data_type": data_type,
            "engine": engine
        }
        try:
            if geo:
                params["geo"] = geo
            else:
                results = self.client.search(
                    **params
                )
            return results[allowed_data_type[data_type]]
        except Exception as e:
            print(f"Error: {e}")
            return {}

    def search_trend(self, category_id: int = None, engine: str = "google_trends_trending_now", location: str = "VN", hours : int = 24):
        try: 
            params = {
                "engine" : engine,
                "geo" : location
            }
            if hours:
                params["hours"] = hours
            if category_id:
                params["category_id"] = category_id
            result = self.client.search(
                **params
            )
            return result["trending_searches"]
        except Exception as e:
            print(f"Errors: {e}")
            return []

if __name__ == "__main__":
    # Load Env file
    load_dotenv()
    serp_api_key = os.getenv("SERP_API_KEY", "")

    serp_client = SerpAPIClient(api_key=serp_api_key)
    query = "Bóng đá"

    # Test each trending data type with query term
    test_data_types = ["TIMESERIES", "GEO_MAP", "GEO_MAP_0", "RELATED_TOPICS", "RELATED_QUERIES"]
    for data_type in test_data_types:
        search_result = serp_client.search(
            query = query,
            engine = "google_trends",
            data_type = data_type
        )
        print(f"\n\nSearch result for {data_type}: ")
        print(f"\n {search_result}")
        # path = os.path.join(working_dir, f"{data_type}_query_search.json")
        result_path =  working_dir / "results"
        if not result_path.exists():
            os.makedirs(str(working_dir / "results"))
        path = working_dir / "results" / f"{data_type}_query_search.json"

        with open(path, "w", encoding = "utf-8") as f:
            json.dump(search_result, f, ensure_ascii = False, indent = 4)
    
    # Test trending now search:
    trending_search = serp_client.search_trend()
    trending_path = working_dir / "results" / "trending_searches.json"
    with open(trending_path, "w", encoding = "utf-8") as f:
            json.dump(trending_search, f, ensure_ascii = False, indent = 4)
