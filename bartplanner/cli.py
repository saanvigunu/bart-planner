"""bart-planner command line.

    python3 -m bartplanner stations [search]
    python3 -m bartplanner next <station> [--north|--south]
    python3 -m bartplanner trip <from> <to> [--time HH:MM] [--arrive-by]
    python3 -m bartplanner advisories

Stations resolve by code (EMBR) or fuzzy name ("embarcadero", "12th").
Live commands hit BART's official API; `stations` works offline from the
committed snapshot.
"""

import sys

from . import api, formatting
from .stations import StationIndex

USAGE = __doc__


def _resolve(index, query):
    try:
        return index.find(query)
    except KeyError as err:
        matches = err.args[0]
        if matches:
            shown = "\n".join("    " + formatting.format_station(s)
                              for s in matches[:8])
            print(f"'{query}' is ambiguous - did you mean one of these?\n{shown}",
                  file=sys.stderr)
        else:
            print(f"no station matches '{query}' "
                  f"(try `python3 -m bartplanner stations {query.split()[0]}`)",
                  file=sys.stderr)
        sys.exit(2)


def cmd_stations(index, args):
    rows = index.search(args[0]) if args else index.stations
    for s in rows:
        print(formatting.format_station(s))
    print(f"{len(rows)} stations", file=sys.stderr)


def cmd_next(index, args):
    direction = None
    names = []
    for a in args:
        if a in ("--north", "-n"):
            direction = "n"
        elif a in ("--south", "-s"):
            direction = "s"
        else:
            names.append(a)
    if not names:
        sys.exit("next needs a station, e.g. `next embarcadero`")
    stn = _resolve(index, " ".join(names))
    try:
        payload = api.departures(stn["abbr"], direction)
    except api.BartApiError as exc:
        sys.exit(str(exc))
    print(formatting.format_departures(payload, stn["name"]))


def cmd_trip(index, args):
    when, arrive_by = None, False
    names = []
    it = iter(range(len(args)))
    skip = False
    for i in it:
        if skip:
            skip = False
            continue
        a = args[i]
        if a == "--time" and i + 1 < len(args):
            when = args[i + 1]
            skip = True
        elif a == "--arrive-by":
            arrive_by = True
        else:
            names.append(a)
    if len(names) < 2:
        sys.exit("trip needs two stations, e.g. `trip embarcadero millbrae`")
    origin = _resolve(index, names[0])
    dest = _resolve(index, " ".join(names[1:]))
    try:
        payload = api.trip(origin["abbr"], dest["abbr"], when, arrive_by)
    except api.BartApiError as exc:
        sys.exit(str(exc))
    print(formatting.format_trips(payload))


def cmd_advisories(index, args):
    try:
        payload = api.advisories()
    except api.BartApiError as exc:
        sys.exit(str(exc))
    print(formatting.format_advisories(payload))


COMMANDS = {"stations": cmd_stations, "next": cmd_next,
            "trip": cmd_trip, "advisories": cmd_advisories}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(USAGE)
        return 0
    cmd = COMMANDS.get(argv[0])
    if cmd is None:
        print(USAGE, file=sys.stderr)
        return 2
    cmd(StationIndex(), argv[1:])
    return 0


if __name__ == "__main__":
    sys.exit(main())
