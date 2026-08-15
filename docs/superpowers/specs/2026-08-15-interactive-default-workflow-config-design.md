# Interactive Default Workflow Configuration Design

## Goal

Make `$video-editing-th <footage-folder>` mean a complete Thai talking-head Reel workflow by default, while storing personal machine paths and preferences in a one-time local configuration outside Git.

## Approved default mission

Unless the user overrides it, Codex will:

1. treat the supplied media as raw Thai talking-head footage;
2. create a fast-paced vertical 1080x1920, 30 fps Reel;
3. transcribe explicitly as Thai and stop if the Thai quality gate fails;
4. remove mistakes, false starts, superseded retakes, and excess dead air while preferring the latest complete good take;
5. generate Thai captions from the validated canonical transcript;
6. search configured local B-roll, overlay, SFX, music, transition, and background folders;
7. retrieve candidates from the persistent catalog, inspect contact sheets, and visually verify finalists before selection;
8. add restrained semantic B-roll, overlays, SFX, punch-ins, zooms, pans, reframing, and transitions;
9. build the editable timeline in ChatCut through MCP first and browser control only where MCP lacks an operation;
10. never delegate editorial or creative decisions to ChatCut AI;
11. render, inspect, and repair the result through a bounded QA loop;
12. retain the transcript, quality report, edit plan, captions, ChatCut manifest, previews, and final render.

## One-time configuration

`video-editing-th configure` is an interactive wizard. It asks for optional local folders for:

- B-roll;
- overlays/graphics;
- sound effects;
- music;
- transitions;
- backgrounds.

It also asks for the default profile, output dimensions/frame rate, whether each creative category is enabled, and whether Thai captions are enabled. Existing values are shown as defaults, so rerunning the wizard edits rather than destroys the configuration.

The default location is `${VIDEO_EDITING_TH_CONFIG}` when set, otherwise `${XDG_CONFIG_HOME}/video-editing-th/config.yaml`, otherwise `~/.config/video-editing-th/config.yaml`. Personal paths and model weights remain outside Git.

## Configuration schema

`AppConfig` keeps executable/model settings and gains nested immutable settings:

- `assets`: role-specific folders, catalog path, and preview directory;
- `workflow`: default profile, editor backend, creative toggles, captions, and caption language;
- `output`: width, height, and fps.

The legacy `asset_root` remains loadable. If role-specific folders are configured, they take precedence for configured asset indexing.

## CLI behavior

New commands:

- `video-editing-th configure` — interactive one-time setup with optional non-interactive flags for Codex automation;
- `video-editing-th config path` — print the active config path;
- `video-editing-th config show` — print the resolved configuration, with `--json` for agents;
- `video-editing-th assets index-configured` — index all configured role folders into one catalog and prune only after the combined scan.

Existing asset search/annotation commands default to the configured catalog when `--catalog` is omitted. ChatCut export defaults to configured output dimensions and fps.

## Codex skill behavior

The skill performs a configuration gate before the first edit. If the config file is absent, Codex runs the wizard and asks the user only for local facts it cannot infer. It never invents paths. Blank optional asset folders are allowed. Once configured, the skill reads the resolved config and does not repeat the long editing brief or ask for the same paths on every project.

The user normally needs to provide only the footage folder and any per-project overrides.

## Error handling

- Non-empty folder answers must resolve to existing directories.
- The wizard creates parent directories and writes YAML atomically.
- No configured asset folders causes `assets index-configured` to fail with a clear configuration error, but does not block a talking-head-only edit.
- Missing configured folders are reported explicitly rather than silently ignored.
- Existing unrelated catalog assets are pruned only after all configured roots are scanned together.

## Tests

Tests cover configuration path resolution, save/load round trips, interactive prompting, non-interactive flags, multiple configured asset roots, combined pruning, CLI discovery, skill default-mission language, documentation examples, and existing CI gates.
