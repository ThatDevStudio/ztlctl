# Category 11: Cross-Cutting Concerns — BAT Critique

**Tests**: BAT-120 through BAT-130
**Score**: 11/11 PASS

## Test Results

| BAT | Test | Result |
|-----|------|--------|
| BAT-120 | JSON Output Mode | **PASS** |
| BAT-121 | JSON Output — Error | **PASS** |
| BAT-122 | Quiet Output — Mutation | **PASS** |
| BAT-123 | Quiet Output — List | **PASS** |
| BAT-124 | Quiet Output — Error | **PASS** |
| BAT-125 | Verbose Output — Telemetry Tree | **PASS** |
| BAT-126 | Non-Interactive Mode | **PASS** |
| BAT-127 | Telemetry — Verbose Spans | **PASS** |
| BAT-128 | Telemetry — JSON Logs | **PASS** |
| BAT-129 | Dual Machine Output | **PASS** |
| BAT-130 | Telemetry Disabled — Zero Overhead | **PASS** |

## Detailed Evaluation

### BAT-120: JSON Output Mode — PASS
- **Correctness**: `--json` produces valid JSON with keys `ok`, `op`, `data`, `warnings`, `error`, `meta`. No ANSI escapes. `ok=true`, `op="create_note"`.
- **Feature value**: Essential for machine consumption. Clean, consistent envelope.

### BAT-121: JSON Output — Error — PASS
- **Correctness**: Error output is valid JSON on stderr with `ok=false`, `error.code="NOT_FOUND"`. Exit code 1.
- **Design**: stdout vs stderr routing is correct — errors go to stderr even in JSON mode.

### BAT-122: Quiet Output — Mutation — PASS
- **Correctness**: Single line: `OK: create_note`. Minimal, scriptable.
- **Feature value**: Perfect for piping and scripting workflows.

### BAT-123: Quiet Output — List — PASS
- **Correctness**: Exactly 3 bare IDs, one per line. No table formatting.
- **Feature value**: `ztlctl -q query list | xargs ...` pipeline-friendly.

### BAT-124: Quiet Output — Error — PASS
- **Correctness**: `ERROR: get — No content found with ID 'ztl_nonexist'`. Exit code 1.
- **UX**: Error format is human-readable but terse. Good for scripts that check exit codes.

### BAT-125: Verbose Output — Telemetry Tree — PASS
- **Correctness**: Hierarchical span tree with durations (e.g., `6.09ms CreateService.create_note` with child spans). Rich-formatted.
- **Feature value**: Debugging and performance insight without code changes. The hierarchical tree reveals exactly where time is spent.

### BAT-126: Non-Interactive Mode — PASS
- **Correctness**: `--no-interact` creates vault with no prompts. 10 files scaffolded.
- **Feature value**: Essential for CI/CD and agent automation.

### BAT-127: Telemetry — Verbose Spans — PASS
- **Correctness**: `meta.telemetry.name = "CreateService.create_note"`, `duration_ms = 6.13` (> 0), `children` array with 5 sub-spans.
- **Feature value**: Machine-readable telemetry embedded in JSON output. Valuable for performance monitoring.

### BAT-128: Telemetry — JSON Logs — PASS
- **Correctness**: JSONL on stderr with structured spans. Each line has `event`, `level`, `timestamp`. DEBUG entries present with -v flag.
- **Feature value**: Log aggregation-friendly. Enables integration with observability tools.

### BAT-129: Dual Machine Output — PASS
- **Correctness**: stdout = clean ServiceResult JSON, stderr = JSONL structured logs. No cross-contamination.
- **Feature value**: Two independent machine-parseable streams on separate file descriptors. Excellent design for automation.

### BAT-130: Telemetry Disabled — Zero Overhead — PASS
- **Correctness**: `meta: null` without `-v`. No telemetry injected.
- **Feature value**: Opt-in telemetry with zero overhead when disabled. Important for production performance.

## Observations

**Strengths**:
- Three output modes (default/quiet/json) serve their intended audiences cleanly
- Consistent behavior across success and error paths in all modes
- Stream discipline is correct: stdout carries results, stderr carries diagnostics
- Telemetry is hierarchical, opt-in, zero-overhead when disabled, and embeds in JSON
- `--json --log-json` dual mode produces two clean non-interfering streams
- Non-interactive mode enables full automation

**Weaknesses**:
- Some JSONL log lines from plugin paths lack `level` and `timestamp` fields (minor inconsistency)
- Error JSON duplication on stdout+stderr is a minor issue shared across all categories

## Usefulness Rating: 9.5/10

Cross-cutting concerns are excellently implemented. The three output modes, opt-in telemetry with hierarchical spans, structured logging, and stream discipline show mature engineering. This is the kind of plumbing that makes a CLI tool genuinely useful for both humans and machines. The dual machine output mode (`--json --log-json`) is particularly noteworthy — it enables sophisticated automation without compromise.
