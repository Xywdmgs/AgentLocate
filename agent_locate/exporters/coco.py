from __future__ import annotations

from typing import Any, Dict

from agent_locate.schema import LocateResult


def to_coco_annotation(
    result: LocateResult,
    *,
    image_id: int,
    category_id: int = 1,
    annotation_id: int = 1,
) -> Dict[str, Any]:
    """Convert one result to a COCO annotation dictionary."""

    x, y, width, height = result.bbox.xywh
    return {
        "id": annotation_id,
        "image_id": image_id,
        "category_id": category_id,
        "bbox": [float(x), float(y), float(width), float(height)],
        "area": float(width * height),
        "iscrowd": 0,
        "score": result.confidence,
    }

