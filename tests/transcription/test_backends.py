import json
from pathlib import Path

import pytest

from video_editing_th.models import MediaItem, Transcript
from video_editing_th.transcription.base import TranscriptionOptions
from video_editing_th.transcription.imported import ImportedTranscriptBackend
from video_editing_th.transcription.service import select_backend
from video_editing_th.transcription.whisper_cpp import WhisperCppBackend


def media(tmp_path: Path) -> MediaItem:
    source = tmp_path / "source.mov"
    source.write_bytes(b"media")
    return MediaItem(
        source_path=source,
        sha256="a" * 64,
        size_bytes=5,
        duration_seconds=8.0,
        width=1080,
        height=1920,
        fps=30,
    )


def test_whisper_cpp_command_forces_thai_and_transcription(tmp_path: Path) -> None:
    backend = WhisperCppBackend(
        model_path=tmp_path / "ggml-large-v3.bin",
        binary="whisper-cli",
        ffmpeg_binary="ffmpeg",
    )
    output_base = tmp_path / "result"

    command = backend.build_command(
        audio_path=tmp_path / "audio.wav",
        output_base=output_base,
        options=TranscriptionOptions(language="th", prompt="ภาษาไทยเท่านั้น"),
    )

    assert command[:2] == ["whisper-cli", "-m"]
    assert "-l" in command and command[command.index("-l") + 1] == "th"
    assert "-tr" not in command
    assert "-ojf" in command
    assert "--prompt" in command
    assert command[-2:] == ["-f", str(tmp_path / "audio.wav")]


def test_whisper_cpp_parses_full_json_to_canonical_transcript(tmp_path: Path) -> None:
    payload = {
        "result": {"language": "th"},
        "transcription": [
            {
                "offsets": {"from": 1000, "to": 3000},
                "text": " สวัสดีครับ",
                "tokens": [
                    {
                        "text": " สวัสดี",
                        "offsets": {"from": 1000, "to": 2000},
                        "p": 0.95,
                    },
                    {
                        "text": "ครับ",
                        "offsets": {"from": 2000, "to": 3000},
                        "p": 0.9,
                    },
                ],
            }
        ],
    }

    transcript = WhisperCppBackend.parse_payload(
        payload,
        media_sha256="a" * 64,
        source_path=tmp_path / "source.mov",
        model="large-v3",
    )

    assert transcript.language == "th"
    assert transcript.segments[0].text == "สวัสดีครับ"
    assert [word.text for word in transcript.words] == ["สวัสดี", "ครับ"]
    assert transcript.words[0].start == 1.0
    assert transcript.words[1].end == 3.0


def test_imported_backend_normalizes_generic_segment_json(tmp_path: Path) -> None:
    imported = tmp_path / "external.json"
    imported.write_text(
        json.dumps(
            {
                "language": "th",
                "segments": [
                    {
                        "start": 0.5,
                        "end": 2.0,
                        "text": "ทดสอบ",
                        "words": [
                            {"start": 0.5, "end": 1.2, "word": "ทด"},
                            {"start": 1.2, "end": 2.0, "word": "สอบ"},
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    backend = ImportedTranscriptBackend(imported)

    transcript = backend.transcribe(media(tmp_path), TranscriptionOptions(language="th"))

    assert isinstance(transcript, Transcript)
    assert transcript.backend == "imported"
    assert transcript.segments[0].word_indices == [0, 1]


def test_select_backend_rejects_unknown_backend() -> None:
    with pytest.raises(ValueError, match="Unknown transcription backend"):
        select_backend("mystery")
