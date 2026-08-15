# Thai Talking-Head Video Editing Pipeline Design

## Product definition

Build a portable, repository-backed Codex workflow that turns raw Thai talking-head footage into an editable first cut. Codex owns editorial reasoning. Local tools provide deterministic analysis, validation, indexing, and preview rendering. ChatCut is the primary nonlinear editor that Codex controls through MCP and browser access; ChatCut's own AI is not part of the decision process.

## Primary workflow

1. Inventory a project folder and record immutable media metadata and hashes.
2. Transcribe Thai speech through a pluggable backend, forcing `th` and transcription mode.
3. validate Thai Unicode, flag multilingual hallucinations, and retain word/segment timing.
4. Analyze silence and speech boundaries from FFmpeg and transcript timing.
5. Group nearby similar utterances as retake candidates; Codex chooses the latest complete/best delivery.
6. Produce a typed rough-cut plan containing exact source ranges and reasons.
7. Generate optional Thai captions from the corrected transcript.
8. Search a persistent local asset catalog for B-roll, overlays, and sound effects; visually verify only shortlisted assets.
9. Produce a creative plan with B-roll, overlays, SFX, zoom, pan, and reframe operations.
10. Validate the complete plan, render a deterministic local preview, then execute the same plan in ChatCut.
11. Render from ChatCut and run cut/effect/caption QA before presenting the result.

## Boundaries

- The repository never stores API keys, model weights, source footage, rendered projects, or the user's asset library.
- The core pipeline must run without ChatCut up to a validated `edit_plan.json` and local rough preview.
- ChatCut remains an adapter. The canonical transcript, asset index, edit decisions, and creative plan belong to this repository's formats.
- Codex selects retakes and creative assets. Heuristics generate candidates but do not silently delete uncertain speech.
- Low-confidence decisions are review items. The default is to preserve speech rather than guess.

## Architecture

### Package

`video_editing_th` is a Python 3.11+ package with a Typer CLI. Runtime data is stored inside each footage project's `edit/` directory. Shared asset metadata lives in SQLite under the asset root or an explicitly configured path.

### Core models

Pydantic models define media inventory, transcript words/segments, quality reports, silence intervals, retake groups, selected clips, captions, asset records, creative operations, and project manifests. JSON files are versioned and reject unknown schema versions.

### Transcription

A backend protocol supports:

- `whisper.cpp` through `whisper-cli` or Auto-Editor's Whisper command;
- `faster-whisper` when the optional dependency is installed;
- imported JSON from any stronger external transcription provider.

Every backend normalizes into the canonical transcript model. The default backend is `auto`, preferring a working local engine. Model downloads happen outside the repository.

### Thai validation

Validation performs Unicode NFC normalization, Thai character ratio checks, unexpected CJK detection, suspicious Latin-heavy segment detection, repeated-phrase detection, impossible timing checks, and non-speech hallucination checks where VAD is available. The report records warnings and a safe/unsafe decision.

### Retake analysis

Transcript segments are grouped within configurable temporal windows using normalized text similarity and restart indicators. The system outputs candidates with timing, completeness signals, and explanatory features. Codex performs final selection and writes reasons/confidence into the edit plan.

### Asset catalog

SQLite stores one record per asset and optional segment-level records. It includes technical metadata, descriptions, tags, use cases, orientation, role, duration, contact-sheet path, content hash, and indexed text. SQLite FTS5 provides fast retrieval. A provider interface permits optional vector embeddings without making them mandatory. New and modified files are indexed incrementally.

Codex descriptions are persisted through an `assets annotate` command. During editing, search returns a shortlist; Codex inspects contact sheets or source excerpts only for that shortlist.

### Timeline and rendering

A canonical edit plan contains:

- structural clips with source in/out and timeline positions;
- captions;
- B-roll and overlay placements;
- SFX placements and gain;
- motion effects with explicit parameters;
- review flags and decision provenance.

The local renderer supports a reliable rough cut and caption burn-in using FFmpeg. ChatCut execution is documented in the skill and consumes the same plan. Unsupported native effects can be generated externally and inserted as transparent media.

### Codex skill

The skill is installed by symlinking the repository's `skills/video-editing-th` directory into `${CODEX_HOME:-~/.codex}/skills/` or `~/.agents/skills/`. It guides Codex through doctor checks, analysis, Thai quality gates, retake selection, asset retrieval, plan validation, ChatCut execution, render inspection, and bounded revision.

### Portability

Setup scripts support macOS and Debian/Ubuntu. `doctor` reports missing external tools without modifying the machine. Users manually configure footage, asset, model, and export paths. `.env` is optional and ignored.

## Quality and safety

- All destructive edits exist only in generated timelines; source media remains untouched.
- Every kept/removed section is auditable.
- Cut points must not intersect canonical transcript words.
- Captions are generated after structural editing using output-time mappings.
- SFX gain is bounded by profile limits.
- Asset reuse and maximum effect frequency are profile-controlled.
- Every run records input hashes, backend/model names, profile version, and tool versions.
- CI runs tests, lint, type checking, package build, and skill validation.

## Initial production profile

`profiles/thai-fast-reel.yaml` targets one-speaker Thai vertical reels:

- prefer latest complete retake;
- preserve low-confidence material;
- fast intra-thought gaps, natural sentence gaps;
- restrained punch-ins and SFX;
- optional Thai captions;
- no automatic B-roll without a catalog match and visual verification.

## Upstream and dependencies

The project is derived from the architecture and selected helper concepts of `browser-use/video-use` at upstream tree `92c2b34e44c205cbc2acae7f6ca7c1c219d5dd66`, used under MIT. Auto-Editor, whisper.cpp, faster-whisper, PySceneDetect, and OpenTimelineIO are external optional tools/libraries, not vendored forks. Their versions and licenses are documented.
