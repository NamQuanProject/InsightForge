def _first_trend_value(item: dict) -> float | int | str:
    values = item.get("values") or []
    if not values:
        return 0

    first = values[0]
    if isinstance(first, dict):
        return first.get("extracted_value") or first.get("value") or 0
    return first or 0


def format_trends_output(data, data_type: str) -> str:
    """Formats Google Trends data for better agent readability."""
    if not data:
        return "No data found for this trend query."

    # Handle Timeseries (Interest over time)
    if data_type == "TIMESERIES":
        # Extracts date and the value for the primary query
        header = "| Date | Interest Score |"
        rows = [
            f"| {item.get('date', 'N/A')} | {_first_trend_value(item)} |"
            for item in data.get('timeline_data', [])[-10:]
            if isinstance(item, dict)
        ] # Get last 10 points
        if not rows:
            return "No timeseries data found for this trend query."
        return "### Interest Over Time\n" + header + "\n|---|---|\n" + "\n".join(rows)

    # Handle Related Queries
    elif data_type == "RELATED_QUERIES":
        output = "### Related Queries\n"
        for category in ['top', 'rising']:
            queries = [
                f"- {q.get('query', 'N/A')} ({q.get('value', 0)})"
                for q in data.get(category, [])[:5]
                if isinstance(q, dict)
            ]
            output += f"**{category.capitalize()}:**\n" + "\n".join(queries) + "\n"
        return output

    # Handle Related Topics
    elif data_type == "RELATED_TOPICS":
        output = "### Related Topics\n"
        for category in ['top', 'rising']:
            topics = []
            for topic_item in data.get(category, [])[:5]:
                if not isinstance(topic_item, dict):
                    continue
                topic = topic_item.get("topic") or {}
                topics.append(
                    f"- {topic.get('title', 'N/A')} "
                    f"[{topic.get('type', 'unknown')}] "
                    f"({topic_item.get('value', 0)})"
                )
            output += f"**{category.capitalize()}:**\n" + "\n".join(topics) + "\n"
        return output

    # Handle Geo-map
    elif data_type == "GEO_MAP_0":
        if not isinstance(data, list):
            return "No regional data found for this trend query."
        header = "| Location | Interest |"
        # Filters for regions with significant interest
        rows = [
            f"| {item.get('location', 'N/A')} | {item.get('extracted_value', 0)} |"
            for item in data
            if isinstance(item, dict) and int(item.get('extracted_value', 0) or 0) > 0
        ]
        if not rows:
            return "No regional data found for this trend query."
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
