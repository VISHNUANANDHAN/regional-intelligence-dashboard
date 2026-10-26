
"""Global incident monitoring using GDACS, GDELT and PostgreSQL."""

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import hashlib
import logging
import re
import time
import xml.etree.ElementTree as ET

import requests
from sqlalchemy.exc import SQLAlchemyError

from database import SessionLocal
from models import Incident

logger = logging.getLogger(__name__)

GDACS_URL = "https://www.gdacs.org/xml/rss.xml"
GDELT_URL = "https://api.gdeltproject.org/api/v2/doc/doc"

REQUEST_TIMEOUT = 15
REFRESH_SECONDS = 180
MAX_INCIDENTS = 100

_session = requests.Session()
_session.headers.update({
    "User-Agent": "RegionalIntelligenceDashboard/1.0"
})

_last_refresh = 0.0
_cached_incidents = None

CATEGORY_TERMS = {
    "Natural disasters": [
        "earthquake", "flood", "cyclone", "hurricane", "typhoon",
        "wildfire", "volcano", "tsunami", "landslide", "drought"
    ],
    "Terrorism and security incidents": [
        "terrorism", "terrorist", "bombing", "hostage",
        "security incident", "shooting"
    ],
    "Political unrest": [
        "protest", "demonstration", "riot", "political unrest",
        "coup", "civil unrest"
    ],
    "Economic and infrastructure disruptions": [
        "power outage", "blackout", "supply chain", "port closure",
        "airport closure", "rail disruption", "oil disruption",
        "economic crisis", "internet outage", "infrastructure disruption"
    ],
    "Geopolitical conflicts": [
        "war", "conflict", "airstrike", "missile", "military attack",
        "armed clashes", "invasion", "ceasefire"
    ],
}


def utc_now():
    return datetime.now(timezone.utc)


def parse_date(value):
    if not value:
        return None

    try:
        result = parsedate_to_datetime(value)
    except (TypeError, ValueError, OverflowError):
        try:
            result = datetime.fromisoformat(
                str(value).replace("Z", "+00:00")
            )
        except (TypeError, ValueError, OverflowError):
            return None

    if result.tzinfo is None:
        result = result.replace(tzinfo=timezone.utc)

    return result.astimezone(timezone.utc)


def clean(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def stable_id(source, url):
    """Keep source IDs within the database column length."""
    return hashlib.sha256(
        f"{source}:{url}".encode("utf-8")
    ).hexdigest()


def classify_category(text, default="Geopolitical conflicts"):
    text = text.lower()

    for category, terms in CATEGORY_TERMS.items():
        if any(term in text for term in terms):
            return category

    return default


def estimate_severity(text):
    """
    Estimated monitoring priority only, not an official threat rating.
    """
    text = text.lower()

    high_terms = [
        "magnitude 7", "magnitude 8", "mass casualties",
        "multiple fatalities", "state of emergency",
        "severe cyclone", "major earthquake", "major flood",
        "widespread blackout"
    ]

    medium_terms = [
        "earthquake", "flood", "protest", "airstrike",
        "explosion", "wildfire", "cyclone", "power outage",
        "military clash", "bombing"
    ]

    if any(term in text for term in high_terms):
        return "HIGH"

    if any(term in text for term in medium_terms):
        return "MEDIUM"

    return "LOW"


def make_incident(
    source, url, title, summary="", published_at=None,
    category=None, latitude=None, longitude=None,
    location=None, data_type="news"
):
    title = clean(title)
    url = clean(url)

    if not title or not url:
        return None

    combined_text = f"{title} {summary}"
    if not category:
        category = classify_category(
            combined_text,
            "Natural disasters"
            if source == "GDACS"
            else "Geopolitical conflicts"
        )

    return {
        "source_id": stable_id(source, url),
        "title": title[:1000],
        "summary": clean(summary) or None,
        "category": category,
        "severity": estimate_severity(combined_text),
        "severity_basis": (
            "Estimated from source text. This is not an official "
            "threat assessment."
        ),
        "location": clean(location) or None,
        "latitude": latitude,
        "longitude": longitude,
        "source": source,
        "source_url": url,
        "data_type": data_type,
        "published_at": published_at,
    }


def fetch_gdacs():
    incidents = []

    try:
        response = _session.get(GDACS_URL, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        root = ET.fromstring(response.content)

        for item in root.findall(".//item"):
            title = item.findtext("title")
            url = item.findtext("link")
            summary = item.findtext("description")
            published = parse_date(item.findtext("pubDate"))

            latitude = None
            longitude = None
            point = item.find("{http://www.georss.org/georss}point")

            if point is not None and point.text:
                try:
                    parts = point.text.strip().split()
                    latitude = float(parts[0])
                    longitude = float(parts[1])

                    if not (-90 <= latitude <= 90):
                        latitude = longitude = None
                    elif not (-180 <= longitude <= 180):
                        latitude = longitude = None
                except (ValueError, IndexError):
                    latitude = longitude = None

            incident = make_incident(
                source="GDACS",
                url=url,
                title=title,
                summary=summary,
                published_at=published,
                category="Natural disasters",
                latitude=latitude,
                longitude=longitude,
                data_type="disaster_alert",
            )

            if incident:
                incidents.append(incident)

    except (requests.RequestException, ET.ParseError) as exc:
        logger.warning("GDACS feed unavailable: %s", exc)

    return incidents


def fetch_gdelt():
    incidents = []

    query = (
        '"conflict" OR "airstrike" OR "military attack" OR '
        '"protest" OR "political unrest" OR "terrorism" OR '
        '"bombing" OR "power outage" OR "infrastructure disruption" OR '
        '"earthquake" OR "flood" OR "wildfire" OR "cyclone"'
    )

    try:
        response = _session.get(
            GDELT_URL,
            params={
                "query": query,
                "mode": "ArtList",
                "format": "json",
                "maxrecords": 50,
                "sort": "HybridRel",
            },
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        payload = response.json()

        for article in payload.get("articles", []):
            title = clean(article.get("title"))
            url = clean(article.get("url"))
            domain = clean(article.get("domain"))

            incident = make_incident(
                source=domain or "GDELT",
                url=url,
                title=title,
                published_at=parse_date(article.get("seendate")),
                data_type="news",
            )

            if incident:
                incidents.append(incident)

    except (requests.RequestException, ValueError, TypeError) as exc:
        logger.warning("GDELT feed unavailable: %s", exc)

    return incidents


def serialize_incident(row):
    def iso(value):
        return value.isoformat() if value else None

    return {
        "id": row.id,
        "source_id": row.source_id,
        "title": row.title,
        "summary": row.summary,
        "category": row.category,
        "severity": row.severity,
        "severity_basis": row.severity_basis,
        "location": row.location,
        "latitude": row.latitude,
        "longitude": row.longitude,
        "source": row.source,
        "source_url": row.source_url,
        "data_type": row.data_type,
        "published_at": iso(row.published_at),
        "first_seen_at": iso(row.first_seen_at),
        "last_seen_at": iso(row.last_seen_at),
    }


def save_incidents(incidents):
    """Insert new source records and update records already known."""
    if not incidents:
        return

    db = SessionLocal()

    try:
        for item in incidents:
            row = (
                db.query(Incident)
                .filter(Incident.source_id == item["source_id"])
                .first()
            )

            if row is None:
                row = Incident(
                    source_id=item["source_id"],
                    title=item["title"],
                    summary=item["summary"],
                    category=item["category"],
                    severity=item["severity"],
                    severity_basis=item["severity_basis"],
                    location=item["location"],
                    latitude=item["latitude"],
                    longitude=item["longitude"],
                    source=item["source"],
                    source_url=item["source_url"],
                    data_type=item["data_type"],
                    published_at=item["published_at"],
                    first_seen_at=utc_now(),
                    last_seen_at=utc_now(),
                )
                db.add(row)
            else:
                row.title = item["title"]
                row.summary = item["summary"]
                row.category = item["category"]
                row.severity = item["severity"]
                row.severity_basis = item["severity_basis"]
                row.location = item["location"]
                row.latitude = item["latitude"]
                row.longitude = item["longitude"]
                row.source = item["source"]
                row.source_url = item["source_url"]
                row.data_type = item["data_type"]

                if item["published_at"]:
                    row.published_at = item["published_at"]

                row.last_seen_at = utc_now()

        db.commit()

    except SQLAlchemyError:
        db.rollback()
        logger.exception("Could not persist incidents to PostgreSQL")
        raise
    finally:
        db.close()


def read_saved_incidents():
    db = SessionLocal()

    try:
        rows = (
            db.query(Incident)
            .order_by(
                Incident.published_at.desc().nullslast(),
                Incident.last_seen_at.desc(),
            )
            .limit(MAX_INCIDENTS)
            .all()
        )
        return [serialize_incident(row) for row in rows]
    finally:
        db.close()


def get_live_incidents(force_refresh=False):
    """Refresh public feeds periodically; return persisted records."""
    global _last_refresh, _cached_incidents

    now = time.time()

    if (
        not force_refresh
        and _cached_incidents is not None
        and now - _last_refresh < REFRESH_SECONDS
    ):
        return list(_cached_incidents)

    source_results = fetch_gdacs()
    source_results.extend(fetch_gdelt())

    try:
        if source_results:
            save_incidents(source_results)

        # Read from PostgreSQL so records remain available between refreshes.
        saved = read_saved_incidents()
        _cached_incidents = saved
        _last_refresh = now
        return list(saved)

    except SQLAlchemyError:
        logger.exception("Incident database unavailable")

        # Return current source results if persistence is temporarily down.
        return source_results


def get_incident_status():
    incidents = get_live_incidents()

    return {
        "updated_at": utc_now().isoformat(),
        "refresh_interval_seconds": REFRESH_SECONDS,
        "incident_count": len(incidents),
        "sources": ["GDACS", "GDELT"],
        "incidents": incidents,
        "notice": (
            "Coverage and publication delays vary by source. Severity is "
            "an estimated monitoring priority, not a verified threat rating. "
            "Missing coordinates are not inferred. An empty feed does not "
            "prove that no incidents are occurring."
        ),
    }
