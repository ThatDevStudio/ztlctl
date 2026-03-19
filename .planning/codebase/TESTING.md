# Testing

## Framework & Configuration

- **Framework:** pytest 9.0.2
- **Runner:** `uv run pytest`
- **Config location:** `pyproject.toml`

```ini
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --tb=short"
```

### Coverage

```ini
[tool.coverage.run]
source = ["ztlctl"]
branch = true
omit = [
    "src/ztlctl/__main__.py",
    "src/ztlctl/mcp/*",
    "src/ztlctl/services/session.py",
    "src/ztlctl/services/reweave.py",
    "src/ztlctl/services/check.py",
    "src/ztlctl/plugins/*",
]

[tool.coverage.report]
show_missing = true
fail_under = 80
```

Target: 80% minimum, excluding optional/integration-heavy modules.

## Test Directory Structure

```
tests/
├── conftest.py                    # Root fixtures (6 fixtures + 4 helpers)
├── commands/                      # CLI integration tests (27 files)
├── config/                        # Settings & discovery tests (4 files)
├── domain/                        # Domain layer tests (IDs, content models)
├── infrastructure/                # Database, repositories tests
│   ├── database/
│   │   └── test_*.py             # Engine, schema, counters
│   └── repositories/
│       └── test_query_repo.py
├── services/                      # Business logic tests (21 files)
├── plugins/                       # Event bus, git plugin, manager tests
├── integration/                   # End-to-end tests (performance, telemetry)
├── output/                        # Formatting & rendering tests
├── mcp/                           # MCP adapter tests
└── [root level]                   # CLI, catalogs, workflows, profiles
```

## Test Counts

- **Total tests:** ~1,300+
- **Test classes:** ~302
- **Test files:** 98 Python files
- **Total test code:** ~37,900 lines

### Breakdown by Area

| Area | Approx Count | Description |
|------|-------------|-------------|
| Services | 300+ | CreateService, QueryService, GraphService, etc. |
| Commands | 250+ | CLI integration via CliRunner |
| Infrastructure | 100+ | Database, schema, repositories |
| Plugins | 50+ | Event bus, git plugin, manager |
| Integration | 20+ | Performance regression, telemetry |
| Config | 30+ | Settings, discovery, logging |
| Domain | 50+ | IDs, content models, enums |
| Output | 50+ | Rich/JSON formatters |

## Naming Conventions

- **Files:** `test_<module_name>.py` (mirrors source structure)
- **Classes:** `class Test<Scenario>:` (e.g., `TestCreateNote`)
- **Functions:** `def test_<behavior>(self, ...) -> None:`

## Core Fixtures

### Root Fixtures (`tests/conftest.py`)

```python
@pytest.fixture
def cli_runner() -> CliRunner:
    """Provide a Click CLI test runner."""
    return CliRunner()

@pytest.fixture
def db_engine(tmp_path: Path) -> Engine:
    """Initialized SQLite engine with all tables created."""
    engine = init_database(tmp_path)
    yield engine
    engine.dispose()

@pytest.fixture
def vault_root(tmp_path: Path) -> Path:
    """Temporary vault directory with basic structure."""
    (tmp_path / "notes").mkdir()
    (tmp_path / "ops" / "logs").mkdir(parents=True)
    (tmp_path / "ops" / "tasks").mkdir(parents=True)
    return tmp_path

@pytest.fixture
def vault(vault_root: Path) -> Vault:
    """Fully initialized vault on a temp directory."""
    settings = ZtlSettings.from_cli(vault_root=vault_root, no_reweave=True)
    v = Vault(settings)
    yield v
    v.close()

@pytest.fixture
def _isolated_vault(vault_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Change CWD to temp vault root so CLI creates isolated vault."""
    monkeypatch.chdir(vault_root)
```

### Helper Functions (`tests/conftest.py`)

```python
create_note(vault, title, **kwargs)      # Creates note via CreateService, asserts success
create_reference(vault, title, **kwargs)  # Creates reference, asserts success
create_task(vault, title, **kwargs)       # Creates task, asserts success
create_decision(vault, title, **kwargs)   # Creates decision note, asserts success
start_session(vault, topic)               # Starts session via SessionService, asserts success
```

All follow pattern: call service method → assert `.ok` → return `.data`.

## Testing Patterns

### Service Testing (Unit)

Services receive `Vault` via constructor (inheriting from `BaseService`):

```python
class TestCreateNote:
    def test_basic_note(self, vault: Vault) -> None:
        svc = CreateService(vault)
        result = svc.create_note("Test Note")
        assert result.ok
        assert result.data["title"] == "Test Note"
```

### Multi-Service Workflows

```python
def test_create_then_query(self, vault: Vault) -> None:
    create_svc = CreateService(vault)
    note = create_svc.create_note("Test").data

    query_svc = QueryService(vault)
    found = query_svc.get_note(note["id"])
    assert found.ok
```

### CLI Command Testing (Integration)

```python
@pytest.mark.usefixtures("_isolated_vault")
class TestCreateNoteCommand:
    def test_create_note(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["create", "note", "CLI Note"])
        assert result.exit_code == 0
```

`@pytest.mark.usefixtures("_isolated_vault")` used ~51 times across CLI tests.

### Mocking Patterns

| Pattern | Usage Count | Typical Use |
|---------|------------|-------------|
| `pytest.MonkeyPatch` | 44+ | Env vars, CWD, settings overrides |
| `unittest.mock.patch()` | 13+ | Subprocess calls, function patches |
| Manual mock objects | Various | `RecordingPlugin`, `FailingPlugin` |

**Git plugin mocking:**
```python
with patch("subprocess.run") as mock_run:
    mock_run.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="", stderr=""
    )
    plugin.post_create(...)
```

**Settings override:**
```python
def test_all_defaults(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ZTLCTL_VAULT_ROOT", raising=False)
    settings = ZtlSettings.from_cli(vault_root=tmp_path)
```

### Assertion Patterns

- `assert result.ok` — primary pattern for service results
- `assert result.exit_code == 0` — CLI testing
- `pytest.raises(Exception)` — 23 exception test cases
- Direct DB assertions via SQLAlchemy `select()` + `execute()`

### Parametrize

```python
@pytest.mark.parametrize("content_type", ["note", "reference", "task"])
def test_create_all_types(self, vault, content_type): ...
```

## Test Execution

```bash
uv run pytest                              # Run all tests
uv run pytest path/to/test.py::test_name   # Run single test
uv run pytest -v --tb=short               # Verbose with short tracebacks
uv run pytest --cov                        # With coverage
```

## Key Testing Notes

- **Frozen Pydantic models** can't be mocked with `patch.object`; use TOML config override instead
- **FTS5 updates** use DELETE + INSERT in tests (FTS5 virtual tables don't support UPDATE)
- **FK bypass** for corruption testing: `PRAGMA foreign_keys=OFF` needed to insert corrupted data
- **Cross-service imports** in tests: mock target where class is defined, not where used
- **Pydantic BaseSettings**: `monkeypatch.setenv()` is overridden by Click's default kwargs passed to `from_cli()`
- **`list_items(limit=0)`** returns 0 items (SQL LIMIT 0); use large limit (10000) for counting
