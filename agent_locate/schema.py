from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator, model_validator


PathLike = Union[str, Path]


class BBox(BaseModel):
    """Pixel-space bounding box in xyxy format."""

    x1: float = Field(..., description="Left coordinate in pixels.")
    y1: float = Field(..., description="Top coordinate in pixels.")
    x2: float = Field(..., description="Right coordinate in pixels.")
    y2: float = Field(..., description="Bottom coordinate in pixels.")

    @model_validator(mode="after")
    def validate_order(self) -> "BBox":
        if self.x2 <= self.x1:
            raise ValueError("x2 must be greater than x1")
        if self.y2 <= self.y1:
            raise ValueError("y2 must be greater than y1")
        return self

    @computed_field
    @property
    def width(self) -> float:
        return self.x2 - self.x1

    @computed_field
    @property
    def height(self) -> float:
        return self.y2 - self.y1

    @computed_field
    @property
    def center(self) -> Tuple[int, int]:
        return (round((self.x1 + self.x2) / 2), round((self.y1 + self.y2) / 2))

    @property
    def xywh(self) -> Tuple[float, float, float, float]:
        return (self.x1, self.y1, self.width, self.height)


class LocateRequest(BaseModel):
    """Input accepted by every AgentLocate backend."""

    image_path: str = Field(..., description="Local screenshot/image path visible to the backend.")
    query: str = Field(..., min_length=1, description="Natural-language target description.")
    top_k: int = Field(1, ge=1, description="Number of candidates requested from the backend.")
    context: Optional[str] = Field(None, description="Optional task or UI context.")
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("image_path", mode="before")
    @classmethod
    def normalize_image_path(cls, value: PathLike) -> str:
        return str(value)


class LocateResult(BaseModel):
    """Single visual grounding result."""

    bbox: BBox
    label: str
    confidence: Optional[float] = Field(None, ge=0, le=1)
    backend: str
    raw: Dict[str, Any] = Field(default_factory=dict)

    @computed_field
    @property
    def center(self) -> Tuple[int, int]:
        return self.bbox.center

    @computed_field
    @property
    def click(self) -> Tuple[int, int]:
        return self.center


class ClickCode(BaseModel):
    playwright: str
    drissionpage: str
    appium: str
    pyautogui: str


class LocateResponse(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    request: LocateRequest
    result: LocateResult
    codegen: ClickCode


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
