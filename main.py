from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from services.weather_service import get_weather
from services.news_service import get_news
from services.intelligence_service import generate_intelligence_report
from services.report_service import generate_report
import time
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Allow all origins during development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.get("/")
def home():
    return {"message": "AI-Assisted Regional Intelligence API Running"}



@app.get("/weather")
def weather(city: str):

    print("\n[1/5] Fetching weather data...")

    weather_data = get_weather(city)

    print("Weather retrieved successfully")

    return weather_data

@app.get("/news")
def news(location: str):

    print("\n[2/5] Fetching news data...")

    news_articles = get_news(location)

    print(f"News articles found: {len(news_articles)}")

    return news_articles

@app.get("/intelligence")
def intelligence(location: str):

    print("\n[3/5] Generating intelligence report...")

    detected_events = generate_intelligence_report(location)

    print(f"Relevant disruptions detected: {len(detected_events)}")

    return detected_events

@app.get("/report")
def report(location: str):
    

    start_time = time.time()

    print("\n" + "="*50)
    print("Regional Intelligence Analysis Started")
    print(f"Location: {location}")
    print(f"Time: {datetime.now()}")
    print("="*50)
    if not location.strip():
        return {
            "error": "Location cannot be empty"
        }
    print("\n[4/5] Preparing response...")
    print("✓ Response generated successfully")
    return generate_report(location)

    end_time = time.time()

    print("\n" + "=" * 50)
    print(
        f"Analysis completed in "
        f"{end_time - start_time:.2f} seconds"
    )
    print("=" * 50)