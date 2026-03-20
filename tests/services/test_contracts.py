"""Tests for typed payload contracts at service/adapter boundaries."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from tests.conftest import create_note, start_session
from ztlctl.infrastructure.vault import Vault
from ztlctl.services.contracts import (
    AgentContextFallbackData,
    AgentContextResultData,
    ListItemsResultData,
    SearchResultData,
)
from ztlctl.services.query import QueryService
from ztlctl.services.session import SessionService


class TestPayloadContracts:
    def test_search_payload_conforms(self, vault: Vault) -> None:
        create_note(vault, "Contract Search Note")
        result = QueryService(vault).search("Contract")
        assert result.ok
        payload = SearchResultData.model_validate(result.data)
        assert payload.count >= 1
        assert payload.items

    def test_list_items_payload_conforms(self, vault: Vault) -> None:
        create_note(vault, "Contract List Note")
        result = QueryService(vault).list_items()
        assert result.ok
        payload = ListItemsResultData.model_validate(result.data)
        assert payload.count >= 1
        assert payload.items

    def test_session_context_payload_conforms(self, vault: Vault) -> None:
        start_session(vault, "Contracts")
        create_note(vault, "Contract Context Note", topic="contracts")
        result = SessionService(vault).context(topic="contracts")
        assert result.ok
        payload = AgentContextResultData.model_validate(result.data)
        assert payload.layers.session.topic == "Contracts"

    def test_mcp_fallback_context_payload_conforms(self, vault: Vault) -> None:
        create_note(vault, "Contract Fallback Note")
        # Replicate the fallback context path (no active session) via QueryService
        svc = QueryService(vault)
        count_result = svc.count_items()
        recent = svc.list_items(sort="recency", limit=5)
        search_result = svc.search("Contract", limit=5)
        work_result = svc.work_queue()
        context: dict = {}
        if count_result.ok:
            context["total_items"] = count_result.data.get("count", 0)
        if recent.ok:
            context["recent"] = recent.data.get("items", [])
        if search_result.ok:
            context["search_results"] = search_result.data.get("items", [])
        if work_result.ok:
            context["work_queue"] = work_result.data.get("items", [])
        payload = AgentContextFallbackData.model_validate(context)
        assert payload.total_items >= 1

    def test_search_contract_rejects_wrong_key(self) -> None:
        with pytest.raises(ValidationError):
            SearchResultData.model_validate(
                {
                    "query": "x",
                    "count": 1,
                    "results": [],
                }
            )

    def test_context_contract_rejects_missing_layers(self) -> None:
        with pytest.raises(ValidationError):
            AgentContextResultData.model_validate(
                {
                    "total_tokens": 100,
                    "budget": 8000,
                    "remaining": 7900,
                    "pressure": "normal",
                }
            )
