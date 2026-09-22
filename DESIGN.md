# Engineering notes: QuakeWarehouse — incremental earthquake warehouse

## Problem and flow

USGS GeoJSON → normalized observation contract → batch fingerprint → transactional validation and upsert → fact table + quarantine + run audit → regional magnitude aggregates. Event IDs are natural keys; only newer source revisions replace existing facts.

## Current boundaries

SQLite analytical prototype. Region uses the source network code rather than inferred political boundaries. No cloud warehouse or scheduler is required. Upstream deletions are not represented by the summary feed; a reconciliation process is needed for them.

## Interview walkthrough

1. Run the demo and explain each output in terms of the code.
2. Show a test that exercises a failure rather than only a successful call.
3. Trace one input through the core implementation and its stored state.
4. Explain the tradeoff made by the current storage or algorithm choice.
5. Describe what would change with 100× the data or concurrent users.
6. Make a small extension and add a regression test before using this in a resume.

## Validation

See `test_engine.py` for executable assertions and `docs/demo-output.txt` for
captured results. CI is configured but remote CI results are not assumed.
