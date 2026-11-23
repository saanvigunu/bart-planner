"""Client tests: time conversion, error handling and payload shaping.

No live network - urlopen is stubbed with the committed samples.
"""

import json
import os
import unittest
from unittest import mock

from bartplanner import api

SAMPLES = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "data", "samples")


def sample(name):
    with open(os.path.join(SAMPLES, name), encoding="utf-8") as fh:
        return fh.read()


class FakeResponse:
    def __init__(self, text):
        self.text = text

    def read(self):
        return self.text.encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class TestTimeConversion(unittest.TestCase):
    def test_24h_to_bart(self):
        self.assertEqual(api._to_bart_time("17:30"), "5:30pm")
        self.assertEqual(api._to_bart_time("00:15"), "12:15am")
        self.assertEqual(api._to_bart_time("12:00"), "12:00pm")
        self.assertEqual(api._to_bart_time("9:05"), "9:05am")

    def test_passthrough_bart_format(self):
        self.assertEqual(api._to_bart_time("5:30pm"), "5:30pm")

    def test_bad_time_rejected(self):
        with self.assertRaises(api.BartApiError):
            api._to_bart_time("99:99")
        with self.assertRaises(api.BartApiError):
            api._to_bart_time("soon")


class TestPayloads(unittest.TestCase):
    def test_departures_shapes_etd(self):
        with mock.patch("urllib.request.urlopen",
                        return_value=FakeResponse(sample("etd_embr.json"))):
            payload = api.departures("EMBR")
        self.assertEqual(payload["stations"][0]["name"], "Embarcadero")
        self.assertIn("11/22/2026", payload["as_of"])

    def test_trip_shapes_schedule(self):
        with mock.patch("urllib.request.urlopen",
                        return_value=FakeResponse(sample("depart_embr_mlbr.json"))):
            payload = api.trip("EMBR", "MLBR", "17:30")
        self.assertEqual(len(payload["trips"]), 4)
        self.assertEqual(payload["trips"][0]["@fare"], "6.15")

    def test_advisories_shapes_bsa(self):
        with mock.patch("urllib.request.urlopen",
                        return_value=FakeResponse(sample("bsa.json"))):
            payload = api.advisories()
        self.assertEqual(payload["advisories"][0]["description"],
                         "No advisories issued.")

    def test_api_error_surfaces_details(self):
        body = json.dumps({"root": {"message": {"error": {
            "text": "Invalid cmd", "details": "bad cmd"}}}})
        with mock.patch("urllib.request.urlopen",
                        return_value=FakeResponse(body)):
            with self.assertRaises(api.BartApiError) as ctx:
                api.advisories()
        self.assertIn("Invalid cmd", str(ctx.exception))

    def test_network_failure_wrapped(self):
        with mock.patch("urllib.request.urlopen", side_effect=OSError("down")):
            with self.assertRaises(api.BartApiError) as ctx:
                api.departures("EMBR")
        self.assertIn("could not reach", str(ctx.exception))

    def test_message_as_plain_string_is_not_an_error(self):
        # BART sometimes sends "message" as a string, not an object
        body = json.dumps({"root": {"message": "", "bsa": []}})
        with mock.patch("urllib.request.urlopen",
                        return_value=FakeResponse(body)):
            payload = api.advisories()
        self.assertEqual(payload["advisories"], [])


if __name__ == "__main__":
    unittest.main()
