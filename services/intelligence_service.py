from services.news_service import get_news


def generate_intelligence_report(location):

    news_articles = get_news(location)

    detected_events = []

    seen = set()

    for article in news_articles:

        category = article["category"]
        sector = article["affected_sector"]

        key = (category, sector)

        if key not in seen:
            seen.add(key)

            detected_events.append({
                "headline": article["title"],
                "source": article["source"],
                "url": article["url"],
                "event_name": article["event_name"],
                "category": article["category"],
                "affected_sector": article["affected_sector"],
                "affected_service": article["affected_service"]
            })
    if not detected_events:
        return {
            "location": location,
            "status": "No major disruptions detected",
            "detected_events": []
        }

    return {
        "location": location,
        "status": "Disruptions detected",
        "detected_events": detected_events
    }