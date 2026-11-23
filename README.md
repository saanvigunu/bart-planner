# bart-planner

A small BART helper CLI built on BART's official API: real-time departures,
trip plans and service advisories, with fuzzy station names.

I got tired of opening the BART site just to answer "when's the next train
and which platform", so this puts the answer in the terminal. Everything it
shows comes from BART itself.

## usage

```bash
python3 -m bartplanner stations [search]        # list/search all 50 stations (offline)
python3 -m bartplanner next embarcadero         # real-time departures
python3 -m bartplanner next 12th --north        # direction filter
python3 -m bartplanner trip embarcadero millbrae
python3 -m bartplanner trip powell dubl --time 17:30
python3 -m bartplanner trip powell dubl --time 18:00 --arrive-by
python3 -m bartplanner advisories
```

Stations resolve by code (`EMBR`) or fuzzy name (`powell`, `12th`,
`civic center`). Ambiguous names list the matches instead of guessing.

stdlib only, nothing to install. Run the tests with:

```bash
python3 -m unittest discover    # 25 tests, no network needed
```

## where the data comes from

- Live departures, trips and advisories: BART's official API
  (`api.bart.gov`), called fresh on every command - nothing cached.
- Trip times, fares and routing are computed by BART's own schedule
  endpoint, not by me; the CLI just makes them readable.
- `stations` works offline from `data/stations.json`, a snapshot of BART's
  station list fetched 2026-11-22 (the file header says so).
- The default API key is the public one from BART's own documentation;
  set `BART_API_KEY` to use your own.

## honesty notes

- Real-time departure estimates are BART's predictions, shown with the
  timestamp the API returned - trains do what trains do.
- Fuzzy matching prefers showing you the candidates over picking one
  silently.
- The sample responses in `data/samples/` are real API responses captured
  2026-11-22; the tests pin against them, so they test the parser against
  what BART actually sends.
