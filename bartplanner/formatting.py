"""Turn raw API payloads into readable terminal output.

Kept separate from the client so tests can pin the exact strings against
the committed sample responses.
"""

def _cdata(value):
    if isinstance(value, dict):
        return value.get("#cdata-section", "")
    return value or ""


def _as_list(value):
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def format_departures(payload, station_name=None):
    """ETD payload -> lines like '  18 min   Antioch          9-car  platform 2'."""
    lines = []
    for stn in _as_list(payload.get("stations")):
        name = station_name or stn.get("name", stn.get("abbr", "?"))
        etds = _as_list(stn.get("etd"))
        if not etds:
            lines.append(f"{name}: no departures listed right now")
            continue
        lines.append(f"{name} (as of {payload.get('as_of', '?')}):")
        for etd in etds:
            dest = etd.get("destination", "?")
            for est in _as_list(etd.get("estimate")):
                mins = est.get("minutes", "?")
                when = "now" if mins.lower() == "leaving" else f"{mins} min"
                length = est.get("length", "?")
                platform = est.get("platform", "?")
                delay = est.get("delay", "0")
                flag = ""
                if delay not in ("0", None):
                    flag = f"  (+{int(delay)//60} min delay)" if str(delay).isdigit() else ""
                lines.append(f"  {when:>8}  {dest:<20} {length}-car  "
                             f"platform {platform}{flag}")
    return "\n".join(lines)


def _fmt_leg(leg):
    origin = leg.get("@origin", "?")
    dest = leg.get("@destination", "?")
    dep = leg.get("@origTimeMin", "?")
    arr = leg.get("@destTimeMin", "?")
    head = leg.get("@trainHeadStation", "?")
    return f"    {dep} {origin} -> {arr} {dest}  ({head} train)"


def format_trips(payload, index=None):
    """Schedule payload -> one block per trip with fare and legs."""
    trips = payload.get("trips", [])
    if not trips:
        return "no trips found in the schedule right now"
    out = []
    for i, t in enumerate(trips, 1):
        fare = t.get("@fare", "?")
        clipper = t.get("@clipper")
        mins = t.get("@tripTime", "?")
        dep = t.get("@origTimeMin", "?")
        arr = t.get("@destTimeMin", "?")
        header = f"trip {i}: {dep} -> {arr} ({mins} min, ${fare}"
        if clipper:
            header += f", ${clipper} with clipper"
        header += ")"
        legs = [_fmt_leg(leg) for leg in _as_list(t.get("leg"))]
        out.append("\n".join([header] + legs))
    note = f"(schedule for {payload.get('schedule_date', '?')}, from BART's own planner)"
    return "\n\n".join(out) + "\n" + note


def format_advisories(payload):
    items = payload.get("advisories", [])
    if not items or all(not a["description"] or "no advisories" in a["description"].lower()
                        for a in items):
        return f"no advisories right now (as of {payload.get('as_of', '?')})"
    lines = [f"advisories (as of {payload.get('as_of', '?')}):"]
    for a in items:
        where = f"[{a['station']}] " if a["station"] else ""
        lines.append(f"  - {where}{a['description']}")
    return "\n".join(lines)


COUNTY_NAMES = {"sanfrancisco": "San Francisco", "alameda": "Alameda",
                "contracosta": "Contra Costa", "sanmateo": "San Mateo",
                "santaclara": "Santa Clara"}


def format_station(s):
    county = COUNTY_NAMES.get(s["county"].lower(), s["county"].title())
    return f"{s['abbr']:5} {s['name']:<34} {s['city']}, {county} Co."
