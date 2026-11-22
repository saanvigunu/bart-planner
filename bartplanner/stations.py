"""Station lookup against the committed snapshot of BART's station list.

The snapshot (data/stations.json) comes from BART's official stn endpoint;
its file header says where and when it was fetched. Station codes are the
same abbreviations every other BART endpoint uses, so one fuzzy match here
feeds departures, trips and advisories.
"""

import json
import os

SNAPSHOT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        os.pardir, "data", "stations.json")


def load_stations(path=SNAPSHOT):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)["stations"]


def _norm(text):
    return " ".join(text.lower().replace(".", " ").replace("/", " ").split())


class StationIndex:
    def __init__(self, stations=None):
        self.stations = stations if stations is not None else load_stations()
        self.by_abbr = {s["abbr"].upper(): s for s in self.stations}

    def find(self, query):
        """Resolve a code or fuzzy name to one station, or raise KeyError
        with the close matches so the caller can show them."""
        q = _norm(query)
        exact = self.by_abbr.get(query.strip().upper())
        if exact:
            return exact
        # substring match on normalized names, shortest name first
        hits = [s for s in self.stations
                if q in _norm(s["name"]) or q in _norm(s["city"])]
        hits.sort(key=lambda s: (len(_norm(s["name"])), s["name"]))
        if len(hits) == 1:
            return hits[0]
        if hits:
            # only auto-pick when the query is an unambiguous word match
            word_hits = [s for s in hits
                         if q in _norm(s["name"]).split() or q == _norm(s["name"])]
            if len(word_hits) == 1:
                return word_hits[0]
        raise KeyError(hits)

    def search(self, query):
        q = _norm(query)
        return [s for s in self.stations
                if q in _norm(s["name"]) or q in _norm(s["city"])
                or q in s["abbr"].lower()]
