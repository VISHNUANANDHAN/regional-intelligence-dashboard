

import requests
from services.ai_classifier import classify_event_ai
from services.classifier import classify_event
from datetime import datetime, timedelta

from services.location_extractor import get_primary_location

date_from = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")

from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv("NEWS_API_KEY")

def get_news(location):

    query = (
        f"{location} AND "
        f"(flood OR rainfall OR storm OR cyclone OR wildfire "
        f"OR strike OR protest OR riot "
        f"OR conflict OR war "
        f"OR railway OR airport OR transport)"
    )

    url = (
        f"https://newsapi.org/v2/everything?"
        f"q={query}&"
        f"from={date_from}&"
        f"language=en&"
        f"sortBy=publishedAt&"
        f"apiKey={API_KEY}"
    )

    response = requests.get(url)

    data = response.json()

    articles = []

    keywords = [
    "flood",
    "rainfall",
    "storm warning",
    "tropical storm",
    "severe storm",
    "storm alert",
    "cyclone",
    "wildfire",
    "forest fire",
    "strike",
    "protest",
    "riot",
    "conflict",
    "war",
    "railway",
    "airport",
    "flight",
    "airline",
    "road closure",
    "transport"
    ]

    sports_words = [
            "beat",
            "beats",
            "won",
            "wins",
            "match",
            "league",
            "cup",
            "tournament",
            "player",
            "coach",
            "team",
            "scores"
            ]
    
    blocked_sources = [
            "Fark.com",
            "TMZ",
            "People",
            "E! Online",
            "Daily Mail"
        ]

   

    for article in data.get("articles", [])[:10]:

        if article["source"]["name"] in blocked_sources:
            continue
        
        title = article["title"]

        # Location validation

        if location.lower() in title.lower():
            pass

        else:
            primary_location = get_primary_location(title)

            if primary_location:

                if primary_location.lower() != location.lower():
                    continue

            if not any(keyword in title.lower() for keyword in keywords):
                continue
            

            if any(word in title.lower() for word in sports_words):
                continue

        try:

            classification = classify_event_ai(
                location=location,
                headline=title,
                description=article.get("description", ""),
                content=article.get("content", "")
            )

        except Exception:

            try:

                classification = classify_event_ai(
                    location=location,
                    headline=title,
                    description=article.get("description", ""),
                    content=article.get("content", "")
                )

            except Exception:

                classification = classify_event(title)

                if classification["event_category"] == "General Information":
                    continue

        if classification["affected_sector"] == "None":
            continue
        articles.append({
            "title": title,
            "url": article["url"],
            "source": article["source"]["name"],
            "event_name": classification["event_name"],
            "category": classification["event_category"],
            "affected_sector": classification["affected_sector"],
            "affected_service": classification["affected_service"]
        })

    return articles