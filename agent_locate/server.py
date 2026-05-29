from __future__ import annotations

import os
from typing import Any, Dict

from agent_locate.locator import Locator
from agent_locate.schema import ErrorResponse, LocateRequest, LocateResponse


def create_app():
    try:
        from fastapi import FastAPI, HTTPException
    except ImportError as exc:
        raise ImportError("Install agent-locate[server] to use the FastAPI server.") from exc

    app = FastAPI(
        title="AgentLocate API",
        version="0.1.0",
        description="Natural-language visual localization service for AI agents and automation.",
    )

    @app.get("/health")
    def health() -> Dict[str, str]:
        return {"status": "ok"}

    @app.post("/locate", response_model=LocateResponse, responses={500: {"model": ErrorResponse}})
    def locate(request: LocateRequest) -> LocateResponse:
        try:
            locator = _locator_from_env()
            return locator.locate(
                request.image_path,
                request.query,
                top_k=request.top_k,
                context=request.context,
                metadata=request.metadata,
            )
        except Exception as exc:  # FastAPI boundary: return a typed HTTP error.
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    return app


def _locator_from_env() -> Locator:
    backend = os.getenv("AGENT_LOCATE_BACKEND", "locateanything")
    kwargs: Dict[str, Any] = {}
    if backend == "remote_api":
        endpoint = os.getenv("AGENT_LOCATE_REMOTE_ENDPOINT")
        if not endpoint:
            raise ValueError("AGENT_LOCATE_REMOTE_ENDPOINT is required for remote_api backend")
        kwargs["endpoint"] = endpoint
        if os.getenv("AGENT_LOCATE_API_KEY"):
            kwargs["api_key"] = os.getenv("AGENT_LOCATE_API_KEY")
    elif backend in {"locateanything", "locateanything-3b", "local"}:
        if os.getenv("AGENT_LOCATE_MODEL_PATH"):
            kwargs["model_path"] = os.getenv("AGENT_LOCATE_MODEL_PATH")
        kwargs["device"] = os.getenv("AGENT_LOCATE_DEVICE", "cuda")
    return Locator(backend=backend, backend_kwargs=kwargs, validate_images=False)


app = create_app()


def main() -> None:
    try:
        import uvicorn
    except ImportError as exc:
        raise ImportError("Install agent-locate[server] to run the server CLI.") from exc

    uvicorn.run("agent_locate.server:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")))

