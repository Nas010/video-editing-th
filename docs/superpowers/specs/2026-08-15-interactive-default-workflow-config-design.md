# Interactive Default Workflow Configuration Design

## Goal

Make `$video-editing-th <footage-folder>` mean a complete Thai talking-head Reel workflow by default, while storing only real machine-specific local visual paths in a one-time configuration outside Git.

## Default mission

Unless the current prompt overrides it, Codex will:

1. treat the supplied media as raw Thai talking-head footage;
2. create a fast-paced vertical 1080x1920, 30 fps Reel;
3. transcribe explicitly as Thai and stop if the Thai quality gate fails;
4. remove mistakes, false starts, superseded retakes, and excess dead air while preferring the latest complete good take;
5. search configured local B-roll, overlay, and background folders;
6. inspect contact sheets and visually verify local finalists before selection;
7. select sound effects, music, and transitions from ChatCut's native libraries;
8. add restrained semantic B-roll, overlays, punch-ins, zooms, pans, reframing, native sound, native music, and native transitions;
9. add captions only when the current project prompt explicitly requests them;
10. build the editable timeline in ChatCut through MCP first and browser control only where MCP lacks an operation;
11. never delegate editorial or creative decisions to ChatCut AI;
12. render, inspect, and repair the result through a bounded QA loop.

## One-time configuration

`video-editing-th configure` asks only for optional local folders for:

- B-roll;
- overlays/graphics;
- backgrounds.

It also asks for the default editing profile. Existing values are shown as defaults, so rerunning the wizard edits rather than destroys the configuration.

It does not ask for sound, music, or transition folders because those media are native to ChatCut. It does not ask for output dimensions/frame rate because social vertical is the built-in default. It does not store a caption preference because caption presence is a per-project prompt decision.

The default location is `${VIDEO_EDITING_TH_CONFIG}` when set, otherwise `${XDG_CONFIG_HOME}/video-editing-th/config.yaml`, otherwise `~/.config/video-editing-th/config.yaml`. Personal paths and model weights remain outside Git.

## Configuration schema

`AppConfig` keeps executable/model settings and nested immutable settings:

- `assets`: local B-roll, overlay, and background folders plus catalog/preview paths;
- `workflow`: default profile, ChatCut backend, and local-visual/motion toggles.

The standard output constants are 1080x1920 at 30 fps and are not persisted. The legacy `asset_root` remains loadable. Deprecated native-media, output, and caption fields are ignored during migration and disappear when the file is saved again.

## CLI behavior

- `video-editing-th configure` — interactive one-time local-visual setup with non-interactive flags for Codex automation;
- `video-editing-th config path` — print the active config path;
- `video-editing-th config show` — print the resolved configuration, with `--json` for agents;
- `video-editing-th assets index-configured` — index all configured local visual folders into one catalog and prune only after the combined scan;
- `video-editing-th chatcut export` — use fixed social defaults unless a project explicitly supplies another format.

Asset search/annotation commands default to the configured visual catalog when `--catalog` is omitted.

## Codex skill behavior

The skill performs a configuration gate before the first edit. If the config file is absent, Codex runs the wizard and asks only for local facts it cannot infer. It never invents paths. Blank optional visual folders are allowed. Once configured, the skill reads the resolved config and does not repeat the questions on every project.

The user normally provides only the footage folder and per-project overrides. Caption instructions must be explicit in that project prompt.

## ChatCut-native references

Native media are recorded in the canonical plan with stable references such as:

```text
chatcut:sfx:soft-pop
chatcut:music:upbeat-clean
```

They are not emitted as local import operations. Codex searches/previews the native choices, records timing/parameters/reason/confidence, and verifies the placement after ChatCut execution.

## Error handling

- Non-empty local folder answers must resolve to existing directories.
- The wizard creates parent directories and writes YAML atomically.
- No configured local visual folders does not block a talking-head-only edit.
- Missing configured folders are reported explicitly rather than silently ignored.
- Catalog pruning happens only after all configured local visual roots are scanned together.
- Missing suitable native media results in omission, not a guessed effect.
