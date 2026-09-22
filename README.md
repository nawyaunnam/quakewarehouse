# QuakeWarehouse — incremental earthquake warehouse

An incremental SQLite warehouse for earthquake observations with revision-aware upserts, invalid-record quarantine, batch lineage, and analytical SQL.

**Focus:** Data engineering / incremental ETL / data quality / dimensional SQL · Python 3.11+ · Standard library · Offline demo

## Tech stack

| Layer | Technologies used |
| --- | --- |
| Language | Python 3.11+ |
| Storage | SQLite fact, quarantine, and batch-audit tables |
| ETL | Revision-aware upserts, content hashes, contract validation |
| Analytics | SQL group-by aggregates and indexed event timestamps |
| Live source | USGS GeoJSON earthquake feed |
| Dashboard | HTML5, CSS, vanilla JavaScript; Python HTTP server |
| Data transport | urllib.request, verified TLS, JSON, ETag caching |
| Testing and CI | unittest, GitHub Actions; Python 3.11–3.13 matrix |

The implementation uses the Python standard library; no external Python packages are required.

## Run in two commands

From this project directory:

```sh
python3 demo.py
python3 -m unittest discover -v
```

No API keys, paid services, or package downloads are required. The offline demo uses
synthetic or hand-authored examples and temporary storage; it does not access
personal data. See [demo output](demo-output.txt) for a captured local run.

## Design

USGS GeoJSON → normalized observation contract → batch fingerprint → transactional validation and upsert → fact table + quarantine + run audit → regional magnitude aggregates. Event IDs are natural keys; only newer source revisions replace existing facts.

## Review the implementation

- [Core implementation](engine.py): domain logic and persistence/algorithms.
- [Executable demo](demo.py): a complete sample workflow.
- [Tests](test_engine.py): expected behavior and edge/failure cases.
- [Architecture and interview notes](DESIGN.md).
- GitHub Actions runs the tests and demo on Python 3.11–3.13 after publishing.

## Scope and limits

SQLite analytical prototype. Region uses the source network code rather than inferred political boundaries. No cloud warehouse or scheduler is required. Upstream deletions are not represented by the summary feed; a reconciliation process is needed for them.

This is a portfolio implementation, not evidence of production use or business
impact. Any reported metrics describe only the included demonstration data.

## Live public-data workflow

Loads the real [USGS feed](https://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson.php) into a persistent local warehouse. Repeated snapshots are content-addressed; revised earthquakes update existing rows and invalid magnitudes are quarantined.

```sh
python3 live.py                         # Fetch real public data, save snapshot.json and report.json
python3 live.py --replay snapshot.json   # Reproduce analysis from the captured data
python3 dashboard.py                    # Open http://127.0.0.1:8090
# In a separate terminal, to keep fetching while viewing the dashboard:
python3 live.py --watch 120
```

The report includes acquisition timestamps and source URLs. HTTP requests use
verified TLS, timeouts, bounded retries, ETags, and a minimum polling interval.
Network failures are explicit; synthetic data is never substituted for live data.
`demo.py` remains an offline synthetic example for tests and onboarding.

The dashboard is a local demonstration, not a publicly deployed service.
Stop the dashboard and live collector with Ctrl+C. Automated CI runs offline tests;
it does not repeatedly call third-party APIs.

## Verified run

- **9 automated tests passed** locally on Python 3.14.
- Live data was fetched successfully; [captured report](live-report.json).
- [Snapshot](snapshot.json) records real data and source acquisition timestamps.
- Offline replay was verified from a fresh temporary working directory.
- [Test log](test-output.txt) and [demo log](demo-output.txt) are included.

To inspect the bundled report without fetching data:

```sh
python3 dashboard.py --report live-report.json
```

## Next engineering milestone

Port facts to PostgreSQL or a columnar warehouse and implement source-deletion reconciliation.

## License and provenance

Original code: [MIT](LICENSE). [Source attribution](DATA-SOURCES.md).
