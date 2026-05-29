from __future__ import annotations

from abc import ABC, abstractmethod

from agent_locate.schema import LocateRequest, LocateResult


class Backend(ABC):
    """Backend protocol for visual grounding providers."""

    name = "base"

    @abstractmethod
    def locate(self, request: LocateRequest) -> LocateResult:
        """Return the best matching target for a natural-language query."""

