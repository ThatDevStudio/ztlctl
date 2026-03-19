"""Controller layer — thin orchestration wrappers over service layer.

Each controller accepts a Vault and delegates to the corresponding service.
All public methods return ServiceResult (same contract as services).
"""

from __future__ import annotations

from ztlctl.controllers.base import BaseController
from ztlctl.controllers.check import CheckController
from ztlctl.controllers.create import CreateController
from ztlctl.controllers.export import ExportController
from ztlctl.controllers.graph import GraphController
from ztlctl.controllers.ingest import IngestController
from ztlctl.controllers.init_ctrl import InitController
from ztlctl.controllers.query import QueryController
from ztlctl.controllers.reweave import ReweaveController
from ztlctl.controllers.session import SessionController
from ztlctl.controllers.update import UpdateController
from ztlctl.controllers.upgrade import UpgradeController
from ztlctl.controllers.vector import VectorController
from ztlctl.controllers.workflow import WorkflowController

__all__ = [
    "BaseController",
    "CheckController",
    "CreateController",
    "ExportController",
    "GraphController",
    "IngestController",
    "InitController",
    "QueryController",
    "ReweaveController",
    "SessionController",
    "UpdateController",
    "UpgradeController",
    "VectorController",
    "WorkflowController",
]
