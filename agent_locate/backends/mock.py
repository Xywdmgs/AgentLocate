from __future__ import annotations

from typing import Sequence

from agent_locate.backends.base import Backend
from agent_locate.schema import BBox, LocateRequest, LocateResult


class MockBackend(Backend):
    """Deterministic backend for installation checks, examples, and CI.

    This backend does not perform real visual grounding. It makes the SDK fully
    runnable without a GPU or remote model service, so users can verify their
    integration before connecting a real backend.
    """

    name = "mock"

    def __init__(self, bbox: Sequence[float] = (100, 100, 260, 180), confidence: float = 1.0) -> None:
        if len(bbox) != 4:
            raise ValueError("mock bbox must contain four values: x1, y1, x2, y2")
        self.bbox = BBox(x1=bbox[0], y1=bbox[1], x2=bbox[2], y2=bbox[3])
        self.confidence = confidence

    def locate(self, request: LocateRequest) -> LocateResult:
        return LocateResult(
            bbox=self.bbox,
            label=request.query,
            confidence=self.confidence,
            backend=self.name,
            raw={"note": "MockBackend returns a fixed bbox for smoke testing only."},
        )

