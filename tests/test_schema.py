import pytest
from pydantic import ValidationError

from zref.schema import PoseDetail, Subject, VisionSchema


def test_schema_minimal_roundtrip() -> None:
    s = VisionSchema(image_summary="A test scene.", subjects=[Subject(pose=PoseDetail(overall="standing"))])
    d = s.model_dump()
    s2 = VisionSchema.model_validate(d)
    assert s2.subjects[0].pose.overall == "standing"


def test_schema_rejects_unknown_field() -> None:
    with pytest.raises(ValidationError):
        VisionSchema.model_validate({"foo": 1})
