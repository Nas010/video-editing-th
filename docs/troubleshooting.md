# Troubleshooting

## Doctor reports no transcription backend

Install `whisper-cli` and a multilingual model, or install the optional Python backend:

```bash
python -m pip install -e '.[transcription]'
video-editing-th doctor
```

## Thai transcript contains Chinese or repeated English text

Do not edit from it. The quality report should mark `unexpected_cjk`, `low_thai_ratio`, or `repeated_phrase`. Re-run with explicit `--language th`, try a stronger multilingual model/backend, or import a corrected canonical transcript.

## Plan validation says a cut is inside a spoken word

Move the source boundary outside the word interval and keep the profile's safety handle. Listen across the cut; timestamp precision alone is not sufficient.

## No assets are returned

Confirm the catalog path, role filter, and annotations. Run the index again after adding files. Search descriptions/tags with a simpler conceptual phrase. A missing candidate is preferable to irrelevant B-roll.

## Contact-sheet generation fails

Run `ffmpeg -version`, verify that the asset is decodable, and inspect the full command by reproducing it with the same file. Reindex with `--continue-on-error` to catalog other assets while recording failures.

## Skill install refuses a destination

The installer only replaces symlinks. Move or remove the real directory at the reported destination after reviewing its contents, then run the install command again.

## ChatCut MCP lacks an effect operation

Keep the operation in the canonical plan. Use Codex browser control for that exact property and verify the resulting editor state. Do not ask ChatCut AI to choose an alternative.

## Rough render has no audio

The local renderer assumes talking-head source clips contain both video and audio streams. Confirm FFprobe output and use source media with a valid audio stream. Complex/multitrack audio belongs in the ChatCut pass.

## Local command differs between machines

Compare Python/package version, profile version, source SHA-256 values, transcription backend/model, and external tool versions. Do not compare only filenames.
