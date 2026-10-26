from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from services.weather_service import get_weather
from services.news_service import get_news
from services.intelligence_service import generate_intelligence_report
from services.report_service import generate_report
import time
from database import Base, engine
import models
from datetime import datetime
from saved_reports import router as saved_reports_router
from auth import router as auth_router


from incident_monitor import get_incident_status


app = FastAPI()
app.include_router(auth_router)
app.include_router(saved_reports_router)
Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://regionalintelligence.netlify.app"
    ],
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


@app.get("/incidents/live")
def live_incidents():
    """Return incidents fetched from public monitoring feeds."""
    return get_incident_status()


@app.get("/incidents/health")
def incident_feed_health():
    """Check whether public incident feeds are returning data."""
    status = get_incident_status()

    return {
        "status": (
            "ok" if status["incident_count"] > 0 else "no_data"
        ),
        "incident_count": status["incident_count"],
        "updated_at": status["updated_at"],
        "sources": status["sources"],
        "notice": status["notice"],
    }
