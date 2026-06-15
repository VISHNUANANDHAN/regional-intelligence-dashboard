import requests
from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv("WEATHER_API_KEY")



def get_weather(city):

    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}"

    response = requests.get(url)

    data = response.json()
    if response.status_code != 200:
        return {
            "error": "Location not found"
        }

    return {
        "city": data["name"],
        "weather": data["weather"][0]["main"],
        "description": data["weather"][0]["description"],
        "temperature": round(data["main"]["temp"] - 273.15, 2)
    }