from contextlib import nullcontext
from io import BytesIO
from unittest.mock import MagicMock
from uuid import uuid4

from PIL import Image

from app.ai.features.object_grounding import GroundedBox
from app.ai.features.object_grounding.mapping import apply_object_grounding
from app.ai.features.object_grounding.service import GroundingDinoObjectGrounder, _canonical_label
from app.schemas.media import AnchorPoint, BoundingBox, SceneObject
from app.services.scene_analysis import SceneAnalysisResult
from app.services.vision_model import VisionImage


class FakeGrounder:
    def __init__(self, boxes):
        self.boxes = boxes
        self.calls = []

    def ground(self, image, labels):
        self.calls.append((image, labels))
        return self.boxes


def _result() -> SceneAnalysisResult:
    return SceneAnalysisResult(
        title="Kitchen",
        objects=[
            SceneObject(
                session_id=uuid4(),
                label="chair",
                bounding_box=BoundingBox(x=0.1, y=0.1, width=0.2, height=0.2),
                anchor_point=AnchorPoint(x=0.15, y=0.15),
            ),
            SceneObject(
                session_id=uuid4(),
                label="table",
                bounding_box=BoundingBox(x=0.5, y=0.1, width=0.2, height=0.2),
            ),
        ],
    )


def test_detector_prompt_labels_match_the_scene_analysis_labels() -> None:
    assert _canonical_label("a pizza") == "pizza"
    assert _canonical_label("an apple.") == "apple"
    assert _canonical_label("the basket") == "basket"


def test_queries_labels_separately_and_accepts_partial_returned_phrase() -> None:
    detector = GroundingDinoObjectGrounder.__new__(GroundingDinoObjectGrounder)
    detector._torch = MagicMock()
    detector._torch.no_grad.side_effect = nullcontext
    detector._model = MagicMock()
    detector._processor = MagicMock()
    detector._threshold = 0.35
    box = MagicMock()
    box.tolist.return_value = [10, 20, 40, 60]
    detector._processor.post_process_grounded_object_detection.side_effect = [
        [{"boxes": [box], "scores": [0.8], "text_labels": ["plant"]}],
        [{"boxes": [], "scores": [], "text_labels": []}],
    ]
    data = BytesIO()
    Image.new("RGB", (100, 100)).save(data, format="PNG")
    boxes = detector.ground(
        VisionImage(data=data.getvalue(), mime_type="image/png"),
        ["hanging plant", "lamp", "hanging plant"],
    )
    assert list(boxes) == ["hanging plant"]
    assert boxes["hanging plant"].score == 0.8
    assert boxes["hanging plant"].x == 0.1
    assert [call.kwargs["text"] for call in detector._processor.call_args_list] == [
        "hanging plant.", "lamp."
    ]


def test_grounding_replaces_the_detector_matched_box_and_anchor() -> None:
    grounder = FakeGrounder(
        {"chair": GroundedBox(x=0.3, y=0.4, width=0.2, height=0.1, score=0.9)}
    )

    result = apply_object_grounding(
        _result(), VisionImage(data=b"image", mime_type="image/png"), grounder
    )

    chair, table = result.objects
    assert chair.bounding_box.model_dump(mode="json") == {
        "x": "0.3",
        "y": "0.4",
        "width": "0.2",
        "height": "0.1",
    }
    assert chair.anchor_point.model_dump(mode="json") == {"x": "0.4", "y": "0.45"}
    assert table.bounding_box.model_dump(mode="json") == {
        "x": "0.5",
        "y": "0.1",
        "width": "0.2",
        "height": "0.2",
    }
    assert grounder.calls[0][1] == ["chair", "table"]
