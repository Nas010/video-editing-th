"""Portable installation of the repository skill for Codex-compatible agents."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from .errors import ConfigurationError

SKILL_NAME = "video-editing-th"


def locate_skill_source(
    *,
    repository_root: Path | None = None,
    install_prefix: Path | None = None,
) -> Path:
    """Locate the source checkout skill or the wheel-installed data copy."""

    root = repository_root or Path(__file__).resolve().parents[2]
    prefix = install_prefix or Path(sys.prefix)
    candidates = (
        root / "skills" / SKILL_NAME,
        prefix / "share" / "video-editing-th" / "skill",
    )
    for candidate in candidates:
        resolved = candidate.expanduser().resolve(strict=False)
        if (resolved / "SKILL.md").is_file():
            return resolved
    raise FileNotFoundError("Could not locate the video-editing-th skill data")


def install_skill_links(
    source: Path,
    *,
    codex_home: Path,
    agents_home: Path,
) -> tuple[Path, Path]:
    """Symlink the complete skill directory into Codex and `.agents` homes."""

    resolved_source = source.expanduser().resolve(strict=True)
    if not (resolved_source / "SKILL.md").is_file():
        raise ConfigurationError(f"Skill source has no SKILL.md: {resolved_source}")

    destinations = (
        codex_home.expanduser().resolve(strict=False) / "skills" / SKILL_NAME,
        agents_home.expanduser().resolve(strict=False) / "skills" / SKILL_NAME,
    )
    for destination in destinations:
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.is_symlink():
            current = destination.resolve(strict=False)
            if current == resolved_source:
                continue
            destination.unlink()
        elif destination.exists():
            raise ConfigurationError(
                f"Refusing to replace non-symlink skill destination: {destination}"
            )
        os.symlink(resolved_source, destination, target_is_directory=True)
    return destinations
