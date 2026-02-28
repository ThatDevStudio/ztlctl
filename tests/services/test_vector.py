"""Tests for VectorService — sqlite-vec vector storage and similarity search."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock

import pytest

from ztlctl.infrastructure.vault import Vault
from ztlctl.services.vector import VectorService, _serialize_f32


class TestSerializeF32:
    def test_serialize_returns_bytes(self) -> None:
        result = _serialize_f32([1.0, 2.0, 3.0])
        assert isinstance(result, bytes)
        assert len(result) == 12  # 3 floats * 4 bytes each

    def test_serialize_roundtrip(self) -> None:
        import struct

        original = [0.1, 0.5, 0.9]
        blob = _serialize_f32(original)
        restored = list(struct.unpack(f"{len(original)}f", blob))
        for o, r in zip(original, restored):
            assert abs(o - r) < 1e-6

    def test_serialize_empty_list(self) -> None:
        result = _serialize_f32([])
        assert result == b""

    def test_serialize_single_element(self) -> None:
        import struct

        result = _serialize_f32([42.0])
        assert len(result) == 4
        (val,) = struct.unpack("f", result)
        assert abs(val - 42.0) < 1e-6


class TestVectorServiceAvailability:
    def test_is_available_returns_bool(self, vault: Vault) -> None:
        svc = VectorService(vault)
        result = svc.is_available()
        assert isinstance(result, bool)
        # sqlite-vec not installed -> False
        assert result is False

    def test_is_available_caches_result(self, vault: Vault) -> None:
        svc = VectorService(vault)
        result1 = svc.is_available()
        result2 = svc.is_available()
        assert result1 == result2
        assert svc._vec_available is not None

    def test_is_available_uses_driver_connection(
        self, monkeypatch: pytest.MonkeyPatch, vault: Vault
    ) -> None:
        raw_conn = object()
        sqlite_vec = MagicMock()
        monkeypatch.setitem(sys.modules, "sqlite_vec", sqlite_vec)

        pool_conn = MagicMock()
        pool_conn.driver_connection = raw_conn
        pool_conn.connection = object()

        sa_conn = MagicMock()
        sa_conn.connection = pool_conn

        connect_ctx = MagicMock()
        connect_ctx.__enter__.return_value = sa_conn
        connect_ctx.__exit__.return_value = False
        monkeypatch.setattr(vault.engine, "connect", MagicMock(return_value=connect_ctx))

        svc = VectorService(vault)

        assert svc.is_available() is True
        sqlite_vec.load.assert_called_once_with(raw_conn)


class TestVectorServiceGracefulDegradation:
    """When sqlite-vec is unavailable, all operations are no-ops."""

    def test_index_node_noop_when_unavailable(self, vault: Vault) -> None:
        provider = MagicMock()
        svc = VectorService(vault, provider=provider)
        # Should not raise, should not call provider
        svc.index_node("ztl_123", "test content")
        provider.embed.assert_not_called()

    def test_remove_node_noop_when_unavailable(self, vault: Vault) -> None:
        svc = VectorService(vault)
        svc.remove_node("ztl_123")  # Should not raise

    def test_search_similar_returns_empty_when_unavailable(self, vault: Vault) -> None:
        svc = VectorService(vault)
        result = svc.search_similar("test query")
        assert result == []

    def test_reindex_all_returns_error_when_unavailable(self, vault: Vault) -> None:
        svc = VectorService(vault)
        result = svc.reindex_all()
        assert not result.ok
        assert result.error is not None
        assert result.error.code == "SEMANTIC_UNAVAILABLE"

    def test_ensure_table_noop_when_unavailable(self, vault: Vault) -> None:
        svc = VectorService(vault)
        svc.ensure_table()  # Should not raise


class TestVectorServiceProvider:
    def test_explicit_provider_used(self, vault: Vault) -> None:
        mock_provider = MagicMock()
        svc = VectorService(vault, provider=mock_provider)
        assert svc._provider is mock_provider

    def test_no_provider_by_default(self, vault: Vault) -> None:
        svc = VectorService(vault)
        assert svc._provider is None
