from __future__ import annotations

import base64
import mimetypes
from pathlib import Path
from typing import Tuple


def ensure_image_exists(image_path: str | Path) -> Path:
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"image not found: {path}")
    if not path.is_file():
        raise FileNotFoundError(f"image path is not a file: {path}")
    return path


def image_to_base64(image_path: str | Path) -> str:
    path = ensure_image_exists(image_path)
    return base64.b64encode(path.read_bytes()).decode("ascii")


def image_to_data_url(image_path: str | Path) -> str:
    path = ensure_image_exists(image_path)
    return f"data:{image_mime_type(path)};base64,{image_to_base64(path)}"


def image_mime_type(image_path: str | Path) -> str:
    path = Path(image_path)
    return mimetypes.guess_type(path.name)[0] or "application/octet-stream"


def get_image_size(image_path: str | Path) -> Tuple[int, int]:
    try:
        from PIL import Image
    except ImportError as exc:
        raise ImportError("Install agent-locate[local] or pillow to read image dimensions.") from exc

    path = ensure_image_exists(image_path)
    with Image.open(path) as image:
        return image.size
