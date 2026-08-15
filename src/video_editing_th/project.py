"""Creation and persistence of per-footage project workspaces."""

from __future__ import annotations

import platform
import sys
import uuid
from pathlib import Path

from .config import EditingProfile
from .io import read_model, write_model_atomic
from .models import ProjectManifest

RUNTIME_DIRECTORIES = ("analysis", "transcripts", "plans", "renders", "qa", "tmp")


def project_edit_dir(root: Path, name: str = "edit") -> Path:
    return root.expanduser().resolve(strict=False) / name


def initialize_project(
    root: Path,
    profile_path: Path,
    *,
    edit_dir_name: str = "edit",
) -> ProjectManifest:
    """Create an idempotent runtime layout without changing source media."""

    resolved_root = root.expanduser().resolve(strict=True)
    resolved_profile = profile_path.expanduser().resolve(strict=True)
    profile = EditingProfile.load(resolved_profile)
    edit_dir = resolved_root / edit_dir_name
    manifest_path = edit_dir / "project.json"

    if manifest_path.exists():
        return read_model(manifest_path, ProjectManifest)

    edit_dir.mkdir(parents=True, exist_ok=True)
    for directory in RUNTIME_DIRECTORIES:
        (edit_dir / directory).mkdir(exist_ok=True)

    project_id = str(uuid.uuid5(uuid.NAMESPACE_URL, resolved_root.as_uri()))
    manifest = ProjectManifest(
        project_id=project_id,
        root=resolved_root,
        edit_dir=edit_dir,
        profile_path=resolved_profile,
        profile_name=profile.name,
        tool_versions={
            "python": platform.python_version(),
            "platform": sys.platform,
        },
    )
    write_model_atomic(manifest_path, manifest)
    return manifest
