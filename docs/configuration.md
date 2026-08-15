# One-Time Configuration

The repository and installed skill define the editing workflow. A small machine-local YAML file stores only paths and reusable preferences that genuinely differ between computers.

## Run the wizard once

```bash
video-editing-th configure
```

The wizard asks for optional local folders containing:

- B-roll;
- overlays and graphics;
- backgrounds.

It also confirms the default editing profile. Press Enter to keep an existing value when rerunning the wizard. Leave an optional folder blank when that visual category is not available.

Every non-empty folder must already exist. Paths are resolved before they are saved.

ChatCut supplies sound effects, music, and transitions through its native libraries. The social-video default is fixed at 1080x1920 at 30 fps. Captions are decided in each project prompt. None of those are one-time machine questions.

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
  --backgrounds "/Users/example/Video Assets/Backgrounds" \
  --profile thai-fast-reel
```

Omit folders that do not exist. Codex must never invent a path.

## Index configured visual assets

After configuration, build or refresh the shared visual catalog:

```bash
video-editing-th assets index-configured
```

All configured visual folders are scanned together. Missing catalog entries are pruned only after the complete combined scan, so indexing B-roll cannot accidentally remove overlays or backgrounds from another configured root.

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

That means the full Thai fast-Reel workflow unless the user provides a per-project override. Captions are never inferred from the machine config:

```text
$video-editing-th /path/to/footage — add Thai captions
```

When the current prompt says nothing about captions, no captions are created.

## Legacy configuration migration

Earlier versions temporarily stored native audio folders, transition folders, output dimensions, and caption settings. Current releases ignore those deprecated fields when loading the file. Run the wizard again and save the configuration to rewrite it in the simplified form.

## Example YAML

```yaml
assets:
  broll: /Users/example/Video Assets/B-roll
  overlays: /Users/example/Video Assets/Overlays
  backgrounds: /Users/example/Video Assets/Backgrounds
  catalog_path: /Users/example/.local/share/video-editing-th/assets.db
  preview_dir: /Users/example/.cache/video-editing-th/asset-previews
workflow:
  default_profile: thai-fast-reel
  editor_backend: chatcut
  use_broll: true
  use_overlays: true
  use_motion: true
model_root: /Users/example/.cache/video-editing-th/models
ffmpeg_binary: ffmpeg
ffprobe_binary: ffprobe
auto_editor_binary: auto-editor
whisper_cpp_binary: whisper-cli
project_edit_dir_name: edit
```
