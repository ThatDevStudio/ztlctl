"""Controller layer — thin orchestration wrappers over service layer.

Each controller accepts a Vault and delegates to the corresponding service.
All public methods return ServiceResult (same contract as services).
"""

from __future__ import annotations

from ztlctl.controllers.check import CheckController
from ztlctl.controllers.export import ExportController
from ztlctl.controllers.graph import GraphController
from ztlctl.controllers.reweave import ReweaveController
from ztlctl.controllers.upgrade import UpgradeController
from ztlctl.controllers.vector import VectorController

__all__ = [
    "CheckController",
    "ExportController",
    "GraphController",
    "ReweaveController",
    "UpgradeController",
    "VectorController",
]
