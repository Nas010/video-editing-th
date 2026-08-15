# Architecture

## Design objective

The system converts raw Thai talking-head media into a reproducible edit while keeping semantic decisions separate from the software that executes the timeline. Codex reasons from compact evidence; deterministic tools produce and validate artifacts; ChatCut supplies the editable NLE and native creative media.

## Responsibility boundaries

### Local deterministic layer

- `media.py`: source discovery, hashing, and FFprobe normalization.
- `transcription/`: provider adapters and the canonical word/segment schema.
- `thai_quality.py`: NFC normalization and the Thai safety gate.
- `audio.py`: FFmpeg silence evidence.
- `packing.py`: low-token transcript representation.
- `retakes.py`: conservative repeated-attempt candidates.
- `assets/`: persistent SQLite FTS catalog, annotations, contact sheets, and shortlist retrieval for local visual assets.
- `planning.py`: word-boundary and creative-limit validation.
- `captions.py`: source-to-output timing and Thai-aware card chunking when captions are requested.
- `render.py`: local structural preview.
- `chatcut.py`: ordered execution manifest with no editorial intelligence.

### Codex reasoning layer

Codex decides which complete take to keep, how much pause to preserve, where visual coverage helps, which shortlisted local visual asset is suitable, which ChatCut-native sound/music/transition fits, and which planned motion treatment supports the speech. Every choice is written into an `EditPlan` with exact times, reason, confidence, and review state.

Caption presence is decided by the current user prompt, not machine configuration. The transcript is always produced for editing evidence; caption cues are produced only when requested.

### ChatCut execution layer

Codex applies the exported manifest to ChatCut through MCP first and browser controls only for unsupported UI operations. ChatCut does not choose content. The structural timeline is applied before optional captions, local B-roll/overlays/backgrounds, motion, native sound/music, and native transitions.

The default composition is fixed at 1080x1920 at 30 fps. Per-project format overrides are possible, but the dimensions are not persisted as machine preferences.

## Versioned artifacts

All canonical JSON uses `schema_version: 1`:

- `project.json`
- source transcript JSON
- transcript quality report
- retake analysis
- `EditPlan`
- ChatCut execution manifest

The local visual-asset catalog has its own schema version in SQLite. Source SHA-256 values connect media, transcripts, and clip decisions without depending on filenames. ChatCut-native media uses stable native IDs rather than fake local paths.

## Failure handling

- Unsafe Thai transcript: stop automatic structural work and preserve footage.
- Missing transcript for a planned clip: plan validation fails.
- Cut inside a spoken word: plan validation fails.
- Excessive sound-effect or motion frequency: plan validation fails.
- Missing/ambiguous local visual asset: keep the talking head visible.
- Missing/ambiguous ChatCut-native choice: omit the effect rather than guessing.
- ChatCut operation not verifiable: leave it unapplied and report it.
- QA defects after three repair passes: report remaining defects rather than loop indefinitely.

## Portability

The Python package and canonical plan are editor-independent except for optional native-media references explicitly prefixed for ChatCut. `whisper.cpp` is the preferred Apple Silicon path; `faster-whisper` is an optional backend. FFmpeg is required. Auto-Editor, PySceneDetect, and OpenTimelineIO are optional extension points rather than hard dependencies.
