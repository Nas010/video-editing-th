from pathlib import Path

from video_editing_th.config import AppConfig
from video_editing_th.doctor import run_doctor


def test_doctor_distinguishes_required_and_optional_tools(tmp_path: Path) -> None:
    available = {
        "ffmpeg": "/usr/bin/ffmpeg",
        "ffprobe": "/usr/bin/ffprobe",
        "git": "/usr/bin/git",
        "whisper-cli": "/usr/bin/whisper-cli",
    }

    report = run_doctor(
        AppConfig(model_root=tmp_path / "models"),
        which=lambda name: available.get(name),
        faster_whisper_available=False,
        python_version=(3, 12, 1),
    )

    assert report.ready is True
    assert report.by_name("ffmpeg").available is True
    assert report.by_name("auto-editor").required is False
    assert report.by_name("codex").available is False


def test_doctor_is_not_ready_without_transcription_backend(tmp_path: Path) -> None:
    available = {"ffmpeg": "/ffmpeg", "ffprobe": "/ffprobe", "git": "/git"}

    report = run_doctor(
        AppConfig(model_root=tmp_path / "models"),
        which=lambda name: available.get(name),
        faster_whisper_available=False,
        python_version=(3, 12, 1),
    )

    assert report.ready is False
    assert report.by_name("transcription-backend").available is False
