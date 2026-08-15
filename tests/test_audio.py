from pathlib import Path

from video_editing_th.audio import build_silencedetect_command, parse_silencedetect


def test_parse_silencedetect_pairs_boundaries() -> None:
    stderr = """
[silencedetect @ 0x1] silence_start: 1.25
[silencedetect @ 0x1] silence_end: 2.75 | silence_duration: 1.50
[silencedetect @ 0x1] silence_start: 4.00
[silencedetect @ 0x1] silence_end: 4.40 | silence_duration: 0.40
"""

    intervals = parse_silencedetect(stderr)

    assert [(item.start, item.end, item.duration) for item in intervals] == [
        (1.25, 2.75, 1.5),
        (4.0, 4.4, 0.4),
    ]


def test_silencedetect_command_is_audio_only_and_configurable(tmp_path: Path) -> None:
    command = build_silencedetect_command(
        tmp_path / "source.mov",
        threshold_db=-32,
        minimum_seconds=0.12,
        ffmpeg_binary="ffmpeg-custom",
    )

    assert command[0] == "ffmpeg-custom"
    assert "silencedetect=noise=-32dB:d=0.12" in command
    assert command[-2:] == ["-", "-nostdin"]
