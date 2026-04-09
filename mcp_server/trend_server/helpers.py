import json

def format_trends_output(data, data_type: str) -> str:
    """Formats Google Trends data for better agent readability."""
    if not data:
        return "No data found for this trend query."

    # Handle Timeseries (Interest over time)
    if data_type == "TIMESERIES":
        # Extracts date and the value for the primary query
        header = "| Date | Interest Score |"
        rows = [f"| {item['date']} | {item['values'][0]['extracted_value']} |" 
                for item in data.get('timeline_data', [])[-10:]] # Get last 10 points
        return "### Interest Over Time\n" + header + "\n|---|---|\n" + "\n".join(rows)

    # Handle Related Queries
    elif data_type == "RELATED_QUERIES":
        output = "### Related Queries\n"
        for category in ['top', 'rising']:
            queries = [f"- {q['query']} ({q['value']})" for q in data.get(category, [])[:5]]
            output += f"**{category.capitalize()}:**\n" + "\n".join(queries) + "\n"
        return output

    # Handle Related Topics
    elif data_type == "RELATED_TOPICS":
        output = "### Related Topics\n"
        for category in ['top', 'rising']:
            topics = [f"- {t['topic']['title']} [{t['topic']['type']}] ({t['value']})" 
                      for t in data.get(category, [])[:5]]
            output += f"**{category.capitalize()}:**\n" + "\n".join(topics) + "\n"
        return output

    # Handle Geo-map
    elif data_type == "GEO_MAP_0":
        header = "| Location | Interest |"
        # Filters for regions with significant interest
        rows = [f"| {item['location']} | {item['extracted_value']} |" 
                for item in data if int(item.get('extracted_value', 0)) > 0]
        return "### Interest by Region\n" + header + "\n|---|---|\n" + "\n".join(rows)

    return str(data) # Fallback to string if unknown


def format_trending_now_output(data_list) -> str:
    """Formats the 'Trending Now' list for the agent."""
    if not data_list or not isinstance(data_list, list):
        return "No trending searches currently active."

    output = "## Current Trending Searches\n"
    header = "| Query | Search Volume | Increase % | Top Breakdown Terms |"
    rows = []

    # Process each trending item
    for item in data_list[:15]: # Limit to top 15 to save tokens
        query = item.get('query', 'N/A')
        volume = item.get('search_volume', 0)
        increase = f"+{item.get('increase_percentage', 0)}%"
        # Extract first 3 related terms from breakdown
        breakdown = ", ".join(item.get('trend_breakdown', [])[:3])
        
        rows.append(f"| {query} | {volume:,} | {increase} | {breakdown} |")

    return output + header + "\n|---|---|---|---|\n" + "\n".join(rows)

def class_to_id() -> dict:
    input_dict = {
    "1": "Autos and Vehicles",
    "2": "Beauty and Fashion",
    "3": "Business and Finance",
    "20": "Climate",
    "4": "Entertainment",
    "5": "Food and Drink",
    "6": "Games",
    "7": "Health",
    "8": "Hobbies and Leisure",
    "9": "Jobs and Education",
    "10": "Law and Government",
    "11": "Other",
    "13": "Pets and Animals",
    "14": "Politics",
    "15": "Science",
    "16": "Shopping",
    "17": "Sports",
    "18": "Technology",
    "19": "Travel and Transportation"
    }
    new_dict = {}
    for key, value in input_dict.items():
        new_dict[value] = key
    with open("mcp_server/trend_server/google_trend_categories.json", "w", encoding = "utf-8") as f:
        json.dump(new_dict, f, indent = 4)
    return new_dict

if __name__ == "__main__":
    class_to_id()