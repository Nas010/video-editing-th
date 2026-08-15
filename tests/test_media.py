import json
from pathlib import Path

from video_editing_th.media import inventory_folder, probe_media


def write_fake_ffprobe(path: Path) -> None:
    payload = {
        "streams": [
            {
                "codec_type": "video",
                "codec_name": "h264",
                "width": 1080,
                "height": 1920,
                "avg_frame_rate": "30000/1001",
                "tags": {"creation_time": "2026-08-15T01:02:03Z"},
            },
            {"codec_type": "audio", "codec_name": "aac"},
        ],
        "format": {"duration": "12.5", "size": "1234"},
    }
    path.write_text(
        "#!/usr/bin/env python3\n"
        "import json\n"
        f"print(json.dumps({json.dumps(payload)}))\n",
        encoding="utf-8",
    )
    path.chmod(0o755)


def test_probe_media_parses_ffprobe_and_hashes_source(tmp_path: Path) -> None:
    source = tmp_path / "clip.mov"
    source.write_bytes(b"video-fixture")
    fake_probe = tmp_path / "ffprobe"
    write_fake_ffprobe(fake_probe)

    item = probe_media(source, ffprobe_binary=str(fake_probe))

    assert item.source_path == source.resolve()
    assert item.duration_seconds == 12.5
    assert item.width == 1080
    assert item.height == 1920
    assert round(item.fps or 0, 3) == 29.97
    assert item.video_codec == "h264"
    assert item.audio_codec == "aac"
    assert len(item.sha256) == 64


def test_inventory_ignores_generated_edit_folder_and_sorts(tmp_path: Path) -> None:
    fake_probe = tmp_path / "ffprobe"
    write_fake_ffprobe(fake_probe)
    (tmp_path / "b.MP4").write_bytes(b"b")
    (tmp_path / "a.mov").write_bytes(b"a")
    (tmp_path / "notes.txt").write_text("ignore", encoding="utf-8")
    edit_dir = tmp_path / "edit"
    edit_dir.mkdir()
    (edit_dir / "generated.mp4").write_bytes(b"generated")

    items = inventory_folder(tmp_path, ffprobe_binary=str(fake_probe))

    assert [item.source_path.name for item in items] == ["a.mov", "b.MP4"]
