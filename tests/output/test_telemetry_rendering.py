"""Tests for telemetry tree rendering."""

from __future__ import annotations

from ztlctl.output.renderers import render_result
from ztlctl.services.result import ServiceResult


class TestTelemetryTreeRendering:
    def test_renders_span_tree_when_verbose(self) -> None:
        result = ServiceResult(
            ok=True,
            op="create_note",
            data={"id": "ztl_abc12345", "path": "notes/t.md", "title": "T", "type": "note"},
            meta={
                "telemetry": {
                    "name": "CreateService.create_note",
                    "duration_ms": 3.42,
                    "children": [
                        {"name": "validate", "duration_ms": 0.12},
                        {"name": "persist", "duration_ms": 2.85},
                    ],
                }
            },
        )
        output = render_result(result, verbose=True)
        assert "3.42ms" in output
        assert "validate" in output
        assert "persist" in output

    def test_renders_tokens_and_cost(self) -> None:
        result = ServiceResult(
            ok=True,
            op="context",
            data={"total_tokens": 5000, "budget": 8000, "remaining": 3000, "pressure": "normal"},
            meta={
                "telemetry": {
                    "name": "ContextAssembler.assemble",
                    "duration_ms": 50.0,
                    "tokens": 5000,
                    "children": [
                        {"name": "layer_0_identity", "duration_ms": 2.0, "tokens": 800},
                    ],
                }
            },
        )
        output = render_result(result, verbose=True)
        assert "tokens=5000" in output or "5000" in output

    def test_renders_annotations(self) -> None:
        result = ServiceResult(
            ok=True,
            op="reweave",
            data={"source": "ztl_abc12345", "new_links": 2, "suggestions": []},
            meta={
                "telemetry": {
                    "name": "ReweaveService.reweave",
                    "duration_ms": 15.0,
                    "children": [
                        {"name": "score", "duration_ms": 5.0, "annotations": {"candidates": 12}},
                    ],
                }
            },
        )
        output = render_result(result, verbose=True)
        assert "candidates=12" in output

    def test_no_telemetry_key_renders_normally(self) -> None:
        result = ServiceResult(
            ok=True,
            op="create_note",
            data={"id": "ztl_abc12345", "path": "notes/t.md", "title": "T", "type": "note"},
            meta={"custom_key": "custom_value"},
        )
        output = render_result(result, verbose=True)
        assert "custom_key" in output
        assert "custom_value" in output

    def test_no_meta_renders_cleanly(self) -> None:
        result = ServiceResult(
            ok=True,
            op="create_note",
            data={"id": "ztl_abc12345", "path": "notes/t.md", "title": "T", "type": "note"},
        )
        output = render_result(result, verbose=True)
        assert "ztl_abc12345" in output
