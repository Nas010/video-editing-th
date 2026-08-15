# Interactive Default Workflow Configuration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a one-time interactive local configuration and make the Codex skill execute the complete Thai Reel workflow by default.

**Architecture:** Extend the typed `AppConfig` with nested asset, workflow, and output defaults persisted in an XDG-style YAML file. Add an interactive CLI wizard plus configured asset indexing, then teach the Codex skill to enforce a first-use configuration gate and apply the complete default mission.

**Tech Stack:** Python 3.11+, Typer, Pydantic v2, PyYAML, SQLite/FTS5, FFmpeg, pytest, Ruff, mypy, GitHub Actions.

## Global Constraints

- Personal absolute paths and model weights must never be committed.
- Source footage remains immutable.
- ChatCut AI must never make editorial or creative decisions.
- Missing optional asset folders must not block a talking-head-only edit.
- Configured non-empty folder paths must exist and be directories.
- Keep legacy `asset_root` configuration loadable.

---

### Task 1: Configuration persistence contract

**Files:**
- Modify: `src/video_editing_th/config.py`
- Test: `tests/test_config.py`

**Interfaces:**
- Produces: `default_config_path() -> Path`, nested `AssetLibraryConfig`, `WorkflowDefaults`, `OutputDefaults`, `AppConfig.save(path: Path | None = None) -> Path`, and automatic `AppConfig.load(None)` discovery.

- [ ] Write failing tests for XDG/environment path resolution, nested path expansion, and save/load round trips.
- [ ] Run `pytest tests/test_config.py -v` and verify the new tests fail for missing APIs.
- [ ] Implement the minimal typed configuration and atomic YAML persistence.
- [ ] Run `pytest tests/test_config.py -v` and verify green.

### Task 2: Interactive configuration CLI

**Files:**
- Modify: `src/video_editing_th/cli.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Produces: root `configure` command and `config path` / `config show` subcommands.

- [ ] Write failing CLI tests for command discovery, interactive answers, and non-interactive options.
- [ ] Run the focused CLI tests and verify RED.
- [ ] Implement prompts that preserve existing values, validate non-empty directories, and save to the resolved config path.
- [ ] Run the focused CLI tests and verify GREEN.

### Task 3: Configured multi-root asset indexing

**Files:**
- Modify: `src/video_editing_th/assets/indexer.py`
- Modify: `src/video_editing_th/assets/__init__.py`
- Modify: `src/video_editing_th/cli.py`
- Test: `tests/assets/test_indexer.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Produces: `index_asset_folders(folders: dict[AssetRole, Path], ...) -> IndexSummary` and `assets index-configured`.

- [ ] Write failing tests proving explicit roles are preserved and combined pruning does not delete assets from another configured root.
- [ ] Run focused asset tests and verify RED.
- [ ] Refactor single-root indexing through one shared internal scanner and add multi-root indexing.
- [ ] Default search/annotation catalog paths to `config.assets.catalog_path` when omitted.
- [ ] Run focused asset and CLI tests and verify GREEN.

### Task 4: Apply configured output defaults

**Files:**
- Modify: `src/video_editing_th/cli.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Changes: `chatcut export` accepts optional width/height/fps and falls back to `AppConfig.output`.

- [ ] Write failing tests for configured ChatCut dimensions.
- [ ] Verify RED.
- [ ] Implement the fallback and verify GREEN.

### Task 5: Codex skill default mission and configuration gate

**Files:**
- Modify: `skills/video-editing-th/SKILL.md`
- Create: `skills/video-editing-th/references/configuration.md`
- Modify: `tests/skill/test_skill_contract.py`
- Add or update: `tests/skill/scenarios/*.md`

**Interfaces:**
- Produces: explicit default mission, first-use configuration gate, and per-project override behavior.

- [ ] Add failing skill-contract assertions and pressure scenarios.
- [ ] Run skill tests and verify RED.
- [ ] Update the skill and configuration reference with concise, unambiguous instructions.
- [ ] Run skill tests and verify GREEN.

### Task 6: Documentation and setup integration

**Files:**
- Modify: `README.md`
- Modify: `docs/setup.md`
- Modify: `docs/asset-library.md`
- Modify: `scripts/setup_macos.sh`
- Modify: `scripts/setup_debian.sh`
- Test: `tests/test_docs_examples.py`

**Interfaces:**
- Documents: one-time configure flow and minimal recurring prompt `$video-editing-th <footage-folder>`.

- [ ] Add failing documentation/example tests for `configure`, `config show`, and `assets index-configured`.
- [ ] Verify RED.
- [ ] Update docs and setup completion messages.
- [ ] Verify GREEN.

### Task 7: Full verification and publication

**Files:**
- Modify only files required by discovered failures.

- [ ] Run Ruff lint and formatting checks.
- [ ] Run strict mypy.
- [ ] Run all tests with the repository coverage threshold.
- [ ] Run shell syntax checks and build distributions.
- [ ] Open a pull request, wait for GitHub Actions on Python 3.11/3.12/3.13, repair failures, and merge only after green.
