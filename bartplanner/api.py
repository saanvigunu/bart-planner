"""Thin client for BART's official public API (api.bart.gov).

Uses the public registration key from BART's own API documentation by
default; set BART_API_KEY to use your own. Everything here is a live
request - no caching, no pretending the data is fresher than it is.
"""

import json
import os
import urllib.parse
import urllib.request

BASE = "https://api.bart.gov/api"
# BART's documentation publishes this key for public use.
DEFAULT_KEY = "MW9S-E7SL-26DU-VV8V"


class BartApiError(Exception):
    pass


def _get(endpoint, **params):
    params["key"] = os.environ.get("BART_API_KEY", DEFAULT_KEY)
    params["json"] = "y"
    url = f"{BASE}/{endpoint}.aspx?" + urllib.parse.urlencode(params)
    # BART's gateway 403s the default python-urllib user agent; a plain
    # browser-style UA is accepted (curl works too).
    req = urllib.request.Request(url, headers={"User-Agent": "bart-planner-cli"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BartApiError(f"could not reach BART's API: {exc}") from exc
    root = payload.get("root", {})
    message = root.get("message")
    error = message.get("error") if isinstance(message, dict) else None
    if error:
        raise BartApiError(f"BART API error: {error.get('text', 'unknown')} "
                           f"({error.get('details', '')})")
    return root


def departures(station_abbr, direction=None):
    """Real-time departure estimates for a station (BART's ETD feed)."""
    params = {"cmd": "etd", "orig": station_abbr}
    if direction in ("n", "s"):
        params["dir"] = direction
    root = _get("etd", **params)
    return {
        "as_of": f"{root.get('date', '')} {root.get('time', '')}".strip(),
        "stations": root.get("station", []),
    }


def trip(origin_abbr, dest_abbr, when=None, arrive_by=False):
    """Trip plan from BART's own schedule endpoint (fares, legs, times).

    when: 'HH:MM' 24-hour or BART's own 'h:mmam/pm'; arrive_by picks
    BART's arrive endpoint instead.
    """
    params = {"cmd": "arrive" if arrive_by else "depart",
              "orig": origin_abbr, "dest": dest_abbr, "a": 4, "b": 0}
    if when:
        params["time"] = _to_bart_time(when)
    root = _get("sched", **params)
    schedule = root.get("schedule", {})
    request = schedule.get("request", {})
    trips = request.get("trip", [])
    if isinstance(trips, dict):
        trips = [trips]
    return {
        "origin": root.get("origin"),
        "destination": root.get("destination"),
        "as_of": f"{root.get('date', '')} {root.get('time', '')}".strip(),
        "schedule_date": schedule.get("date", ""),
        "trips": trips,
    }


def _to_bart_time(when):
    """BART's sched endpoints want 'h:mmam/pm'; accept 24-hour too."""
    w = when.strip().lower().replace(" ", "")
    if w.endswith(("am", "pm")):
        return w
    try:
        hour, minute = (int(p) for p in w.split(":"))
    except ValueError:
        raise BartApiError(f"bad --time '{when}' (use HH:MM, e.g. 17:30)")
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise BartApiError(f"bad --time '{when}' (use HH:MM, e.g. 17:30)")
    suffix = "am" if hour < 12 else "pm"
    return f"{hour % 12 or 12}:{minute:02d}{suffix}"


def advisories():
    """Current service advisories (BSA)."""
    root = _get("bsa", cmd="bsa")
    items = root.get("bsa", [])
    if isinstance(items, dict):
        items = [items]
    return {
        "as_of": f"{root.get('date', '')} {root.get('time', '')}".strip(),
        "advisories": [
            {"station": i.get("station", ""),
             "description": i.get("description", {}).get("#cdata-section", "")}
            for i in items
        ],
      }
