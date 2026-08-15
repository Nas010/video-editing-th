"""Hardware-aware whisper.cpp model selection for local Thai ASR.

The model is used only for speech recognition: Thai text, timing, and confidence
signals. Editorial decisions remain with Codex and deterministic pipeline logic.
"""

from __future__ import annotations

import platform
import subprocess
from dataclasses import dataclass
from pathlib import Path

GIB = 1024**3


@dataclass(frozen=True, slots=True)
class WhisperModelSpec:
    """Known multilingual whisper.cpp model artifact."""

    name: str
    disk_mib: int
    quantized: bool
    turbo: bool
    notes: str


MODEL_SPECS: dict[str, WhisperModelSpec] = {
    "large-v3": WhisperModelSpec(
        name="large-v3",
        disk_mib=2960,
        quantized=False,
        turbo=False,
        notes="Maximum-quality baseline; whisper.cpp documents about 3.9 GB runtime memory for large.",
    ),
    "large-v3-q5_0": WhisperModelSpec(
        name="large-v3-q5_0",
        disk_mib=1126,
        quantized=True,
        turbo=False,
        notes="Accuracy-oriented quantized large-v3; preferred accuracy mode on memory-constrained Macs.",
    ),
    "large-v3-turbo": WhisperModelSpec(
        name="large-v3-turbo",
        disk_mib=1536,
        quantized=False,
        turbo=True,
        notes="Faster multilingual large-v3-turbo model.",
    ),
    "large-v3-turbo-q5_0": WhisperModelSpec(
        name="large-v3-turbo-q5_0",
        disk_mib=547,
        quantized=True,
        turbo=True,
        notes="Low-memory production default for 8 GB machines; benchmark Thai accuracy before unattended use.",
    ),
}


@dataclass(frozen=True, slots=True)
class HardwareProfile:
    """Minimal hardware facts needed for local ASR selection."""

    os_name: str
    architecture: str
    memory_gib: float | None

    @property
    def is_apple_silicon(self) -> bool:
        return self.os_name == "Darwin" and self.architecture.lower() in {"arm64", "aarch64"}


@dataclass(frozen=True, slots=True)
class ModelRecommendation:
    """Conservative local-ASR recommendation for an editing workstation."""

    default_model: str
    accuracy_model: str
    full_large_v3_supported: bool
    full_large_v3_recommended: bool
    rationale: str


def detect_hardware() -> HardwareProfile:
    """Detect OS, architecture, and total physical memory without mutating the machine."""

    os_name = platform.system()
    architecture = platform.machine()
    memory_gib = _detect_memory_gib(os_name)
    return HardwareProfile(os_name=os_name, architecture=architecture, memory_gib=memory_gib)


def recommend_whisper_model(hardware: HardwareProfile) -> ModelRecommendation:
    """Choose a model while reserving memory for Codex, browser, and the NLE."""

    memory = hardware.memory_gib
    if memory is not None and memory <= 8.5:
        return ModelRecommendation(
            default_model="large-v3-turbo-q5_0",
            accuracy_model="large-v3-q5_0",
            full_large_v3_supported=memory >= 7.0,
            full_large_v3_recommended=False,
            rationale=(
                "8 GB-class machines share memory with macOS and the editing stack. "
                "Use turbo-q5 for normal runs; use large-v3-q5_0 when accuracy matters most."
            ),
        )
    if memory is not None and memory < 15.0:
        return ModelRecommendation(
            default_model="large-v3-q5_0",
            accuracy_model="large-v3-q5_0",
            full_large_v3_supported=True,
            full_large_v3_recommended=False,
            rationale=(
                "The full large-v3 model can fit, but a quantized large-v3 leaves more memory "
                "for Codex, browser automation, ChatCut, and rendering."
            ),
        )
    if memory is not None and memory >= 15.0:
        return ModelRecommendation(
            default_model="large-v3",
            accuracy_model="large-v3",
            full_large_v3_supported=True,
            full_large_v3_recommended=True,
            rationale="16 GB-class or larger machines can use full large-v3 as the accuracy baseline.",
        )
    return ModelRecommendation(
        default_model="large-v3-q5_0",
        accuracy_model="large-v3",
        full_large_v3_supported=True,
        full_large_v3_recommended=False,
        rationale="Memory could not be detected; use a conservative quantized default.",
    )


def resolve_model_name(requested: str, hardware: HardwareProfile | None = None) -> str:
    """Resolve ``auto`` to a supported model name and validate explicit names."""

    normalized = requested.strip().lower()
    if normalized == "auto":
        return recommend_whisper_model(hardware or detect_hardware()).default_model
    if normalized not in MODEL_SPECS:
        supported = ", ".join(sorted(MODEL_SPECS))
        raise ValueError(f"Unsupported whisper.cpp model {requested!r}; choose one of: {supported}")
    return normalized


def model_path(root: Path, model_name: str) -> Path:
    """Return the canonical local path for a whisper.cpp GGML model."""

    if model_name not in MODEL_SPECS:
        raise ValueError(f"Unknown whisper.cpp model: {model_name}")
    return root.expanduser().resolve(strict=False) / f"ggml-{model_name}.bin"


def installed_models(root: Path) -> tuple[str, ...]:
    """Return supported model names already present in the configured cache."""

    return tuple(name for name in MODEL_SPECS if model_path(root, name).is_file())


def _detect_memory_gib(os_name: str) -> float | None:
    if os_name == "Darwin":
        try:
            result = subprocess.run(
                ["sysctl", "-n", "hw.memsize"],
                check=True,
                capture_output=True,
                text=True,
            )
            return int(result.stdout.strip()) / GIB
        except (OSError, ValueError, subprocess.CalledProcessError):
            return None
    if os_name == "Linux":
        try:
            for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
                if line.startswith("MemTotal:"):
                    kib = int(line.split()[1])
                    return kib * 1024 / GIB
        except (OSError, ValueError, IndexError):
            return None
    return None
