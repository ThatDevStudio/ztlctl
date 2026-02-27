# Quick Wins Batch + Semantic Search — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Ship three quick-win features (MCP HTTP transport, local plugin discovery, Alembic migration tests) as one PR, then semantic search with sqlite-vec + local embeddings as a second PR.

**Architecture:** Quick wins are independent additions to existing modules. Semantic search adds a new `VectorService` with `EmbeddingProvider` infrastructure, a sqlite-vec virtual table, and hybrid ranking in `QueryService.search()`. All gated by `SearchConfig.semantic_enabled`.

**Tech Stack:** Python 3.13, Click, FastMCP (mcp 1.26.0), pluggy, Alembic, sqlite-vec, sentence-transformers, SQLAlchemy Core, pytest.

---

## PR 1: Quick Wins Batch

### Task 1: MCP Streamable HTTP Transport (T-012)

**Files:**
- Modify: `src/ztlctl/mcp/server.py:26-53`
- Modify: `src/ztlctl/commands/serve.py:10-38`
- Test: `tests/commands/test_serve.py`

**Step 1: Write failing tests for new transport options**

Add to `tests/commands/test_serve.py`:

```python
def test_serve_help_shows_transports(self, cli_runner: CliRunner) -> None:
    result = cli_runner.invoke(cli, ["serve", "--help"])
    assert "stdio" in result.output
    assert "sse" in result.output
    assert "streamable-http" in result.output

def test_serve_help_shows_host_port(self, cli_runner: CliRunner) -> None:
    result = cli_runner.invoke(cli, ["serve", "--help"])
    assert "--host" in result.output
    assert "--port" in result.output
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/commands/test_serve.py -v`
Expected: FAIL — "sse" and "--host" not in help output.

**Step 3: Update `create_server()` to accept host/port**

In `src/ztlctl/mcp/server.py`, change `create_server()`:

```python
def create_server(
    *,
    vault_root: Path | None = None,
    host: str = "127.0.0.1",
    port: int = 8000,
) -> Any:
    """Create and configure the MCP server.

    Creates a Vault from *vault_root* (or CWD) and registers all tools,
    resources, and prompts. Returns the FastMCP instance.

    *host* and *port* are only meaningful for non-stdio transports.
    """
    if not mcp_available or _FastMCP is None:
        msg = "MCP extra not installed. Install with: pip install ztlctl[mcp]"
        raise RuntimeError(msg)

    from ztlctl.config.settings import ZtlSettings
    from ztlctl.infrastructure.vault import Vault
    from ztlctl.mcp.prompts import register_prompts
    from ztlctl.mcp.resources import register_resources
    from ztlctl.mcp.tools import register_tools

    settings = ZtlSettings.from_cli(vault_root=vault_root)
    vault = Vault(settings)

    server = _FastMCP("ztlctl", host=host, port=port)

    register_tools(server, vault)
    register_resources(server, vault)
    register_prompts(server, vault)

    return server
```

**Step 4: Update `serve` command to accept transport/host/port**

In `src/ztlctl/commands/serve.py`:

```python
"""serve — start the MCP server (requires ztlctl[mcp] extra)."""

from __future__ import annotations

import click

from ztlctl.commands._base import ZtlCommand


@click.command(
    cls=ZtlCommand,
    examples="""\
  # Start the MCP server (stdio transport)
  ztlctl serve

  # Start with streamable HTTP transport
  ztlctl serve --transport streamable-http

  # Start HTTP on custom host/port
  ztlctl serve --transport streamable-http --host 0.0.0.0 --port 9000""",
)
@click.option(
    "--transport",
    default="stdio",
    type=click.Choice(["stdio", "sse", "streamable-http"]),
    help="MCP transport protocol.",
)
@click.option("--host", default="127.0.0.1", help="Bind address (HTTP transports only).")
@click.option("--port", default=8000, type=int, help="Listen port (HTTP transports only).")
@click.pass_obj
def serve(app: object, transport: str, host: str, port: int) -> None:
    """Start the MCP server (requires ztlctl[mcp] extra)."""
    from ztlctl.mcp.server import create_server, mcp_available

    if not mcp_available:
        click.echo("MCP not installed. Install with: pip install ztlctl[mcp]", err=True)
        raise SystemExit(1)

    from ztlctl.commands._context import AppContext

    assert isinstance(app, AppContext)
    server = create_server(vault_root=app.settings.vault_root, host=host, port=port)
    server.run(transport=transport)
```

**Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/commands/test_serve.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add src/ztlctl/mcp/server.py src/ztlctl/commands/serve.py tests/commands/test_serve.py
git commit -m "feat(serve): add streamable-http and sse transport options with host/port"
```

---

### Task 2: Local Plugin Discovery (T-009)

**Files:**
- Modify: `src/ztlctl/plugins/manager.py:20-64`
- Create: `tests/plugins/test_local_discovery.py`

**Step 1: Write failing test for local plugin loading**

Create `tests/plugins/test_local_discovery.py`:

```python
"""Tests for local directory plugin discovery."""

from __future__ import annotations

from pathlib import Path

import pluggy
import pytest

from ztlctl.plugins.hookspecs import ZtlctlHookSpec
from ztlctl.plugins.manager import PluginManager

hookimpl = pluggy.HookimplMarker("ztlctl")


class _DummyPlugin:
    """Minimal plugin used as a test fixture."""

    @hookimpl
    def post_create(
        self,
        content_type: str,
        content_id: str,
        title: str,
        path: str,
        tags: list[str],
    ) -> None:
        pass


def _write_plugin(plugin_dir: Path, name: str, body: str) -> Path:
    """Write a .py plugin file and return its path."""
    p = plugin_dir / f"{name}.py"
    p.write_text(body, encoding="utf-8")
    return p


class TestLocalPluginDiscovery:
    def test_discovers_local_plugin(self, tmp_path: Path) -> None:
        _write_plugin(
            tmp_path,
            "my_plugin",
            '''\
import pluggy

hookimpl = pluggy.HookimplMarker("ztlctl")


class MyPlugin:
    @hookimpl
    def post_init(self, vault_name: str, client: str, tone: str) -> None:
        pass
''',
        )
        pm = PluginManager()
        loaded = pm.discover_and_load(local_dir=tmp_path)
        assert any("my_plugin" in n.lower() or "MyPlugin" in n for n in loaded)

    def test_skips_bad_plugin_gracefully(self, tmp_path: Path) -> None:
        _write_plugin(tmp_path, "bad_plugin", "raise SyntaxError('boom')\n")
        pm = PluginManager()
        # Should not raise — logs warning and continues
        loaded = pm.discover_and_load(local_dir=tmp_path)
        assert "bad_plugin" not in " ".join(loaded)

    def test_no_local_dir_is_noop(self) -> None:
        pm = PluginManager()
        loaded = pm.discover_and_load(local_dir=None)
        # Only entry-point plugins (if any) — no error
        assert isinstance(loaded, list)

    def test_nonexistent_dir_is_noop(self, tmp_path: Path) -> None:
        pm = PluginManager()
        loaded = pm.discover_and_load(local_dir=tmp_path / "does_not_exist")
        assert isinstance(loaded, list)

    def test_local_plugin_hooks_fire(self, tmp_path: Path) -> None:
        _write_plugin(
            tmp_path,
            "tracker",
            '''\
import pluggy

hookimpl = pluggy.HookimplMarker("ztlctl")

calls = []

class TrackerPlugin:
    @hookimpl
    def post_init(self, vault_name: str, client: str, tone: str) -> None:
        calls.append(vault_name)
''',
        )
        pm = PluginManager()
        pm.discover_and_load(local_dir=tmp_path)
        pm.hook.post_init(vault_name="test-vault", client="obsidian", tone="research")
        # Import the module to check its state
        import importlib.util

        spec = importlib.util.spec_from_file_location("tracker", tmp_path / "tracker.py")
        mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        # Note: the module was already loaded by discover, so calls is on the
        # already-imported instance, not this fresh import. We verify via the
        # plugin manager's registered plugins instead.
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/plugins/test_local_discovery.py -v`
Expected: FAIL — `discover_and_load()` doesn't accept `local_dir`.

**Step 3: Implement local plugin discovery**

Replace `src/ztlctl/plugins/manager.py`:

```python
"""Plugin discovery and loading.

Discovery: entry_points (pip-installed) via pluggy setuptools entrypoints,
then local directory scanning for .py files in .ztlctl/plugins/.
"""

from __future__ import annotations

import importlib.util
import logging
import sys
from pathlib import Path

import pluggy

from ztlctl.plugins.hookspecs import ZtlctlHookSpec

PROJECT_NAME = "ztlctl"

logger = logging.getLogger(__name__)


class PluginManager:
    """Manages plugin discovery, loading, and hook dispatch."""

    def __init__(self) -> None:
        self._pm = pluggy.PluginManager(PROJECT_NAME)
        self._pm.add_hookspecs(ZtlctlHookSpec)
        self._loaded: bool = False

    def discover_and_load(self, *, local_dir: Path | None = None) -> list[str]:
        """Discover plugins from entry points and optional local directory.

        Uses pluggy's native setuptools entry_point discovery for the
        ``ztlctl.plugins`` group, then scans *local_dir* for ``.py`` files
        containing plugin classes. Returns a list of loaded plugin names.
        """
        self._pm.load_setuptools_entrypoints("ztlctl.plugins")
        if local_dir is not None:
            self._discover_local(local_dir)
        self._loaded = True
        return self.list_plugin_names()

    def _discover_local(self, local_dir: Path) -> None:
        """Scan a directory for .py plugin files and register them."""
        if not local_dir.is_dir():
            logger.debug("Local plugin dir does not exist: %s", local_dir)
            return

        for py_file in sorted(local_dir.glob("*.py")):
            if py_file.name.startswith("_"):
                continue
            module_name = f"ztlctl_local_plugin_{py_file.stem}"
            try:
                spec = importlib.util.spec_from_file_location(module_name, py_file)
                if spec is None or spec.loader is None:
                    logger.warning("Could not load plugin spec: %s", py_file)
                    continue
                mod = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = mod
                spec.loader.exec_module(mod)
            except Exception:
                logger.warning("Failed to load local plugin %s", py_file, exc_info=True)
                continue

            # Scan module for classes that have hookimpl-decorated methods
            for attr_name in dir(mod):
                obj = getattr(mod, attr_name)
                if not isinstance(obj, type):
                    continue
                if self._has_hook_impls(obj):
                    try:
                        instance = obj()
                        self._pm.register(instance, name=f"local:{py_file.stem}:{attr_name}")
                        logger.debug("Registered local plugin: %s from %s", attr_name, py_file)
                    except Exception:
                        logger.warning(
                            "Failed to instantiate plugin class %s from %s",
                            attr_name,
                            py_file,
                            exc_info=True,
                        )

    @staticmethod
    def _has_hook_impls(cls: type) -> bool:
        """Check if a class has any pluggy hookimpl-decorated methods."""
        for name in dir(cls):
            method = getattr(cls, name, None)
            if method is not None and hasattr(method, "ztlctl_impl"):
                return True
        return False

    def register_plugin(self, plugin: object, name: str | None = None) -> None:
        """Register a plugin instance directly (e.g. built-in plugins)."""
        resolved_name = name or plugin.__class__.__name__
        self._pm.register(plugin, name=resolved_name)
        logger.debug("Registered plugin: %s", resolved_name)

    def unregister(self, plugin: object) -> None:
        """Unregister a plugin instance."""
        self._pm.unregister(plugin)

    @property
    def is_loaded(self) -> bool:
        """Whether discover_and_load() has been called."""
        return self._loaded

    @property
    def hook(self) -> pluggy.HookRelay:
        """Access the hook relay for dispatching events."""
        return self._pm.hook

    def get_plugins(self) -> list[object]:
        """Return all registered plugins."""
        return list(self._pm.get_plugins())

    def list_plugin_names(self) -> list[str]:
        """Return names of all registered plugins."""
        return [self._pm.get_name(p) or p.__class__.__name__ for p in self._pm.get_plugins()]
```

**Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/plugins/test_local_discovery.py -v`
Expected: Some tests may need adjustment — `_has_hook_impls` checks `ztlctl_impl` attribute which is pluggy's internal marker. If tests fail, adjust the detection logic (see step 4a).

**Step 4a: Fix hook detection if needed**

The pluggy `HookimplMarker("ztlctl")` sets an attribute named `ztlctl_impl` on decorated methods. Verify this works:

```python
# Quick check — run in Python REPL if needed:
import pluggy
hookimpl = pluggy.HookimplMarker("ztlctl")
@hookimpl
def foo(): pass
print(hasattr(foo, "ztlctl_impl"))  # Should be True
```

If the attribute name differs, adjust `_has_hook_impls()` accordingly.

**Step 5: Run full test suite**

Run: `uv run pytest -x -q`
Expected: All tests pass. The existing `discover_and_load()` callers don't pass `local_dir`, so they get `None` (noop).

**Step 6: Commit**

```bash
git add src/ztlctl/plugins/manager.py tests/plugins/test_local_discovery.py
git commit -m "feat(plugins): add local directory plugin discovery from .ztlctl/plugins/"
```

---

### Task 3: Alembic Migration Service Tests (T-024)

**Files:**
- Create: `tests/services/test_upgrade.py`

**Step 1: Write the test file**

Create `tests/services/test_upgrade.py`:

```python
"""Tests for UpgradeService — Alembic migration pipeline."""

from __future__ import annotations

import pytest

from ztlctl.infrastructure.vault import Vault
from ztlctl.services.upgrade import UpgradeService


@pytest.mark.usefixtures()
class TestUpgradeService:
    """Integration tests for UpgradeService methods."""

    def test_check_pending_on_fresh_vault(self, vault: Vault) -> None:
        """Freshly initialized vault (stamped at head) has 0 pending."""
        svc = UpgradeService(vault)
        result = svc.check_pending()
        assert result.ok
        assert result.data["pending_count"] == 0
        assert result.data["current"] == result.data["head"]

    def test_apply_already_current(self, vault: Vault) -> None:
        """Applying on an up-to-date vault returns 0 applied."""
        svc = UpgradeService(vault)
        result = svc.apply()
        assert result.ok
        assert result.data["applied_count"] == 0
        assert "already up to date" in result.data.get("message", "").lower()

    def test_stamp_current(self, vault: Vault) -> None:
        """stamp_current() succeeds and reports head revision."""
        svc = UpgradeService(vault)
        result = svc.stamp_current()
        assert result.ok
        assert result.data["stamped"] is True
        assert result.data["current"] is not None

    def test_tables_exist_true(self, vault: Vault) -> None:
        """_tables_exist() returns True when core tables are present."""
        svc = UpgradeService(vault)
        assert svc._tables_exist() is True

    def test_tables_exist_false_on_empty_db(self, tmp_path: pytest.TempPathFactory) -> None:
        """_tables_exist() returns False on a database with no tables."""
        from sqlalchemy import create_engine

        from ztlctl.config.settings import ZtlSettings

        # Create a vault with an empty database (no init_database)
        root = tmp_path if isinstance(tmp_path, __import__("pathlib").Path) else tmp_path.mktemp()
        db_path = root / ".ztlctl" / "ztlctl.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        engine = create_engine(f"sqlite:///{db_path}")
        # Create a minimal vault with the empty engine
        settings = ZtlSettings.from_cli(vault_root=root, no_reweave=True)
        v = Vault.__new__(Vault)
        v._settings = settings
        v._engine = engine
        v._root = root
        v._event_bus = None

        svc = UpgradeService(v)
        assert svc._tables_exist() is False

    def test_check_pending_reports_head_revision(self, vault: Vault) -> None:
        """check_pending always reports the head revision."""
        svc = UpgradeService(vault)
        result = svc.check_pending()
        assert result.ok
        assert result.data["head"] is not None
        assert result.data["head"] == "001_baseline"
```

**Step 2: Run tests to verify they pass**

Run: `uv run pytest tests/services/test_upgrade.py -v`
Expected: Most should pass since they test the real Alembic pipeline on a fresh vault. The `test_tables_exist_false_on_empty_db` test may need adjustment — see step 2a.

**Step 2a: Fix the empty-db test if Vault construction is complex**

The Vault constructor may do more than we need. If Vault's `__init__` runs `init_database()` internally, we may need to avoid it. Check how `Vault.__init__` works and adjust the test to construct a minimal stub. Alternatively, test `_tables_exist()` by directly constructing an UpgradeService with a vault that has an empty-engine:

```python
def test_tables_exist_false_on_empty_db(self, tmp_path: Path) -> None:
    """_tables_exist() returns False on a database with no tables."""
    from pathlib import Path
    from unittest.mock import MagicMock

    from sqlalchemy import create_engine

    db_path = tmp_path / "empty.db"
    engine = create_engine(f"sqlite:///{db_path}")

    mock_vault = MagicMock()
    mock_vault.engine = engine
    mock_vault.root = tmp_path

    svc = UpgradeService(mock_vault)
    assert svc._tables_exist() is False
```

**Step 3: Run full test suite**

Run: `uv run pytest -x -q`
Expected: All tests pass.

**Step 4: Commit**

```bash
git add tests/services/test_upgrade.py
git commit -m "test(upgrade): add UpgradeService integration tests for Alembic pipeline"
```

---

### Task 4: Quick Wins Validation and PR

**Step 1: Run full validation suite**

```bash
uv run ruff check . && uv run ruff format --check . && uv run pytest && uv run mypy src/
```

Fix any issues and commit fixes.

**Step 2: Push and create PR**

```bash
git push -u origin feature/quick-wins-batch-2
gh pr create --base develop --title "feat: quick wins — MCP HTTP transport, local plugin discovery, Alembic tests" --body "$(cat <<'EOF'
## Summary
- **T-012**: Add `--transport sse|streamable-http` and `--host`/`--port` options to `ztlctl serve`
- **T-009**: Add local directory plugin discovery from `.ztlctl/plugins/*.py`
- **T-024**: Add UpgradeService integration tests for Alembic migration pipeline

## Test plan
- [ ] `ztlctl serve --help` shows all 3 transports and host/port options
- [ ] Local plugin `.py` in `.ztlctl/plugins/` is discovered and hooks fire
- [ ] Bad plugin files log warnings without crashing
- [ ] UpgradeService tests cover check_pending, apply, stamp_current, _tables_exist
- [ ] Full test suite passes: `uv run pytest`
- [ ] Lint/format/typecheck clean

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

---

## PR 2: Semantic Search (T-015)

### Task 5: EmbeddingProvider Infrastructure

**Files:**
- Create: `src/ztlctl/infrastructure/embeddings.py`
- Create: `tests/infrastructure/test_embeddings.py`

**Step 1: Write failing tests for EmbeddingProvider**

Create `tests/infrastructure/test_embeddings.py`:

```python
"""Tests for EmbeddingProvider — local sentence-transformers wrapper."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from ztlctl.infrastructure.embeddings import EmbeddingProvider


class TestEmbeddingProvider:
    def test_embed_returns_correct_dimension(self) -> None:
        """embed() returns a list of floats with correct dimension."""
        with patch("ztlctl.infrastructure.embeddings._load_model") as mock_load:
            mock_model = MagicMock()
            mock_model.encode.return_value = [0.1] * 384
            mock_load.return_value = mock_model

            provider = EmbeddingProvider(model_name="test-model", dim=384)
            result = provider.embed("Hello world")
            assert isinstance(result, list)
            assert len(result) == 384
            assert all(isinstance(x, float) for x in result)

    def test_embed_batch_returns_list_of_vectors(self) -> None:
        """embed_batch() returns a list of vectors."""
        with patch("ztlctl.infrastructure.embeddings._load_model") as mock_load:
            import numpy as np

            mock_model = MagicMock()
            mock_model.encode.return_value = np.array([[0.1] * 384, [0.2] * 384])
            mock_load.return_value = mock_model

            provider = EmbeddingProvider(model_name="test-model", dim=384)
            result = provider.embed_batch(["Hello", "World"])
            assert len(result) == 2
            assert all(len(v) == 384 for v in result)

    def test_lazy_model_loading(self) -> None:
        """Model is not loaded until first embed() call."""
        with patch("ztlctl.infrastructure.embeddings._load_model") as mock_load:
            provider = EmbeddingProvider(model_name="test-model", dim=384)
            mock_load.assert_not_called()

            mock_model = MagicMock()
            mock_model.encode.return_value = [0.1] * 384
            mock_load.return_value = mock_model

            provider.embed("trigger load")
            mock_load.assert_called_once()

    def test_is_available_true_when_installed(self) -> None:
        """is_available() returns True when sentence-transformers is importable."""
        with patch("ztlctl.infrastructure.embeddings._st_available", True):
            assert EmbeddingProvider.is_available() is True

    def test_is_available_false_when_missing(self) -> None:
        """is_available() returns False when sentence-transformers is not installed."""
        with patch("ztlctl.infrastructure.embeddings._st_available", False):
            assert EmbeddingProvider.is_available() is False
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/infrastructure/test_embeddings.py -v`
Expected: FAIL — module does not exist.

**Step 3: Implement EmbeddingProvider**

Create `src/ztlctl/infrastructure/embeddings.py`:

```python
"""EmbeddingProvider — local sentence-transformers wrapper.

Lazy-loads the model on first embed() call. Guarded import so the
sentence-transformers package is only required when semantic search is enabled.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

_st_available = False
try:
    import sentence_transformers  # noqa: F401

    _st_available = True
except ImportError:
    pass


def _load_model(model_name: str) -> Any:
    """Load a sentence-transformers model. Raises if not installed."""
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_name)


class EmbeddingProvider:
    """Wraps sentence-transformers for local embedding generation.

    The model is loaded lazily on the first ``embed()`` or ``embed_batch()``
    call to avoid startup cost when semantic search is disabled.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", dim: int = 384) -> None:
        self._model_name = model_name
        self._dim = dim
        self._model: Any = None

    def _ensure_model(self) -> Any:
        if self._model is None:
            self._model = _load_model(self._model_name)
        return self._model

    def embed(self, text: str) -> list[float]:
        """Embed a single text string into a float vector."""
        model = self._ensure_model()
        vec = model.encode(text)
        # sentence-transformers returns ndarray or list
        if hasattr(vec, "tolist"):
            return [float(x) for x in vec.tolist()]
        return [float(x) for x in vec]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple texts into float vectors."""
        model = self._ensure_model()
        vecs = model.encode(texts)
        result: list[list[float]] = []
        for vec in vecs:
            if hasattr(vec, "tolist"):
                result.append([float(x) for x in vec.tolist()])
            else:
                result.append([float(x) for x in vec])
        return result

    @staticmethod
    def is_available() -> bool:
        """Check if sentence-transformers is installed."""
        return _st_available
```

**Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/infrastructure/test_embeddings.py -v`
Expected: PASS (all tests use mocks, no real model download).

**Step 5: Commit**

```bash
git add src/ztlctl/infrastructure/embeddings.py tests/infrastructure/test_embeddings.py
git commit -m "feat(embeddings): add EmbeddingProvider with lazy sentence-transformers loading"
```

---

### Task 6: sqlite-vec Virtual Table and VectorService

**Files:**
- Create: `src/ztlctl/services/vector.py`
- Create: `tests/services/test_vector.py`
- Modify: `src/ztlctl/infrastructure/database/schema.py:140-145` (add vec DDL constant)

**Step 1: Add VEC_CREATE_SQL constant to schema.py**

In `src/ztlctl/infrastructure/database/schema.py`, after line 145 (the FTS5_CREATE_SQL):

```python
# sqlite-vec virtual table DDL — created when semantic search is enabled.
# node_id maps to nodes.id; embedding dimension must match SearchConfig.embedding_dim.
VEC_CREATE_SQL = (
    "CREATE VIRTUAL TABLE IF NOT EXISTS vec_items USING vec0("
    "node_id TEXT PRIMARY KEY, embedding FLOAT[384])"
)
```

**Step 2: Write failing tests for VectorService**

Create `tests/services/test_vector.py`:

```python
"""Tests for VectorService — sqlite-vec vector storage and search."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from ztlctl.infrastructure.vault import Vault


class TestVectorService:
    """Tests using a mock EmbeddingProvider (no real model download)."""

    def _make_mock_provider(self, dim: int = 384) -> MagicMock:
        provider = MagicMock()
        provider.embed.return_value = [0.1] * dim
        provider.embed_batch.return_value = [[0.1] * dim, [0.2] * dim]
        return provider

    def test_is_available_checks_sqlite_vec(self, vault: Vault) -> None:
        from ztlctl.services.vector import VectorService

        svc = VectorService(vault)
        # Returns bool — True if sqlite-vec extension loads, False otherwise
        result = svc.is_available()
        assert isinstance(result, bool)

    def test_index_node_stores_embedding(self, vault: Vault) -> None:
        from ztlctl.services.vector import VectorService

        svc = VectorService(vault, provider=self._make_mock_provider())
        if not svc.is_available():
            pytest.skip("sqlite-vec not available")
        svc.ensure_table()
        svc.index_node("ztl_abc123", "Test note about Python patterns")
        svc._provider.embed.assert_called_once()

    def test_remove_node_deletes_embedding(self, vault: Vault) -> None:
        from ztlctl.services.vector import VectorService

        svc = VectorService(vault, provider=self._make_mock_provider())
        if not svc.is_available():
            pytest.skip("sqlite-vec not available")
        svc.ensure_table()
        svc.index_node("ztl_abc123", "Test note")
        svc.remove_node("ztl_abc123")
        # Search should return no results for this node
        results = svc.search_similar("Test note", limit=5)
        assert all(r["node_id"] != "ztl_abc123" for r in results)

    def test_search_similar_returns_ranked_results(self, vault: Vault) -> None:
        from ztlctl.services.vector import VectorService

        svc = VectorService(vault, provider=self._make_mock_provider())
        if not svc.is_available():
            pytest.skip("sqlite-vec not available")
        svc.ensure_table()
        svc.index_node("ztl_001", "Python design patterns")
        svc.index_node("ztl_002", "JavaScript frameworks")
        results = svc.search_similar("Python patterns", limit=5)
        assert isinstance(results, list)

    def test_reindex_all_processes_nodes(self, vault: Vault) -> None:
        from tests.conftest import create_note

        from ztlctl.services.vector import VectorService

        create_note(vault, "Test Note A")
        create_note(vault, "Test Note B")
        svc = VectorService(vault, provider=self._make_mock_provider())
        if not svc.is_available():
            pytest.skip("sqlite-vec not available")
        svc.ensure_table()
        result = svc.reindex_all()
        assert result.ok
        assert result.data["indexed_count"] >= 2
```

**Step 3: Run tests to verify they fail**

Run: `uv run pytest tests/services/test_vector.py -v`
Expected: FAIL — `VectorService` does not exist.

**Step 4: Implement VectorService**

Create `src/ztlctl/services/vector.py`:

```python
"""VectorService — sqlite-vec vector storage and similarity search.

Requires: sqlite-vec extension, sentence-transformers (via EmbeddingProvider).
All operations gated by is_available() — graceful no-op when deps missing.
"""

from __future__ import annotations

import logging
import struct
from typing import TYPE_CHECKING, Any

from sqlalchemy import text

from ztlctl.services.base import BaseService
from ztlctl.services.result import ServiceError, ServiceResult
from ztlctl.services.telemetry import trace_span, traced

if TYPE_CHECKING:
    from ztlctl.infrastructure.embeddings import EmbeddingProvider

logger = logging.getLogger(__name__)


def _serialize_f32(vec: list[float]) -> bytes:
    """Serialize a float list to a compact binary format for sqlite-vec."""
    return struct.pack(f"{len(vec)}f", *vec)


class VectorService(BaseService):
    """Manages vector embeddings for semantic search."""

    def __init__(
        self,
        vault: Any,
        *,
        provider: EmbeddingProvider | None = None,
    ) -> None:
        super().__init__(vault)
        self._provider = provider
        self._vec_available: bool | None = None

    def _ensure_provider(self) -> EmbeddingProvider:
        if self._provider is None:
            from ztlctl.infrastructure.embeddings import EmbeddingProvider

            cfg = self._vault.settings.search
            self._provider = EmbeddingProvider(
                model_name=cfg.embedding_model
                if cfg.embedding_model != "local"
                else "all-MiniLM-L6-v2",
                dim=cfg.embedding_dim,
            )
        return self._provider

    def is_available(self) -> bool:
        """Check if sqlite-vec extension can be loaded."""
        if self._vec_available is not None:
            return self._vec_available
        try:
            import sqlite_vec  # noqa: F401

            with self._vault.engine.connect() as conn:
                raw = conn.connection.connection  # type: ignore[union-attr]
                sqlite_vec.load(raw)
            self._vec_available = True
        except Exception:
            self._vec_available = False
        return self._vec_available

    def ensure_table(self) -> None:
        """Create the vec_items virtual table if it doesn't exist."""
        if not self.is_available():
            return
        dim = self._vault.settings.search.embedding_dim
        with self._vault.engine.connect() as conn:
            raw = conn.connection.connection  # type: ignore[union-attr]
            import sqlite_vec

            sqlite_vec.load(raw)
            conn.execute(
                text(
                    f"CREATE VIRTUAL TABLE IF NOT EXISTS vec_items "
                    f"USING vec0(node_id TEXT PRIMARY KEY, embedding FLOAT[{dim}])"
                )
            )
            conn.commit()

    @traced
    def index_node(self, node_id: str, content: str) -> None:
        """Embed content and store in vec_items."""
        if not self.is_available():
            return
        provider = self._ensure_provider()
        vec = provider.embed(content)
        blob = _serialize_f32(vec)
        with self._vault.engine.connect() as conn:
            raw = conn.connection.connection  # type: ignore[union-attr]
            import sqlite_vec

            sqlite_vec.load(raw)
            # Upsert: delete then insert (sqlite-vec doesn't support ON CONFLICT)
            conn.execute(text("DELETE FROM vec_items WHERE node_id = :nid"), {"nid": node_id})
            conn.execute(
                text("INSERT INTO vec_items(node_id, embedding) VALUES (:nid, :emb)"),
                {"nid": node_id, "emb": blob},
            )
            conn.commit()

    @traced
    def remove_node(self, node_id: str) -> None:
        """Remove a node's embedding from vec_items."""
        if not self.is_available():
            return
        with self._vault.engine.connect() as conn:
            raw = conn.connection.connection  # type: ignore[union-attr]
            import sqlite_vec

            sqlite_vec.load(raw)
            conn.execute(text("DELETE FROM vec_items WHERE node_id = :nid"), {"nid": node_id})
            conn.commit()

    @traced
    def search_similar(
        self,
        query_text: str,
        *,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Find nodes most similar to query text by cosine distance."""
        if not self.is_available():
            return []
        provider = self._ensure_provider()
        with trace_span("embed_query"):
            query_vec = provider.embed(query_text)
        blob = _serialize_f32(query_vec)

        with self._vault.engine.connect() as conn:
            raw = conn.connection.connection  # type: ignore[union-attr]
            import sqlite_vec

            sqlite_vec.load(raw)
            rows = conn.execute(
                text(
                    "SELECT node_id, distance FROM vec_items "
                    "WHERE embedding MATCH :qvec AND k = :k "
                    "ORDER BY distance"
                ),
                {"qvec": blob, "k": limit},
            ).fetchall()

        return [
            {"node_id": r.node_id, "distance": float(r.distance)}
            for r in rows
        ]

    @traced
    def reindex_all(self) -> ServiceResult:
        """Re-embed all non-archived nodes."""
        op = "vector_reindex"
        if not self.is_available():
            return ServiceResult(
                ok=False,
                op=op,
                error=ServiceError(
                    code="SEMANTIC_UNAVAILABLE",
                    message="sqlite-vec extension not available",
                ),
            )
        provider = self._ensure_provider()

        with self._vault.engine.connect() as conn:
            rows = conn.execute(
                text(
                    "SELECT n.id, n.title, COALESCE(fts.body, '') AS body "
                    "FROM nodes n LEFT JOIN nodes_fts fts ON n.id = fts.id "
                    "WHERE n.archived = 0"
                )
            ).fetchall()

        texts = [f"{r.title} {r.body}".strip() for r in rows]
        node_ids = [r.id for r in rows]

        if not texts:
            return ServiceResult(ok=True, op=op, data={"indexed_count": 0})

        with trace_span("batch_embed"):
            vectors = provider.embed_batch(texts)

        with self._vault.engine.connect() as conn:
            raw = conn.connection.connection  # type: ignore[union-attr]
            import sqlite_vec

            sqlite_vec.load(raw)
            conn.execute(text("DELETE FROM vec_items"))
            for nid, vec in zip(node_ids, vectors):
                blob = _serialize_f32(vec)
                conn.execute(
                    text("INSERT INTO vec_items(node_id, embedding) VALUES (:nid, :emb)"),
                    {"nid": nid, "emb": blob},
                )
            conn.commit()

        return ServiceResult(
            ok=True,
            op=op,
            data={"indexed_count": len(node_ids)},
        )
```

**Step 5: Run tests**

Run: `uv run pytest tests/services/test_vector.py -v`
Expected: Tests that require sqlite-vec will skip if not installed. Mock-based tests should pass.

**Step 6: Commit**

```bash
git add src/ztlctl/infrastructure/database/schema.py src/ztlctl/services/vector.py tests/services/test_vector.py
git commit -m "feat(vector): add VectorService with sqlite-vec storage and similarity search"
```

---

### Task 7: Hybrid Ranking in QueryService

**Files:**
- Modify: `src/ztlctl/services/query.py:46-135`
- Modify: `src/ztlctl/config/models.py:72-79` (add `semantic_weight`)
- Create: `tests/services/test_query_semantic.py`

**Step 1: Add `semantic_weight` to SearchConfig**

In `src/ztlctl/config/models.py`, add to `SearchConfig` class:

```python
class SearchConfig(BaseModel):
    """[search] section."""

    model_config = {"frozen": True}

    semantic_enabled: bool = False
    embedding_model: str = "local"
    embedding_dim: int = 384
    half_life_days: float = 30.0
    semantic_weight: float = 0.5
```

**Step 2: Write failing tests for semantic/hybrid ranking**

Create `tests/services/test_query_semantic.py`:

```python
"""Tests for semantic and hybrid search ranking in QueryService."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from ztlctl.infrastructure.vault import Vault
from ztlctl.services.query import QueryService
from tests.conftest import create_note


class TestHybridRanking:
    def test_search_with_semantic_rank_by(self, vault: Vault) -> None:
        """rank_by='semantic' triggers vector search."""
        create_note(vault, "Python Patterns")
        create_note(vault, "Design Patterns in Go")
        svc = QueryService(vault)

        # Mock vector service to return results
        mock_vec = MagicMock()
        mock_vec.is_available.return_value = True
        mock_vec.search_similar.return_value = [
            {"node_id": "ztl_001", "distance": 0.1},
            {"node_id": "ztl_002", "distance": 0.5},
        ]

        with patch.object(svc, "_get_vector_service", return_value=mock_vec):
            result = svc.search("patterns", rank_by="semantic")

        assert result.ok

    def test_search_with_hybrid_rank_by(self, vault: Vault) -> None:
        """rank_by='hybrid' combines BM25 and vector scores."""
        create_note(vault, "Python Patterns")
        svc = QueryService(vault)

        mock_vec = MagicMock()
        mock_vec.is_available.return_value = True
        mock_vec.search_similar.return_value = [
            {"node_id": "ztl_001", "distance": 0.1},
        ]

        with patch.object(svc, "_get_vector_service", return_value=mock_vec):
            result = svc.search("Python", rank_by="hybrid")

        assert result.ok

    def test_semantic_unavailable_falls_back(self, vault: Vault) -> None:
        """When vector service unavailable, semantic search returns warning."""
        create_note(vault, "Fallback Test")
        svc = QueryService(vault)

        mock_vec = MagicMock()
        mock_vec.is_available.return_value = False

        with patch.object(svc, "_get_vector_service", return_value=mock_vec):
            result = svc.search("Fallback", rank_by="semantic")

        assert result.ok
        assert any("semantic" in w.lower() for w in result.warnings)
```

**Step 3: Run tests to verify they fail**

Run: `uv run pytest tests/services/test_query_semantic.py -v`
Expected: FAIL — `rank_by="semantic"` not supported, `_get_vector_service` doesn't exist.

**Step 4: Add semantic/hybrid ranking to QueryService**

In `src/ztlctl/services/query.py`, add these changes:

1. Add `_get_vector_service()` method:

```python
def _get_vector_service(self) -> Any:
    """Lazy-create VectorService for semantic search."""
    from ztlctl.services.vector import VectorService
    return VectorService(self._vault)
```

2. In `search()` method, add handling for `rank_by="semantic"` and `rank_by="hybrid"` after the existing `use_time_decay` / `use_graph_rank` logic. Add a new branch:

```python
use_semantic = rank_by == "semantic"
use_hybrid = rank_by == "hybrid"

# ... (existing FTS5 search for all modes except pure semantic) ...

if use_semantic:
    # Pure vector search — FTS5 not needed
    vec_svc = self._get_vector_service()
    if not vec_svc.is_available():
        warnings.append("Semantic search unavailable — returning FTS5 results")
        # Fall through to FTS5 results
    else:
        vec_results = vec_svc.search_similar(query, limit=limit)
        # Convert distances to similarity scores and join with node metadata
        ...

elif use_hybrid:
    # Weighted merge of BM25 + cosine
    vec_svc = self._get_vector_service()
    if not vec_svc.is_available():
        warnings.append("Semantic search unavailable — using FTS5 only")
    else:
        vec_results = vec_svc.search_similar(query, limit=fetch_limit)
        # Normalize and merge scores
        ...
```

The exact implementation should:
- For `semantic`: query vector service directly, join results with node metadata from DB
- For `hybrid`: run FTS5 AND vector search, min-max normalize both score sets, weighted merge using `SearchConfig.semantic_weight`

**Step 5: Run tests**

Run: `uv run pytest tests/services/test_query_semantic.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add src/ztlctl/config/models.py src/ztlctl/services/query.py tests/services/test_query_semantic.py
git commit -m "feat(search): add semantic and hybrid rank_by modes to QueryService"
```

---

### Task 8: CLI Surface for Semantic Search

**Files:**
- Modify: `src/ztlctl/commands/query.py` (add `--rank-by` choices)
- Create: `src/ztlctl/commands/vector.py` (new `vector` command group)
- Modify: `src/ztlctl/cli.py` (register vector group)
- Create: `tests/commands/test_vector.py`

**Step 1: Write failing tests**

Create `tests/commands/test_vector.py`:

```python
"""Tests for the vector CLI command group."""

from __future__ import annotations

import json

import pytest
from click.testing import CliRunner

from ztlctl.cli import cli


class TestVectorCommandGroup:
    def test_vector_registered(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["--help"])
        assert "vector" in result.output

    def test_vector_status(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["vector", "status"])
        # May fail if sqlite-vec not installed — that's OK, just check no crash
        assert result.exit_code in (0, 1)

    @pytest.mark.usefixtures("_isolated_vault")
    def test_vector_status_json(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(cli, ["--json", "vector", "status"])
        assert result.exit_code in (0, 1)
        data = json.loads(result.output)
        assert "ok" in data
```

**Step 2: Implement vector command group and update search --rank-by**

Create `src/ztlctl/commands/vector.py` with `status` and `reindex` subcommands.

Update `src/ztlctl/commands/query.py` to add `"semantic"` and `"hybrid"` to the `--rank-by` Click.Choice.

Register the vector group in `src/ztlctl/cli.py`.

**Step 3: Run tests**

Run: `uv run pytest tests/commands/test_vector.py -v`
Expected: PASS

**Step 4: Commit**

```bash
git add src/ztlctl/commands/vector.py src/ztlctl/commands/query.py src/ztlctl/cli.py tests/commands/test_vector.py
git commit -m "feat(cli): add vector command group and semantic/hybrid rank-by options"
```

---

### Task 9: Dependencies and Integration

**Files:**
- Modify: `pyproject.toml` (add sentence-transformers to semantic extra)
- Modify: `src/ztlctl/services/create.py` (call VectorService.index_node after persist)
- Modify: `src/ztlctl/services/update.py` (re-index on title/body change)

**Step 1: Update pyproject.toml**

Add `sentence-transformers` to the `semantic` optional dependency group:

```toml
semantic = ["sqlite-vec", "sentence-transformers"]
```

**Step 2: Wire indexing into CreateService**

In `CreateService`, after the PERSIST stage and before RESPOND, add:

```python
# VECTOR INDEX (if semantic search enabled)
if self._vault.settings.search.semantic_enabled:
    from ztlctl.services.vector import VectorService
    vec_svc = VectorService(self._vault)
    if vec_svc.is_available():
        vec_svc.index_node(node_id, f"{title} {body}")
```

**Step 3: Wire indexing into UpdateService**

Similar pattern — re-index when title or body changes.

**Step 4: Run full test suite**

Run: `uv run pytest -x -q`
Expected: All tests pass. Vector indexing is guarded by `semantic_enabled` (default False), so existing tests are unaffected.

**Step 5: Commit**

```bash
git add pyproject.toml src/ztlctl/services/create.py src/ztlctl/services/update.py
git commit -m "feat(semantic): wire vector indexing into create and update pipelines"
```

---

### Task 10: Semantic Search Validation and PR

**Step 1: Run full validation suite**

```bash
uv run ruff check . && uv run ruff format --check . && uv run pytest && uv run mypy src/
```

Fix any issues and commit fixes.

**Step 2: Push and create PR**

```bash
git push -u origin feature/semantic-search
gh pr create --base develop --title "feat(search): add semantic search with sqlite-vec and local embeddings" --body "$(cat <<'EOF'
## Summary
- **EmbeddingProvider**: Lazy sentence-transformers wrapper with `embed()` and `embed_batch()`
- **VectorService**: sqlite-vec storage with `index_node()`, `remove_node()`, `search_similar()`, `reindex_all()`
- **Hybrid ranking**: `rank_by=semantic|hybrid` in `QueryService.search()` with configurable weight
- **CLI**: `ztlctl vector status|reindex`, `ztlctl search --rank-by semantic|hybrid`
- **Pipeline integration**: Auto-index on create/update when `semantic_enabled=True`
- All gated by `[search] semantic_enabled = true` (default: false)

## Test plan
- [ ] `EmbeddingProvider` tests with mock model (no download)
- [ ] `VectorService` tests skip when sqlite-vec not installed
- [ ] Hybrid ranking normalizes and merges scores correctly
- [ ] `ztlctl vector status` reports availability
- [ ] Existing tests unaffected (semantic_enabled defaults to false)
- [ ] Full test suite passes: `uv run pytest`
- [ ] Lint/format/typecheck clean

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```
