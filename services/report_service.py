from services.weather_service import get_weather
from services.intelligence_service import generate_intelligence_report

def generate_report(location):
    weather_data = get_weather(location)
    if "error" in weather_data:
        return {
            "error": weather_data["error"]
        }

    intelligence_data = generate_intelligence_report(location)
    
    return {
    "location": weather_data["city"],
    "weather": {
        "temperature": weather_data["temperature"],
        "condition": weather_data["weather"],
        "description": weather_data["description"]
    },
    "status": intelligence_data["status"],
    "detected_events": intelligence_data["detected_events"]
    }