from __future__ import annotations

from typing import Any, Dict, Optional

import httpx

from agent_locate.backends.base import Backend
from agent_locate.image_utils import image_to_base64, image_mime_type
from agent_locate.schema import BBox, LocateRequest, LocateResult


class RemoteAPIBackend(Backend):
    """HTTP backend for GPU hosts or managed inference services.

    The remote endpoint should accept a JSON-encoded LocateRequest and return either:
    {"bbox": {"x1": ..., "y1": ..., "x2": ..., "y2": ...}, "label": "...", ...}
    or {"result": {same shape as above}}.
    """

    name = "remote_api"

    def __init__(
        self,
        endpoint: str,
        *,
        api_key: Optional[str] = None,
        timeout: float = 60.0,
        headers: Optional[Dict[str, str]] = None,
        include_image: bool = False,
    ) -> None:
        self.endpoint = endpoint
        self.api_key = api_key
        self.timeout = timeout
        self.headers = headers or {}
        self.include_image = include_image

    def locate(self, request: LocateRequest) -> LocateResult:
        headers = dict(self.headers)
        if self.api_key:
            headers.setdefault("Authorization", f"Bearer {self.api_key}")

        payload = request.model_dump()
        if self.include_image:
            metadata = dict(payload.get("metadata") or {})
            metadata["image_base64"] = image_to_base64(request.image_path)
            metadata["image_mime_type"] = image_mime_type(request.image_path)
            payload["metadata"] = metadata
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(self.endpoint, json=payload, headers=headers)
            response.raise_for_status()

        data = response.json()
        result_data = data.get("result", data)
        return self._parse_result(result_data)

    def _parse_result(self, data: Dict[str, Any]) -> LocateResult:
        bbox_data = data.get("bbox")
        if bbox_data is None:
            raise ValueError("remote response must contain a bbox field")

        return LocateResult(
            bbox=BBox.model_validate(bbox_data),
            label=data.get("label") or data.get("text") or "target",
            confidence=data.get("confidence"),
            backend=data.get("backend") or self.name,
            raw=data,
        )
