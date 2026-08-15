# One-Time Configuration

The repository defines the editing workflow. A small machine-local YAML file stores paths and preferences that differ between computers.

## Run the wizard once

```bash
video-editing-th configure
```

The wizard asks for optional folders containing:

- B-roll;
- overlays and graphics;
- sound effects;
- music;
- transitions;
- backgrounds.

It also confirms the default editing profile, output dimensions, frame rate, and Thai-caption preference. Press Enter to keep an existing value when rerunning the wizard. Leave an optional folder blank when that asset category is not available.

Every non-empty folder must already exist. Paths are resolved before they are saved.

## Where configuration is stored

Print the active location:

```bash
video-editing-th config path
```

Resolution order:

1. `VIDEO_EDITING_TH_CONFIG`;
2. `$XDG_CONFIG_HOME/video-editing-th/config.yaml`;
3. `~/.config/video-editing-th/config.yaml`.

The normal catalog and preview locations are also outside Git:

```text
~/.local/share/video-editing-th/assets.db
~/.cache/video-editing-th/asset-previews/
```

Inspect the resolved values:

```bash
video-editing-th config show
video-editing-th config show --json
```

Do not commit this file. It may contain personal absolute paths.

## Codex-assisted setup

Codex should run the interactive wizard on first use and ask only for values it cannot infer. When all values have already been supplied, Codex can configure the machine non-interactively:

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

Omit folders that do not exist. Codex must never invent a path.

## Index configured assets

After configuration, build or refresh the shared catalog:

```bash
video-editing-th assets index-configured
```

All configured role folders are scanned together. This matters because missing catalog entries are pruned only after the complete combined scan; indexing B-roll cannot accidentally remove indexed SFX from another configured root.

Search and annotation commands use the configured catalog automatically, so `--catalog` is normally unnecessary:

```bash
video-editing-th assets search "strength training chest" \
  --role broll \
  --orientation portrait
```

## Default recurring use

Once configured, invoke the installed skill with only the changing project input:

```text
$video-editing-th <footage-folder>
```

That means the full Thai fast-Reel workflow unless the user provides a per-project override. For example, “no captions for this one” changes only that project; it does not rewrite the saved configuration.

## Example YAML

```yaml
assets:
  broll: /Users/example/Video Assets/B-roll
  overlays: /Users/example/Video Assets/Overlays
  sfx: /Users/example/Video Assets/SFX
  catalog_path: /Users/example/.local/share/video-editing-th/assets.db
  preview_dir: /Users/example/.cache/video-editing-th/asset-previews
workflow:
  default_profile: thai-fast-reel
  editor_backend: chatcut
  use_broll: true
  use_overlays: true
  use_sfx: true
  use_music: true
  use_transitions: true
  use_motion: true
  captions_enabled: true
  caption_language: th
output:
  width: 1080
  height: 1920
  fps: 30.0
model_root: /Users/example/.cache/video-editing-th/models
ffmpeg_binary: ffmpeg
ffprobe_binary: ffprobe
auto_editor_binary: auto-editor
whisper_cpp_binary: whisper-cli
project_edit_dir_name: edit
```
