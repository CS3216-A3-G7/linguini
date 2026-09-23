"""Local Grounding DINO adapter for precise object locations.

The vision model supplies useful vocabulary labels. This adapter receives only
those labels and finds their pixels, so the numbered marker does not depend on
the vision model estimating normalized coordinates.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from io import BytesIO
from typing import Protocol

from app.services.vision_model import VisionImage


class ObjectGroundingError(RuntimeError):
    """The optional detector could not produce usable locations."""


@dataclass(frozen=True)
class GroundedBox:
    """A detector result in normalized image coordinates."""

    x: float
    y: float
    width: float
    height: float
    score: float


class ObjectGrounder(Protocol):
    def ground(
        self, image: VisionImage, labels: Sequence[str]
    ) -> Mapping[str, GroundedBox]: ...


class GroundingDinoObjectGrounder:
    """Zero-shot detector backed by ``IDEA-Research/grounding-dino-base``.

    Imports and model loading are deliberately lazy. Deployments that do not
    opt into grounding do not need PyTorch, Transformers, or model weights.
    """

    def __init__(self, model_name: str, threshold: float) -> None:
        try:
            import torch
            from transformers import AutoModelForZeroShotObjectDetection, AutoProcessor
        except ImportError as error:
            raise ObjectGroundingError(
                "Grounding DINO needs the 'grounding' backend extra. "
                "Install it before setting AI_OBJECT_GROUNDING_PROVIDER=groundingDino."
            ) from error

        self._torch = torch
        self._processor = AutoProcessor.from_pretrained(model_name)
        self._model = AutoModelForZeroShotObjectDetection.from_pretrained(model_name)
        self._threshold = threshold

    def ground(
        self, image: VisionImage, labels: Sequence[str]
    ) -> Mapping[str, GroundedBox]:
        if not labels:
            return {}
        try:
            from PIL import Image, ImageOps

            source = ImageOps.exif_transpose(Image.open(BytesIO(image.data))).convert("RGB")
            width, height = source.size
            best: dict[str, GroundedBox] = {}
            # A single query identifies the requested class without relying on
            # generated text_labels (which may drop words or merge phrases).
            for label in dict.fromkeys(labels):
                inputs = self._processor(
                    images=source, text=f"{_canonical_label(label)}.", return_tensors="pt"
                )
                with self._torch.no_grad():
                    outputs = self._model(**inputs)
                results = self._processor.post_process_grounded_object_detection(
                    outputs,
                    inputs.input_ids,
                    threshold=self._threshold,
                    text_threshold=self._threshold,
                    target_sizes=[(height, width)],
                )[0]
                for box, score in zip(results["boxes"], results["scores"], strict=True):
                    left, top, right, bottom = (float(value) for value in box.tolist())
                    normalized = _normalize_box(
                        left, top, right, bottom, width, height, float(score)
                    )
                    if normalized is not None and (
                        label not in best or normalized.score > best[label].score
                    ):
                        best[label] = normalized
        except Exception as error:
            raise ObjectGroundingError("Grounding DINO could not process this image") from error
        return best


def _canonical_label(label: str) -> str:
    """Match Grounding DINO's prompt phrase (for example, ``a pizza``)."""
    normalized = " ".join(label.casefold().strip().rstrip(".").split())
    for article in ("a ", "an ", "the "):
        if normalized.startswith(article):
            return normalized.removeprefix(article)
    return normalized


def _normalize_box(
    left: float, top: float, right: float, bottom: float, width: int, height: int, score: float
) -> GroundedBox | None:
    left, right = sorted((max(0.0, left), min(float(width), right)))
    top, bottom = sorted((max(0.0, top), min(float(height), bottom)))
    if right <= left or bottom <= top:
        return None
    return GroundedBox(
        x=left / width,
        y=top / height,
        width=(right - left) / width,
        height=(bottom - top) / height,
        score=score,
    )
