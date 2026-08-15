# One-Time Machine Configuration

## Purpose

The editing behavior belongs to the skill. Personal absolute paths belong in a machine-local configuration outside Git. Run this setup once per machine, then reuse it for every project.

The active file is resolved in this order:

1. `VIDEO_EDITING_TH_CONFIG`;
2. `$XDG_CONFIG_HOME/video-editing-th/config.yaml`;
3. `~/.config/video-editing-th/config.yaml`.

## First-use procedure

1. Run `video-editing-th config path`.
2. Check whether the returned file exists.
3. When it is absent, run `video-editing-th configure`.
4. Ask the user for each local fact. Never invent or guess a path.
5. Blank answers are allowed for optional asset categories.
6. Confirm the saved result with `video-editing-th config show --json`.
7. When at least one asset folder is configured, run `video-editing-th assets index-configured`.

The wizard asks for:

- **B-roll folder**;
- **Overlay/graphics folder**;
- **Sound-effects folder**;
- music folder;
- transition folder;
- background folder;
- default editing profile;
- output width, height, and frame rate;
- whether Thai captions are enabled.

Configured non-empty folders must already exist. The wizard stores resolved absolute paths, but the repository never stores them.

## Codex-assisted non-interactive setup

When the user has supplied all known values, Codex may run:

```bash
video-editing-th configure \
  --non-interactive \
  --broll "/Users/example/Video Assets/B-roll" \
  --overlays "/Users/example/Video Assets/Overlays" \
  --sfx "/Users/example/Video Assets/SFX" \
  --music "/Users/example/Video Assets/Music" \
  --transitions "/Users/example/Video Assets/Transitions" \
  --backgrounds "/Users/example/Video Assets/Backgrounds" \
  --profile thai-fast-reel \
  --width 1080 \
  --height 1920 \
  --fps 30 \
  --captions
```

Omit optional folders the user does not have. Do not create imaginary directories merely to satisfy the command.

## Reconfiguration

Re-run `video-editing-th configure` when the user asks to change defaults or when a saved directory has moved. Existing values appear as defaults, so pressing Enter preserves them. Use explicit flags for automation.

Do not repeat configuration questions during normal edits. Once the file exists, the normal invocation is simply:

```text
$video-editing-th <footage-folder>
```

Per-project instructions override only the specified defaults. For example, “no captions for this one” must not permanently change the saved configuration unless the user explicitly asks to reconfigure it.
