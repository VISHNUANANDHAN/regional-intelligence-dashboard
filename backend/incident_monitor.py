
"""Fetch real global disaster alerts and news for incident monitoring."""

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import logging
import re
import time
import xml.etree.ElementTree as ET

import requests

logger = logging.getLogger(__name__)

GDACS_FEED_URL = "https://www.gdacs.org/xml/rss.xml"
GDELT_API_URL = "https://api.gdeltproject.org/api/v2/doc/doc"

REQUEST_TIMEOUT = 15
MAX_INCIDENTS = 100
CACHE_SECONDS = 180

_session = requests.Session()
_session.headers.update({
    "User-Agent": "RegionalIntelligenceDashboard/1.0 (public incident monitoring)"
})

_cache = {"timestamp": 0.0, "incidents": []}

CATEGORIES = {
    "Geopolitical conflicts": [
        "war", "conflict", "airstrike", "missile", "military attack",
        "armed clashes", "invasion", "ceasefire"
    ],
    "Natural disasters": [
        "earthquake", "flood", "cyclone", "hurricane", "typhoon",
        "wildfire", "volcano", "tsunami", "landslide", "drought"
    ],
    "Political unrest": [
        "protest", "demonstration", "riot", "political unrest",
        "coup", "strike", "civil unrest"
    ],
    "Terrorism and security incidents": [
        "terrorism", "terrorist", "bombing", "explosion", "hostage",
        "security incident", "attack", "shooting"
    ],
    "Economic and infrastructure disruptions": [
        "power outage", "blackout", "infrastructure", "supply chain",
        "port closure", "airport closure", "rail disruption",
        "oil disruption", "economic crisis", "internet outage"
    ],
}

def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _parse_date(value):
    if not value:
        return None

    try:
        dt = parsedate_to_datetime(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()
    except (TypeError, ValueError, OverflowError):
        pass

    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()
    except (TypeError, ValueError, OverflowError):
        return None


def _classify_category(text, default="Geopolitical conflicts"):
    lowered = text.lower()

    # Check specific categories before the broad conflict category.
    priority = [
        "Natural disasters",
        "Terrorism and security incidents",
        "Political unrest",
        "Economic and infrastructure disruptions",
        "Geopolitical conflicts",
    ]

    for category in priority:
        if any(term in lowered for term in CATEGORIES[category]):
            return category

    return default


def _estimate_severity(text, official_level=None):
    """
    Return a monitoring-priority estimate.
    This is not an official threat assessment.
    """
    if official_level:
        level = str(official_level).strip().lower()
        if level in {"red", "high", "3", "severe"}:
            return "HIGH"
        if level in {"orange", "medium", "2"}:
            return "MEDIUM"
        if level in {"green", "low", "1"}:
            return "LOW"

    lowered = text.lower()

    high_terms = (
        "major earthquake", "magnitude 7", "magnitude 8",
        "major flood", "mass casualties", "multiple fatalities",
        "large-scale attack", "state of emergency", "severe cyclone",
        "major explosion", "widespread blackout"
    )
    medium_terms = (
        "earthquake", "flood", "protest", "airstrike", "explosion",
        "wildfire", "cyclone", "power outage", "military clash"
    )

    if any(term in lowered for term in high_terms):
        return "HIGH"
    if any(term in lowered for term in medium_terms):
        return "MEDIUM"
    return "LOW"


def _clean_text(value):
    if not value:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def _fetch_gdacs():
    incidents = []

    try:
        response = _session.get(
            GDACS_FEED_URL,
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()

        root = ET.fromstring(response.content)

        for item in root.findall(".//item"):
            title = _clean_text(item.findtext("title"))
            link = _clean_text(item.findtext("link"))
            description = _clean_text(item.findtext("description"))
            published = _parse_date(item.findtext("pubDate"))
            text = f"{title} {description}"

            if not title or not link:
                continue

            latitude = None
            longitude = None

            # GDACS feeds may expose a GeoRSS point.
            point = item.find("{http://www.georss.org/georss}point")
            if point is not None and point.text:
                try:
                    values = point.text.strip().split()
                    if len(values) >= 2:
                        latitude = float(values[0])
                        longitude = float(values[1])
                except (ValueError, TypeError):
                    latitude = longitude = None

            incidents.append({
                "id": f"gdacs:{link}",
                "title": title,
                "summary": description,
                "category": _classify_category(
                    text, "Natural disasters"
                ),
                "severity": _estimate_severity(text),
                "severity_basis": "Estimated from feed text; see source alert.",
                "location": None,
                "latitude": latitude,
                "longitude": longitude,
                "source": "GDACS",
                "source_url": link,
                "published_at": published,
                "fetched_at": _now_iso(),
                "data_type": "disaster_alert",
            })

    except (requests.RequestException, ET.ParseError) as exc:
        logger.warning("GDACS feed unavailable: %s", exc)

    return incidents


def _fetch_gdelt():
    incidents = []

    query = (
        '"conflict" OR "airstrike" OR "military attack" OR '
        '"protest" OR "political unrest" OR "terrorism" OR '
        '"bombing" OR "power outage" OR "infrastructure disruption" OR '
        '"earthquake" OR "flood" OR "wildfire" OR "cyclone"'
    )

    try:
        response = _session.get(
            GDELT_API_URL,
            params={
                "query": query,
                "mode": "ArtList",
                "format": "json",
                "maxrecords": 50,
                "sort": "HybridRel",
            },
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        payload = response.json()

        for article in payload.get("articles", []):
            title = _clean_text(article.get("title"))
            url = _clean_text(article.get("url"))

            if not title or not url:
                continue

            domain = _clean_text(article.get("domain"))
            source = domain or "GDELT-indexed news"

            # GDELT's article list does not reliably provide coordinates.
            # Do not invent a location from a headline.
            published = _parse_date(article.get("seendate"))

            incidents.append({
                "id": f"gdelt:{url}",
                "title": title,
                "summary": "",
                "category": _classify_category(title),
                "severity": _estimate_severity(title),
                "severity_basis": (
                    "Estimated from headline keywords; verify the source."
                ),
                "location": None,
                "latitude": None,
                "longitude": None,
                "source": source,
                "source_url": url,
                "published_at": published,
                "fetched_at": _now_iso(),
                "data_type": "news",
            })

    except (
        requests.RequestException,
        ValueError,
        TypeError
    ) as exc:
        logger.warning("GDELT feed unavailable: %s", exc)

    return incidents


def get_live_incidents(force_refresh=False):
    """Return normalized incidents from available public feeds."""
    now = time.time()

    if (
        not force_refresh
        and _cache["incidents"]
        and now - _cache["timestamp"] < CACHE_SECONDS
    ):
        return list(_cache["incidents"])

    incidents = _fetch_gdacs()
    incidents.extend(_fetch_gdelt())

    # Deduplicate by stable source ID.
    unique = {}
    for incident in incidents:
        unique.setdefault(incident["id"], incident)

    result = sorted(
        unique.values(),
        key=lambda item: item.get("published_at") or "",
        reverse=True
    )[:MAX_INCIDENTS]

    _cache["timestamp"] = now
    _cache["incidents"] = result

    return list(result)


def get_incident_status():
    """Provide feed status without fabricating incidents."""
    incidents = get_live_incidents()

    return {
        "updated_at": _now_iso(),
        "refresh_interval_seconds": CACHE_SECONDS,
        "incident_count": len(incidents),
        "sources": ["GDACS", "GDELT"],
        "incidents": incidents,
        "notice": (
            "Feed coverage and publication delays vary. Severity is an "
            "estimated monitoring priority, not a verified threat rating. "
            "Missing coordinates are not inferred."
        ),
    }

