from __future__ import annotations

from typing import Any, Optional

from agent_locate.backends.base import Backend
from agent_locate.schema import LocateRequest, LocateResult


class LocateAnythingBackend(Backend):
    """Local backend placeholder for nvidia/LocateAnything-3B integration.

    AgentLocate intentionally does not ship model weights. Install and load
    nvidia/LocateAnything-3B according to its official repository and license,
    then wire the actual model/pipeline object into this backend.
    """

    name = "locateanything"

    def __init__(
        self,
        model_path: Optional[str] = None,
        *,
        device: str = "cuda",
        model: Optional[Any] = None,
        processor: Optional[Any] = None,
    ) -> None:
        self.model_path = model_path
        self.device = device
        self.model = model
        self.processor = processor

    def locate(self, request: LocateRequest) -> LocateResult:
        if self.model is None:
            raise NotImplementedError(
                "LocateAnythingBackend requires a loaded LocateAnything-3B model. "
                "AgentLocate does not include model weights. TODO: initialize the "
                "official nvidia/LocateAnything-3B pipeline here and convert its "
                "output into LocateResult."
            )

        # TODO: Implement once the official local inference API is selected:
        # 1. Load request.image_path.
        # 2. Run nvidia/LocateAnything-3B with request.query.
        # 3. Convert model output to BBox(x1, y1, x2, y2), confidence, and raw metadata.
        raise NotImplementedError("Local LocateAnything-3B inference adapter is not implemented yet.")

