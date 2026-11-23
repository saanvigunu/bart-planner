"""Station lookup tests against the committed BART station snapshot."""

import json
import os
import unittest

from bartplanner.stations import StationIndex, load_stations

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


class TestSnapshot(unittest.TestCase):
    def test_snapshot_has_all_50_stations(self):
        stations = load_stations()
        self.assertEqual(len(stations), 50)

    def test_snapshot_header_is_honest(self):
        with open(os.path.join(DATA, "stations.json"), encoding="utf-8") as fh:
            meta = json.load(fh)
        self.assertIn("api.bart.gov", meta["source"])
        self.assertEqual(meta["fetched_at"], "2026-11-22")

    def test_every_station_complete(self):
        for s in load_stations():
            self.assertTrue(s["abbr"])
            self.assertTrue(s["name"])
            self.assertTrue(s["city"])
            self.assertTrue(-123 < s["lon"] < -121)
            self.assertTrue(37 < s["lat"] < 39)


class TestFind(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index = StationIndex()

    def test_exact_code(self):
        self.assertEqual(self.index.find("EMBR")["name"], "Embarcadero")
        self.assertEqual(self.index.find("embr")["name"], "Embarcadero")

    def test_full_name_case_insensitive(self):
        self.assertEqual(self.index.find("powell st.")["abbr"], "POWL")
        self.assertEqual(self.index.find("Powell")["abbr"], "POWL")

    def test_partial_unique(self):
        self.assertEqual(self.index.find("embarcadero")["abbr"], "EMBR")
        self.assertEqual(self.index.find("millbrae")["abbr"], "MLBR")

    def test_ambiguous_raises_with_matches(self):
        with self.assertRaises(KeyError) as ctx:
            self.index.find("mission")
        abbrs = {s["abbr"] for s in ctx.exception.args[0]}
        self.assertEqual(abbrs, {"16TH", "24TH"})

    def test_unknown_raises_empty(self):
        with self.assertRaises(KeyError) as ctx:
            self.index.find("atlantis")
        self.assertEqual(ctx.exception.args[0], [])


class TestSearch(unittest.TestCase):
    def test_search_by_city(self):
        index = StationIndex()
        hits = index.search("berkeley")
        self.assertTrue(any(s["abbr"] == "DBRK" for s in hits))
        self.assertTrue(any(s["abbr"] == "NBRK" for s in hits))


if __name__ == "__main__":
    unittest.main()
