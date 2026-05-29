from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, Union

from agent_locate.backends.base import Backend
from agent_locate.backends.locateanything import LocateAnythingBackend
from agent_locate.backends.mock import MockBackend
from agent_locate.backends.remote_api import RemoteAPIBackend
from agent_locate.codegen import generate_click_code
from agent_locate.image_utils import ensure_image_exists
from agent_locate.schema import LocateRequest, LocateResponse


BackendLike = Union[str, Backend]


class Locator:
    """High-level SDK entry point for natural-language visual localization."""

    def __init__(
        self,
        backend: BackendLike = "locateanything",
        *,
        backend_kwargs: Optional[Dict[str, Any]] = None,
        validate_images: bool = False,
    ) -> None:
        self.backend = self._resolve_backend(backend, backend_kwargs or {})
        self.validate_images = validate_images

    def locate(
        self,
        image_path: str | Path,
        query: str,
        *,
        top_k: int = 1,
        context: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> LocateResponse:
        if self.validate_images:
            ensure_image_exists(image_path)

        request = LocateRequest(
            image_path=str(image_path),
            query=query,
            top_k=top_k,
            context=context,
            metadata=metadata or {},
        )
        result = self.backend.locate(request)
        return LocateResponse(request=request, result=result, codegen=generate_click_code(result))

    def _resolve_backend(self, backend: BackendLike, kwargs: Dict[str, Any]) -> Backend:
        if isinstance(backend, Backend):
            return backend

        if backend == "remote_api":
            return RemoteAPIBackend(**kwargs)
        if backend in {"mock", "demo", "test"}:
            return MockBackend(**kwargs)
        if backend in {"locateanything", "locateanything-3b", "local"}:
            return LocateAnythingBackend(**kwargs)

        raise ValueError(f"unknown backend: {backend}")
