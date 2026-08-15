"""Read-only environment diagnostics for the portable editing pipeline."""

from __future__ import annotations

import importlib.util
import shutil
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from .config import AppConfig

Which = Callable[[str], str | None]


@dataclass(frozen=True, slots=True)
class DoctorCheck:
    """One dependency or capability reported by :func:`run_doctor`."""

    name: str
    available: bool
    required: bool
    detail: str
    path: Path | None = None


@dataclass(frozen=True, slots=True)
class DoctorReport:
    """Aggregated environment readiness report."""

    checks: tuple[DoctorCheck, ...]

    @property
    def ready(self) -> bool:
        return all(check.available for check in self.checks if check.required)

    def by_name(self, name: str) -> DoctorCheck:
        for check in self.checks:
            if check.name == name:
                return check
        raise KeyError(name)


def run_doctor(
    config: AppConfig,
    *,
    which: Which = shutil.which,
    faster_whisper_available: bool | None = None,
    python_version: tuple[int, int, int] | None = None,
) -> DoctorReport:
    """Inspect the current machine without installing or mutating anything."""

    version = python_version or (
        sys.version_info.major,
        sys.version_info.minor,
        sys.version_info.micro,
    )
    python_ok = version >= (3, 11, 0)
    if faster_whisper_available is None:
        faster_whisper_available = importlib.util.find_spec("faster_whisper") is not None

    checks: list[DoctorCheck] = [
        DoctorCheck(
            name="python",
            available=python_ok,
            required=True,
            detail=f"Python {version[0]}.{version[1]}.{version[2]} (requires >= 3.11)",
            path=Path(sys.executable),
        )
    ]

    def executable_check(name: str, binary: str, *, required: bool) -> DoctorCheck:
        resolved = which(binary)
        return DoctorCheck(
            name=name,
            available=resolved is not None,
            required=required,
            detail=resolved or f"{binary!r} was not found on PATH",
            path=Path(resolved) if resolved else None,
        )

    checks.extend(
        [
            executable_check("ffmpeg", config.ffmpeg_binary, required=True),
            executable_check("ffprobe", config.ffprobe_binary, required=True),
            executable_check("git", "git", required=True),
        ]
    )
    whisper = executable_check(
        "whisper-cli",
        config.whisper_cpp_binary,
        required=False,
    )
    checks.append(whisper)
    checks.append(
        DoctorCheck(
            name="faster-whisper",
            available=faster_whisper_available,
            required=False,
            detail=(
                "Python package is importable"
                if faster_whisper_available
                else "Optional faster-whisper package is not installed"
            ),
        )
    )
    checks.append(
        DoctorCheck(
            name="transcription-backend",
            available=whisper.available or faster_whisper_available,
            required=True,
            detail=(
                "At least one local transcription backend is available"
                if whisper.available or faster_whisper_available
                else "Install whisper.cpp or the faster-whisper optional dependency"
            ),
        )
    )
    checks.extend(
        [
            executable_check(
                "auto-editor",
                config.auto_editor_binary,
                required=False,
            ),
            executable_check("codex", "codex", required=False),
        ]
    )
    model_root = config.model_root
    checks.append(
        DoctorCheck(
            name="model-cache",
            available=model_root.exists(),
            required=False,
            detail=(
                f"Model cache: {model_root}"
                if model_root.exists()
                else f"Model cache will be created at {model_root}"
            ),
            path=model_root if model_root.exists() else None,
        )
    )
    return DoctorReport(checks=tuple(checks))
