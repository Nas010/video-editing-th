from pathlib import Path

from video_editing_th.io import read_model, write_model_atomic
from video_editing_th.models import EditPlan


def test_atomic_model_write_and_read(tmp_path: Path) -> None:
    destination = tmp_path / "nested" / "edit_plan.json"
    plan = EditPlan(project_id="p1", profile_name="thai-fast-reel")

    write_model_atomic(destination, plan)
    restored = read_model(destination, EditPlan)

    assert restored == plan
    assert list(destination.parent.glob(".*.tmp")) == []
    assert destination.read_text(encoding="utf-8").endswith("\n")
