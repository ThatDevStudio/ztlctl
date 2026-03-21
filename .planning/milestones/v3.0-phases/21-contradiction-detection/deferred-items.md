# Deferred Items — Phase 21

## Pre-existing Test Failure (Out of Scope)

**File:** `tests/integration/test_verbose_telemetry.py::TestVerboseTelemetry::test_verbose_json_includes_telemetry_in_meta`

**Error:** `json.decoder.JSONDecodeError: Extra data: line 41 column 1`

**Discovered during:** Phase 21 Plan 02 full regression run

**Status:** Pre-existing failure confirmed present before Plan 02 changes (verified via git stash). Not caused by contradiction detection work. The test parses multi-line JSON structured logs and fails due to extra JSON content in the captured output.

**Owner:** Future cleanup phase
