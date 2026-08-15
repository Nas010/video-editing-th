from pathlib import Path

from video_editing_th.assets.previews import build_contact_sheet_command


def test_contact_sheet_command_samples_and_tiles_frames(tmp_path: Path) -> None:
    command = build_contact_sheet_command(
        tmp_path / "source.mp4",
        tmp_path / "sheet.jpg",
        duration_seconds=12,
        frame_count=6,
        ffmpeg_binary="ffmpeg-custom",
    )

    assert command[0] == "ffmpeg-custom"
    assert "fps=0.5" in command[command.index("-vf") + 1]
    assert "tile=3x2" in command[command.index("-vf") + 1]
    assert command[-1] == str(tmp_path / "sheet.jpg")
