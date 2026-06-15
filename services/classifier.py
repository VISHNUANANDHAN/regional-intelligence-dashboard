def classify_event(text):

    text = text.lower()

    result = {
    "event_name": "General Event",
    "event_category": "General Information",
    "affected_sector": "General",
    "affected_service": "General"
    }

    # Event Category

    if any(word in text for word in [
        "flood",
        "rainfall",
        "storm",
        "cyclone",
        "wildfire",
        "forest fire",
        "fire"
    ]):
        result["event_category"] = "Natural Calamity"

    elif any(word in text for word in [
        "drone strike",
        "missile strike",
        "air strike",
        "military strike",
        "war",
        "conflict",
        "border",
        "military"
        ]):
        result["event_category"] = "Geopolitical Event"

    elif any(word in text for word in [
        "workers strike",
        "employee strike",
        "staff strike",
        "railway strike",
        "bus strike",
        "protest",
        "riot",
        "curfew"
    ]):
        result["event_category"] = "Public & Social Disruption"

    elif any(word in text for word in [
        "road closure",
        "traffic",
        "train",
        "railway",
        "flight",
        "airport",
        "bus"
    ]):
        result["event_category"] = "Transportation Disruption"

    elif any(word in text for word in [
        "war",
        "conflict",
        "border",
        "military"
    ]):
        result["event_category"] = "Geopolitical Event"

    # Affected Sector

    if any(word in text for word in [
        "train",
        "railway",
        "airport",
        "flight",
        "airline",
        "bus",
        "transport",
        "road",
        "traffic",
        "flood",
        "rainfall",
        "storm",
        "cyclone"
    ]):
        result["affected_sector"] = "Transportation"

    elif any(word in text for word in [
        "cargo",
        "shipment",
        "supply chain",
        "delivery",
        "logistics"
    ]):
        result["affected_sector"] = "Logistics"

    elif any(word in text for word in [
        "tourism",
        "travel",
        "hotel",
        "visitor",
        "tourist"
    ]):
        result["affected_sector"] = "Tourism"

    elif any(word in text for word in [
        "evacuation",
        "emergency",
        "safety",
        "warning",
        "alert"
    ]):
        result["affected_sector"] = "Public Safety"

    # Affected Service

    if "railway" in text or "train" in text:
        
        result["affected_service"] = "Railway Services"

    elif "airport" in text or "flight" in text or "airline" in text:
        result["affected_service"] = "Airline Operations"

    elif "bus" in text:
        result["affected_service"] = "Bus Services"

    elif "road" in text or "traffic" in text:
        result["affected_service"] = "Road Transportation"

    elif "cargo" in text or "shipment" in text:
        result["affected_service"] = "Cargo Movement"

    elif "hotel" in text or "tourism" in text or "tourist" in text:
        result["affected_service"] = "Tourism Services"

    elif "emergency" in text or "evacuation" in text:
        result["affected_service"] = "Emergency Response"
    elif any(word in text for word in [
        "flood",
        "rainfall",
        "storm",
        "cyclone"
        ]):
        result["affected_service"] = "Road Transportation"

    # Event Name

    if any(word in text for word in [
    "drone strike",
    "missile strike",
    "air strike",
    "military strike"
    ]):
        result["event_name"] = "Military Strike"

    elif any(word in text for word in [
        "workers strike",
        "employee strike",
        "staff strike",
        "railway strike",
        "bus strike"
    ]):
        result["event_name"] = "Workers Strike"

    elif "protest" in text:
        result["event_name"] = "Protest"

    elif "riot" in text:
        result["event_name"] = "Riot"

    elif "flood" in text:
        result["event_name"] = "Flood"

    elif "rainfall" in text:
        result["event_name"] = "Heavy Rainfall"

    elif "cyclone" in text:
        result["event_name"] = "Cyclone"

    elif "storm" in text:
        result["event_name"] = "Storm"

    elif "wildfire" in text or "forest fire" in text:
        result["event_name"] = "Forest Fire"

    elif "war" in text:
        result["event_name"] = "War"

    elif "conflict" in text:
        result["event_name"] = "Conflict"

    elif "road closure" in text:
        result["event_name"] = "Road Closure"

    elif "airport" in text or "flight" in text or "airline" in text:
        result["event_name"] = "Air Travel Disruption"

    elif "railway" in text or "train" in text:
        result["event_name"] = "Railway Disruption"
    return result