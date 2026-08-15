# Thai Video Editing Production Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a portable, tested Codex-driven pipeline that analyzes raw Thai talking-head footage, indexes reusable creative assets, produces a validated edit plan and rough preview, and directs ChatCut to build the editable final timeline.

**Architecture:** A Python package owns canonical data models, deterministic media analysis, asset retrieval, plan validation, caption generation, and preview rendering. Codex performs semantic retake and creative decisions through a repository skill; ChatCut is a replaceable NLE adapter operated through MCP/browser controls.

**Tech Stack:** Python 3.11+, Typer, Pydantic v2, PyYAML, Rich, SQLite FTS5, FFmpeg/FFprobe, pytest, Ruff, mypy, GitHub Actions; optional whisper.cpp, faster-whisper, Auto-Editor, PySceneDetect, OpenTimelineIO.

## Global Constraints

- Source footage, asset libraries, model weights, API keys, and rendered projects are never committed.
- Thai transcription must be forced to `th` where the backend permits and must pass Unicode quality gates before automatic structural editing.
- Codex, not ChatCut AI, makes all editorial and creative decisions.
- ChatCut is the primary NLE adapter; the core must still produce a validated plan and local rough preview without ChatCut.
- Unknown or low-confidence speech is preserved and flagged.
- All schemas and run manifests are versioned.

---

### Task 1: Package foundation and typed configuration

**Files:**
- Create: `pyproject.toml`, `src/video_editing_th/__init__.py`, `src/video_editing_th/cli.py`, `src/video_editing_th/config.py`, `src/video_editing_th/errors.py`
- Create: `profiles/thai-fast-reel.yaml`, `.gitignore`, `.env.example`
- Test: `tests/test_config.py`, `tests/test_cli.py`

**Interfaces:**
- Produces: `AppConfig.load(path: Path | None) -> AppConfig`, `EditingProfile.load(path: Path) -> EditingProfile`, Typer app `app`.

- [ ] Write failing tests for valid profile loading, invalid pause bounds, path expansion, and `--help`.
- [ ] Run focused tests and confirm failures are due to missing package behavior.
- [ ] Implement typed config/profile models and the CLI shell.
- [ ] Run focused tests and the package import check.
- [ ] Commit foundation.

### Task 2: Canonical schemas and persistence

**Files:**
- Create: `src/video_editing_th/models.py`, `src/video_editing_th/io.py`
- Test: `tests/test_models.py`, `tests/test_io.py`

**Interfaces:**
- Produces: versioned `MediaItem`, `Transcript`, `TranscriptWord`, `TranscriptSegment`, `QualityReport`, `SilenceInterval`, `RetakeGroup`, `AssetRecord`, `ClipDecision`, `CreativeOperation`, `EditPlan`, `ProjectManifest`; `read_model`, `write_model_atomic`.

- [ ] Write failing round-trip, schema-version, overlap, and atomic-write tests.
- [ ] Confirm tests fail for missing models.
- [ ] Implement minimal strict Pydantic models and atomic JSON persistence.
- [ ] Run tests and refactor shared validators while green.
- [ ] Commit schemas.

### Task 3: Media inventory and project initialization

**Files:**
- Create: `src/video_editing_th/media.py`, `src/video_editing_th/project.py`
- Test: `tests/test_media.py`, `tests/test_project.py`

**Interfaces:**
- Produces: `probe_media(path) -> MediaItem`, `inventory_folder(root) -> list[MediaItem]`, `initialize_project(root, profile) -> ProjectManifest`.

- [ ] Write failing tests using a fake ffprobe executable and fixture files.
- [ ] Confirm expected command/probe failures.
- [ ] Implement hashing, supported-extension discovery, ffprobe parsing, and immutable `edit/` layout creation.
- [ ] Run tests and verify sources are never changed.
- [ ] Commit inventory.

### Task 4: Transcription adapters and Thai validation

**Files:**
- Create: `src/video_editing_th/transcription/base.py`, `whisper_cpp.py`, `faster_whisper.py`, `imported.py`, `service.py`, `thai_quality.py`
- Test: `tests/transcription/test_backends.py`, `tests/transcription/test_thai_quality.py`

**Interfaces:**
- Produces: `TranscriptionBackend.transcribe(media, options) -> Transcript`, `select_backend(name)`, `validate_thai_transcript(transcript) -> QualityReport`.

- [ ] Write failing adapter command/parsing tests and Thai/CJK/repetition/timing quality tests.
- [ ] Verify red failures.
- [ ] Implement local CLI adapter, optional Python adapter, imported JSON normalizer, backend auto-selection, NFC normalization, and quality scoring.
- [ ] Run focused and full tests.
- [ ] Commit transcription.

### Task 5: Silence analysis, transcript packing, and retake candidates

**Files:**
- Create: `src/video_editing_th/audio.py`, `src/video_editing_th/packing.py`, `src/video_editing_th/retakes.py`
- Test: `tests/test_audio.py`, `tests/test_packing.py`, `tests/test_retakes.py`

**Interfaces:**
- Produces: `detect_silence(media, threshold_db, minimum_seconds)`, `pack_transcript(transcript, break_seconds)`, `find_retake_groups(transcript, profile)`.

- [ ] Write failing parsers and grouping tests including Thai text without spaces.
- [ ] Confirm correct failures.
- [ ] Implement FFmpeg silencedetect parsing, compact Markdown/JSON packing, normalized Thai character n-gram similarity, restart/completeness features, and conservative grouping.
- [ ] Run tests and keep uncertain segments ungrouped.
- [ ] Commit analysis.

### Task 6: Asset catalog, contact sheets, annotations, and retrieval

**Files:**
- Create: `src/video_editing_th/assets/catalog.py`, `indexer.py`, `search.py`, `previews.py`
- Test: `tests/assets/test_catalog.py`, `test_indexer.py`, `test_search.py`

**Interfaces:**
- Produces: `AssetCatalog`, `index_assets(root, catalog, preview_dir)`, `annotate_asset`, `search_assets(query, role, filters, limit)`.

- [ ] Write failing SQLite migration, incremental hashing, FTS ranking, annotation, and role/filter tests.
- [ ] Verify failures.
- [ ] Implement SQLite schema/FTS5, technical indexing, FFmpeg contact sheets, persisted descriptions/tags/use cases, and deterministic shortlist ranking.
- [ ] Run tests with fake probes/preview runner.
- [ ] Commit asset system.

### Task 7: Edit-plan validation, captions, and rough rendering

**Files:**
- Create: `src/video_editing_th/planning.py`, `captions.py`, `render.py`, `chatcut.py`
- Test: `tests/test_planning.py`, `tests/test_captions.py`, `tests/test_render.py`, `tests/test_chatcut.py`

**Interfaces:**
- Produces: `validate_edit_plan`, `build_srt`, `render_rough_preview`, `build_chatcut_execution_manifest`.

- [ ] Write failing tests for word-boundary cuts, overlap rejection, output-time caption mapping, Thai caption chunking, safe SFX gain, FFmpeg command generation, and ChatCut manifest ordering.
- [ ] Verify failures.
- [ ] Implement validators, caption generation, concat-based rough renderer, optional subtitle burn-in, and a stable ChatCut execution manifest.
- [ ] Run focused and full tests.
- [ ] Commit planning/rendering.

### Task 8: Complete CLI workflows and environment doctor

**Files:**
- Modify: `src/video_editing_th/cli.py`
- Create: `src/video_editing_th/doctor.py`, `scripts/setup_macos.sh`, `scripts/setup_debian.sh`, `scripts/install_codex_skill.sh`
- Test: `tests/test_workflows.py`, `tests/test_doctor.py`

**Interfaces:**
- Produces commands: `doctor`, `project init`, `project inventory`, `transcribe`, `analyze`, `assets index`, `assets annotate`, `assets search`, `plan validate`, `captions build`, `render preview`, `chatcut export`, `skill install`.

- [ ] Write failing CLI workflow and doctor-report tests.
- [ ] Verify red failures.
- [ ] Implement command orchestration and idempotent setup scripts with no automatic package-manager mutations in `doctor`.
- [ ] Run tests and CLI smoke checks.
- [ ] Commit workflows.

### Task 9: Codex skill and operational references

**Files:**
- Create: `skills/video-editing-th/SKILL.md`, `skills/video-editing-th/references/chatcut-execution.md`, `thai-transcription.md`, `asset-selection.md`, `qa.md`
- Create: `tests/skill/test_skill_contract.py`, `tests/skill/scenarios/*.md`

**Interfaces:**
- Produces a discoverable skill that invokes the CLI, enforces Thai quality gates, writes decisions into canonical plans, uses ChatCut only as an execution surface, and performs bounded render QA.

- [ ] Write failing static contract tests for frontmatter, required gates, command references, and forbidden ChatCut-AI delegation.
- [ ] Confirm baseline failure before creating the skill.
- [ ] Write the minimal skill and heavy references.
- [ ] Run static skill tests and manually exercise scenario fixtures against the documented workflow; record that behavioral subagent testing requires Codex multi-agent support.
- [ ] Commit skill.

### Task 10: Documentation, CI, licensing, and release readiness

**Files:**
- Create: `README.md`, `docs/architecture.md`, `docs/setup.md`, `docs/project-layout.md`, `docs/asset-library.md`, `docs/chatcut.md`, `docs/troubleshooting.md`, `THIRD_PARTY.md`, `NOTICE`, `CONTRIBUTING.md`, `SECURITY.md`, `.github/workflows/ci.yml`, `.github/ISSUE_TEMPLATE/bug_report.yml`, `.github/pull_request_template.md`
- Modify: `LICENSE`, `pyproject.toml`
- Test: `tests/test_docs_examples.py`

**Interfaces:**
- Produces install/run instructions, upstream attribution, supported-platform contract, CI, and packaged metadata.

- [ ] Write failing tests that execute README CLI snippets in dry-run/help mode and verify required documentation links/files.
- [ ] Verify failures.
- [ ] Write documentation, MIT/NOTICE attribution, contribution/security guidance, and CI for Python 3.11–3.13 with lint/type/test/build/skill checks.
- [ ] Run documentation tests, `pytest`, Ruff, mypy, build, and package smoke install.
- [ ] Commit release readiness.

### Task 11: Final verification and GitHub publication

**Files:**
- Review all files and generated diff.

**Interfaces:**
- Produces verified commit history published to `Nas010/video-editing-th`, with documented upstream relationship.

- [ ] Run full tests, lint, type check, build, CLI smoke tests, shell syntax checks, and a synthetic FFmpeg end-to-end fixture.
- [ ] Review the design/spec coverage and scan for secrets, placeholders, generated media, and machine-specific paths.
- [ ] Commit final corrections.
- [ ] Publish the verified tree to the repository and verify GitHub's resulting commit/tree.
