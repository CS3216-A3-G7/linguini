from uuid import uuid4

from app.ai.features.object_grounding import GroundedBox
from app.ai.features.object_grounding.mapping import apply_object_grounding
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
