from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from agent_locate.backends.base import Backend
from agent_locate.schema import BBox, LocateRequest, LocateResult


BOX_PATTERN = re.compile(r"<box><(\d+)><(\d+)><(\d+)><(\d+)></box>")
POINT_PATTERN = re.compile(r"<box><(\d+)><(\d+)></box>")


def parse_locateanything_output(
    answer: str,
    *,
    image_width: int,
    image_height: int,
    label: str = "target",
    backend: str = "locateanything",
    point_box_size: int = 8,
) -> LocateResult:
    """Parse LocateAnything structured text into AgentLocate's pixel bbox schema.

    LocateAnything emits normalized integer coordinates in the range [0, 1000],
    for example `<box><100><200><500><800></box>` or `<box><500><250></box>`.
    """

    box_match = BOX_PATTERN.search(answer)
    if box_match:
        x1, y1, x2, y2 = [int(group) for group in box_match.groups()]
        return LocateResult(
            bbox=BBox(
                x1=_scale_coord(x1, image_width),
                y1=_scale_coord(y1, image_height),
                x2=_scale_coord(x2, image_width),
                y2=_scale_coord(y2, image_height),
            ),
            label=label,
            confidence=None,
            backend=backend,
            raw={"answer": answer},
        )

    point_match = POINT_PATTERN.search(answer)
    if point_match:
        x, y = [int(group) for group in point_match.groups()]
        px = _scale_coord(x, image_width)
        py = _scale_coord(y, image_height)
        half = point_box_size / 2
        return LocateResult(
            bbox=BBox(
                x1=max(0, px - half),
                y1=max(0, py - half),
                x2=min(image_width, px + half),
                y2=min(image_height, py + half),
            ),
            label=label,
            confidence=None,
            backend=backend,
            raw={"answer": answer, "point": {"x": px, "y": py}},
        )

    raise ValueError(f"LocateAnything output did not contain a parseable box or point: {answer!r}")


def _scale_coord(value: int, size: int) -> float:
    return value / 1000 * size


@dataclass
class LocateAnythingWorker:
    """Lazy local worker based on the official Transformers integration."""

    model_path: str
    device: str = "cpu"
    dtype: Optional[str] = None

    def __post_init__(self) -> None:
        try:
            import torch
            from transformers import AutoModel, AutoProcessor, AutoTokenizer
        except ImportError as exc:
            raise ImportError(
                "Install agent-locate[locateanything] and a CPU/GPU PyTorch build "
                "to use the local LocateAnything backend."
            ) from exc

        torch_dtype = _resolve_torch_dtype(torch, self.dtype, self.device)
        self.torch = torch
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path, trust_remote_code=True)
        self.processor = AutoProcessor.from_pretrained(self.model_path, trust_remote_code=True)
        self.model = (
            AutoModel.from_pretrained(
                self.model_path,
                dtype=torch_dtype,
                trust_remote_code=True,
            )
            .to(self.device)
            .eval()
        )
        self.torch_dtype = torch_dtype

    def ground_gui(
        self,
        image: Any,
        phrase: str,
        *,
        output_type: str = "box",
        generation_mode: str = "hybrid",
        max_new_tokens: int = 2048,
        temperature: float = 0.7,
        verbose: bool = False,
        **generate_kwargs: Any,
    ) -> Dict[str, Any]:
        if output_type == "point":
            prompt = f"Point to: {phrase}."
        else:
            prompt = f"Locate the region that matches the following description: {phrase}."
        return self.predict(
            image,
            prompt,
            generation_mode=generation_mode,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            verbose=verbose,
            **generate_kwargs,
        )

    def predict(
        self,
        image: Any,
        question: str,
        *,
        generation_mode: str = "hybrid",
        max_new_tokens: int = 2048,
        temperature: float = 0.7,
        verbose: bool = False,
        **generate_kwargs: Any,
    ) -> Dict[str, Any]:
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": image},
                    {"type": "text", "text": question},
                ],
            }
        ]

        text = self.processor.py_apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        images, videos = self.processor.process_vision_info(messages)
        inputs = self.processor(
            text=[text], images=images, videos=videos, return_tensors="pt"
        ).to(self.device)

        pixel_values = inputs["pixel_values"].to(self.torch_dtype)
        response = self.model.generate(
            pixel_values=pixel_values,
            input_ids=inputs["input_ids"],
            attention_mask=inputs["attention_mask"],
            image_grid_hws=inputs.get("image_grid_hws", None),
            tokenizer=self.tokenizer,
            max_new_tokens=max_new_tokens,
            use_cache=True,
            generation_mode=generation_mode,
            temperature=temperature,
            do_sample=generate_kwargs.pop("do_sample", True),
            top_p=generate_kwargs.pop("top_p", 0.9),
            repetition_penalty=generate_kwargs.pop("repetition_penalty", 1.1),
            verbose=verbose,
            **generate_kwargs,
        )

        result: Dict[str, Any] = {"answer": response[0] if isinstance(response, tuple) else response}
        if isinstance(response, tuple) and len(response) >= 3:
            result["history"] = response[1]
            result["stats"] = response[2]
        return result


class LocateAnythingBackend(Backend):
    """Local backend for nvidia/LocateAnything-3B.

    AgentLocate does not ship model weights. Pass `model_path` pointing at a
    local checkout such as `D:\\models\\LocateAnything-3B`, or inject a worker
    compatible with `ground_gui(image, phrase, output_type="box")`.
    """

    name = "locateanything"

    def __init__(
        self,
        model_path: Optional[str] = None,
        *,
        device: str = "cpu",
        dtype: Optional[str] = None,
        model: Optional[Any] = None,
        output_type: str = "box",
        generation_mode: str = "hybrid",
        max_new_tokens: int = 2048,
        point_box_size: int = 8,
        **generate_kwargs: Any,
    ) -> None:
        self.model_path = model_path
        self.device = device
        self.dtype = dtype
        self.worker = model
        self.output_type = output_type
        self.generation_mode = generation_mode
        self.max_new_tokens = max_new_tokens
        self.point_box_size = point_box_size
        self.generate_kwargs = generate_kwargs

    def locate(self, request: LocateRequest) -> LocateResult:
        image = self._load_image(request.image_path)
        worker = self._get_worker()
        response = worker.ground_gui(
            image,
            request.query,
            output_type=self.output_type,
            generation_mode=self.generation_mode,
            max_new_tokens=self.max_new_tokens,
            **self.generate_kwargs,
        )
        answer = response.get("answer") if isinstance(response, dict) else str(response)
        result = parse_locateanything_output(
            str(answer),
            image_width=image.size[0],
            image_height=image.size[1],
            label=request.query,
            backend=self.name,
            point_box_size=self.point_box_size,
        )
        raw = dict(result.raw)
        raw["model_response"] = response
        return LocateResult(
            bbox=result.bbox,
            label=result.label,
            confidence=result.confidence,
            backend=result.backend,
            raw=raw,
        )

    def _get_worker(self) -> Any:
        if self.worker is not None:
            return self.worker
        if not self.model_path:
            raise ValueError(
                "LocateAnythingBackend requires model_path or an injected worker. "
                "AgentLocate does not include model weights."
            )
        self.worker = LocateAnythingWorker(
            self.model_path,
            device=self.device,
            dtype=self.dtype,
        )
        return self.worker

    def _load_image(self, image_path: str) -> Any:
        try:
            from PIL import Image
        except ImportError as exc:
            raise ImportError("Install agent-locate[local] or Pillow to load local images.") from exc

        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"image not found: {path}")
        return Image.open(path).convert("RGB")


def _resolve_torch_dtype(torch: Any, dtype: Optional[str], device: str) -> Any:
    if dtype:
        if not hasattr(torch, dtype):
            raise ValueError(f"unknown torch dtype: {dtype}")
        return getattr(torch, dtype)
    if device == "cpu":
        return torch.float32
    return torch.bfloat16
