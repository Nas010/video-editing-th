import json
from pathlib import Path

from typer.testing import CliRunner

from video_editing_th.cli import app

runner = CliRunner()


def test_assets_index_command_serializes_slots_summary(tmp_path: Path) -> None:
    asset_root = tmp_path / "assets"
    (asset_root / "broll").mkdir(parents=True)
    (asset_root / "broll" / "clip.mov").write_bytes(b"asset")
    fake_probe = tmp_path / "ffprobe"
    probe_payload = {
        "streams": [
            {
                "codec_type": "video",
                "codec_name": "h264",
                "width": 1080,
                "height": 1920,
                "avg_frame_rate": "30/1",
            },
            {"codec_type": "audio", "codec_name": "aac"},
        ],
        "format": {"duration": "2.0"},
    }
    fake_probe.write_text(
        f"#!/usr/bin/env python3\nimport json\nprint(json.dumps({json.dumps(probe_payload)}))\n",
        encoding="utf-8",
    )
    fake_probe.chmod(0o755)
    fake_ffmpeg = tmp_path / "ffmpeg"
    fake_ffmpeg.write_text(
        "#!/usr/bin/env python3\nimport pathlib, sys\npathlib.Path(sys.argv[-1]).touch()\n",
        encoding="utf-8",
    )
    fake_ffmpeg.chmod(0o755)
    config = tmp_path / "config.yaml"
    config.write_text(
        f"ffprobe_binary: {fake_probe}\nffmpeg_binary: {fake_ffmpeg}\n",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "assets",
            "index",
            str(asset_root),
            "--catalog",
            str(tmp_path / "catalog.db"),
            "--preview-dir",
            str(tmp_path / "previews"),
            "--config",
            str(config),
        ],
    )

    assert result.exit_code == 0, result.stdout
    assert json.loads(result.stdout)["indexed"] == 1
