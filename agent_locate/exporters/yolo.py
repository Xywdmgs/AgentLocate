from __future__ import annotations

from agent_locate.schema import LocateResult


def to_yolo_line(result: LocateResult, *, image_width: int, image_height: int, class_id: int = 0) -> str:
    """Convert one result to a YOLO detection line: class cx cy w h."""

    cx, cy = result.center
    width = result.bbox.width
    height = result.bbox.height
    return (
        f"{class_id} "
        f"{cx / image_width:.6f} "
        f"{cy / image_height:.6f} "
        f"{width / image_width:.6f} "
        f"{height / image_height:.6f}"
    )

