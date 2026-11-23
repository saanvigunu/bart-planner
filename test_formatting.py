"""Formatting tests pinned to the committed real API samples.

Numbers in here are the actual contents of data/samples/*.json (fetched
2026-11-22); if the formatter drifts, these strings move.
"""

import json
import os
import unittest

from bartplanner import formatting

SAMPLES = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "data", "samples")


def load(name):
    with open(os.path.join(SAMPLES, name), encoding="utf-8") as fh:
        return json.load(fh)


class TestDepartures(unittest.TestCase):
    def test_real_embarcadero_sample(self):
        root = load("etd_embr.json")["root"]
        payload = {"as_of": f"{root['date']} {root['time']}",
                   "stations": root["station"]}
        out = formatting.format_departures(payload, "Embarcadero")
        lines = out.splitlines()
        self.assertTrue(lines[0].startswith("Embarcadero (as of "))
        self.assertIn("17 min", out)          # first Antioch estimate
        self.assertIn("Antioch", out)
        self.assertIn("9-car", out)
        self.assertIn("platform 2", out)
        # 7 destinations in this snapshot, at least one line each
        self.assertGreaterEqual(len(lines), 8)

    def test_empty_station(self):
        out = formatting.format_departures(
            {"as_of": "x", "stations": [{"name": "Nowhere", "etd": None}]})
        self.assertIn("no departures", out)


class TestTrips(unittest.TestCase):
    def test_real_embarcadero_millbrae_sample(self):
        root = load("depart_embr_mlbr.json")["root"]
        schedule = root["schedule"]
        trips = schedule["request"]["trip"]
        payload = {"schedule_date": schedule["date"], "trips": trips}
        out = formatting.format_trips(payload)
        self.assertIn("trip 1: 09:48 AM -> 10:28 AM (40 min, $6.15, "
                      "$2.30 with clipper)", out)
        self.assertIn("EMBR -> 10:28 AM MLBR", out)
        self.assertIn("SFO Airport / Millbrae train", out)
        self.assertEqual(out.count("trip "), 4)
        self.assertIn("from BART's own planner", out)

    def test_no_trips(self):
        self.assertIn("no trips", formatting.format_trips({"trips": []}))


class TestAdvisories(unittest.TestCase):
    def test_real_no_advisories_sample(self):
        root = load("bsa.json")["root"]
        items = root["bsa"]
        if isinstance(items, dict):
            items = [items]
        payload = {"as_of": f"{root['date']} {root['time']}",
                   "advisories": [
                       {"station": i.get("station", ""),
                        "description": i.get("description", {})
                        .get("#cdata-section", "")} for i in items]}
        self.assertIn("no advisories",
                      formatting.format_advisories(payload))

    def test_real_advisory_rendered(self):
        payload = {"as_of": "now",
                   "advisories": [{"station": "EMBR",
                                   "description": "10 min delay"}]}
        out = formatting.format_advisories(payload)
        self.assertIn("[EMBR] 10 min delay", out)


class TestStationRow(unittest.TestCase):
    def test_county_cleanup(self):
        row = formatting.format_station(
            {"abbr": "POWL", "name": "Powell St.",
             "city": "San Francisco", "county": "sanfrancisco"})
        self.assertIn("San Francisco Co.", row)
        self.assertNotIn("Sanfrancisco", row)


if __name__ == "__main__":
    unittest.main()
