from pathlib import Path

from video_editing_th.models import ClipDecision, EditPlan
from video_editing_th.render import build_render_command


def test_render_command_trims_concats_and_fades_audio(tmp_path: Path) -> None:
    first = tmp_path / "a.mov"
    second = tmp_path / "b.mov"
    plan = EditPlan(
        project_id="p1",
        profile_name="test",
        structural_clips=[
            ClipDecision(
                id="c1",
                source_path=first,
                source_sha256="a" * 64,
                source_start=1,
                source_end=3,
                timeline_start=0,
                timeline_end=2,
                reason="keep",
                confidence=1,
            ),
            ClipDecision(
                id="c2",
                source_path=second,
                source_sha256="b" * 64,
                source_start=4,
                source_end=6,
                timeline_start=2,
                timeline_end=4,
                reason="keep",
                confidence=1,
            ),
        ],
    )

    command = build_render_command(plan, tmp_path / "preview.mp4", ffmpeg_binary="ffmpeg-x")
    filter_complex = command[command.index("-filter_complex") + 1]

    assert command[0] == "ffmpeg-x"
    assert command.count("-i") == 2
    assert "trim=start=1:end=3" in filter_complex
    assert "atrim=start=4:end=6" in filter_complex
    assert "afade=t=in" in filter_complex
    assert "concat=n=2:v=1:a=1" in filter_complex
    assert command[-1] == str(tmp_path / "preview.mp4")
