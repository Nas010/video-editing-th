from pathlib import Path

from video_editing_th.io import read_model
from video_editing_th.models import ProjectManifest, ProjectStatus
from video_editing_th.project import initialize_project


def test_initialize_project_creates_runtime_layout_without_touching_source(tmp_path: Path) -> None:
    source = tmp_path / "raw.mov"
    source.write_bytes(b"source")
    original_bytes = source.read_bytes()
    profile = tmp_path / "profile.yaml"
    profile.write_text(
        "name: test\nversion: 1\nlanguage: th\n",
        encoding="utf-8",
    )

    manifest = initialize_project(tmp_path, profile)

    assert manifest.status == ProjectStatus.INITIALIZED
    assert manifest.root == tmp_path.resolve()
    assert source.read_bytes() == original_bytes
    for name in ["analysis", "transcripts", "plans", "renders", "qa", "tmp"]:
        assert (tmp_path / "edit" / name).is_dir()
    persisted = read_model(tmp_path / "edit" / "project.json", ProjectManifest)
    assert persisted.project_id == manifest.project_id
    assert persisted.profile_name == "test"


def test_initialize_project_is_idempotent(tmp_path: Path) -> None:
    profile = tmp_path / "profile.yaml"
    profile.write_text("name: test\nversion: 1\nlanguage: th\n", encoding="utf-8")

    first = initialize_project(tmp_path, profile)
    second = initialize_project(tmp_path, profile)

    assert first.project_id == second.project_id
    assert first.created_at == second.created_at
