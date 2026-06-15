import json

from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv("NVIDIA_API_KEY")
client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=API_KEY
)


def classify_event_ai(location, headline, description="", content=""):

    prompt = f"""
You are an intelligence analyst for a Regional Disruption Intelligence System.

User Location: {location}

Headline:
{headline}

Description:
{description}

Content:
{content}

TASK:

Determine whether this article describes a REAL disruption occurring in the User Location.

A disruption means an event that directly affects people, infrastructure, transportation, safety, or public services in that location.

Examples of VALID disruptions:
- Floods
- Heavy rainfall causing traffic disruption
- Cyclones
- Wildfires
- Protests
- Riots
- Workers strikes affecting services
- Airport disruptions
- Railway disruptions
- Bus service disruptions
- Road closures
- Military attacks occurring in that location
- Armed conflicts directly impacting that location

Examples of INVALID disruptions:
- Meetings
- Diplomatic talks
- Summits
- Conferences
- Mediation efforts
- Discussions about conflicts elsewhere
- Bills, legislation, or policy proposals
- Government announcements
- Price updates
- Commodity market reactions
- Economic analysis
- Company expansions
- Technology developments
- Sports news
- Entertainment news
- Opinion articles
- Commentary articles
- News merely mentioning the location

IMPORTANT:

The MAIN SUBJECT of the article must itself be the disruption.

If the disruption occurs somewhere else and the User Location is only mentioned as a meeting place, discussion venue, mediator, observer, or reference point, classify it as No Disruption.

If the article primarily discusses consequences of a disruption (market effects, political reactions, international commentary) rather than the disruption itself occurring in the User Location, classify it as No Disruption.

If there is NO disruption affecting the User Location, return EXACTLY:

{{
    "event_name": "No Disruption",
    "event_category": "General Information",
    "affected_sector": "None",
    "affected_service": "None"
}}

Otherwise return JSON in this exact format:

{{
    "event_name": "...",
    "event_category": "...",
    "affected_sector": "...",
    "affected_service": "..."
}}

Interviews, opinions, expert commentary, editorials,
analyses, and discussions ABOUT disruptions are NOT disruptions.

Only classify as a disruption if the article itself reports
the disruptive event occurring in the user location.

Allowed event categories:
- Natural Calamity
- Public & Social Disruption
- Transportation Disruption
- Geopolitical Event

Allowed affected sectors:
- Transportation
- Logistics
- Tourism
- Public Safety
- National Security

Allowed affected services:
- Road Transportation
- Railway Services
- Airline Operations
- Bus Services
- Cargo Movement
- Tourism Services
- Emergency Response
- Civilian Infrastructure

IMPORTANT:
Return ONLY raw JSON.
Do NOT use markdown.
Do NOT wrap the response inside ```json blocks.
"""

    response = client.chat.completions.create(
        model="meta/llama-3.3-70b-instruct",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.1,
        max_tokens=250
    )

    result = response.choices[0].message.content

    result = result.replace("```json", "")
    result = result.replace("```", "")
    result = result.strip()

    try:
        return json.loads(result)
    except:
        return {
            "event_name": "No Disruption",
            "event_category": "General Information",
            "affected_sector": "None",
            "affected_service": "None"
        }