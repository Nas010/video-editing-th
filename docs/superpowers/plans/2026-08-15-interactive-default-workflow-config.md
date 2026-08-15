# Interactive Default Workflow Configuration Implementation Plan

> **For agentic workers:** Use superpowers:test-driven-development for behavior changes and superpowers:verification-before-completion before publishing.

**Goal:** Make the Codex skill execute the complete Thai Reel workflow by default while persisting only machine-specific local visual paths.

**Final architecture:** `AppConfig` stores local B-roll, overlay, and background folders plus reusable workflow/profile settings. ChatCut supplies native sound effects, music, and transitions. Output defaults are fixed at 1080x1920 at 30 fps. Captions are included only when the current project prompt explicitly requests them.

**Tech Stack:** Python 3.11+, Typer, Pydantic v2, PyYAML, SQLite/FTS5, FFmpeg, pytest, Ruff, mypy, GitHub Actions.

## Global constraints

- Personal absolute paths and model weights never enter Git.
- Source footage remains immutable.
- ChatCut AI never makes editorial or creative decisions.
- Missing optional local visual folders do not block a talking-head-only edit.
- Configured non-empty folder paths must exist and be directories.
- Legacy `asset_root` remains loadable.
- Deprecated output, caption, and native-media folder fields migrate without blocking existing users.

---

### Task 1: Simplified configuration contract

**Files:**
- `src/video_editing_th/config.py`
- `tests/test_config.py`

- [x] Add fixed social constants: 1080x1920 at 30 fps.
- [x] Restrict configured assets to B-roll, overlays, and backgrounds.
- [x] Remove persisted native audio/transition choices, output settings, and caption choices.
- [x] Add backward-compatible migration for files written by the earlier wizard.
- [x] Verify save/load round trips and path expansion.

### Task 2: Simplified setup wizard

**Files:**
- `src/video_editing_th/cli.py`
- `tests/test_cli.py`

- [x] Ask only for local visual folders and the default profile.
- [x] Remove native-media, composition, and caption options from `configure`.
- [x] Keep interactive and non-interactive setup.
- [x] Keep config path/show commands.

### Task 3: Fixed output with explicit project override

**Files:**
- `src/video_editing_th/cli.py`
- `tests/test_workflows.py`

- [x] Default ChatCut export to 1080x1920 at 30 fps.
- [x] Preserve explicit width/height/fps flags for a real per-project format override.

### Task 4: ChatCut-native media operations

**Files:**
- `src/video_editing_th/models.py`
- `src/video_editing_th/chatcut.py`
- `tests/test_chatcut.py`

- [x] Add a music creative-operation kind.
- [x] Support stable native asset IDs without local import operations.
- [x] Emit native SFX and music in the audio phase.
- [x] Keep native transitions in the transitions phase.

### Task 5: Codex skill behavior

**Files:**
- `skills/video-editing-th/SKILL.md`
- `skills/video-editing-th/references/configuration.md`
- `skills/video-editing-th/references/asset-selection.md`
- `skills/video-editing-th/references/chatcut-execution.md`
- `tests/skill/test_skill_contract.py`
- `tests/skill/scenarios/05-first-use-configuration.md`

- [x] Declare ChatCut-native sound effects, music, and transitions.
- [x] Keep all selection decisions with Codex.
- [x] Require explicit current-prompt caption instructions; silent means no captions.
- [x] Limit first-use questions to local visual paths and profile.
- [x] Preserve the full default Thai Reel mission.

### Task 6: Documentation and setup integration

**Files:**
- `README.md`
- `docs/architecture.md`
- `docs/setup.md`
- `docs/configuration.md`
- `docs/asset-library.md`
- `docs/chatcut.md`
- setup scripts
- `tests/test_docs_examples.py`

- [x] Document fixed social defaults.
- [x] Document native ChatCut media.
- [x] Document prompt-controlled captions.
- [x] Remove obsolete wizard questions and flags.
- [x] Update post-install guidance.

### Task 7: Publication

- [ ] Run Ruff lint and formatting checks.
- [ ] Run strict mypy.
- [ ] Run all tests with the repository coverage threshold.
- [ ] Run shell syntax checks and build distributions.
- [ ] Review the PR patch for accidental schema or compatibility regressions.
- [ ] Merge only after the PR and post-merge `main` workflows are green.
