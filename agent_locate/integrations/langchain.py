from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from agent_locate.locator import Locator


class AgentLocateToolInput(BaseModel):
    image_path: str = Field(..., description="Path to the screenshot or image.")
    query: str = Field(..., description="Natural-language description of the visual target.")
    context: Optional[str] = Field(None, description="Optional task context.")


def create_langchain_tool(locator: Locator):
    """Create a LangChain StructuredTool that returns AgentLocate response JSON."""

    try:
        from langchain_core.tools import StructuredTool
    except ImportError as exc:
        raise ImportError("Install agent-locate[langchain] to use LangChain integration.") from exc

    def _run(image_path: str, query: str, context: Optional[str] = None) -> str:
        response = locator.locate(image_path, query, context=context)
        return response.model_dump_json()

    return StructuredTool.from_function(
        name="agent_locate",
        description=(
            "Locate a UI element or visual object in an image using natural language. "
            "Returns bbox, center/click coordinates, and automation click snippets."
        ),
        func=_run,
        args_schema=AgentLocateToolInput,
    )

