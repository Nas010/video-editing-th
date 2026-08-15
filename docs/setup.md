# Setup

## Supported baseline

- macOS on Apple Silicon or Intel, or Debian/Ubuntu Linux;
- Python 3.11–3.13;
- Git;
- FFmpeg and FFprobe;
- one transcription backend: `whisper-cli` or the `faster-whisper` Python extra;
- Codex with the ChatCut MCP integration and browser access for final NLE execution.

## Clone and install

```bash
git clone https://github.com/Nas010/video-editing-th.git
cd video-editing-th
```

### macOS: recommended local-ASR setup

```bash
scripts/setup_macos.sh --install-system --with-whisper
```

`--with-whisper` builds the pinned whisper.cpp release and downloads a hardware-recommended multilingual model outside Git. On an 8 GB M1 Mac the normal default is `large-v3-turbo-q5_0`; `large-v3-q5_0` is the accuracy-oriented alternative. See [Local Thai ASR Models](asr-models.md).

If FFmpeg/CMake are already installed and you do not want the script to use Homebrew, omit `--install-system`.

Optional Python adapters can be added at the same time:

```bash
scripts/setup_macos.sh --install-system --with-whisper --with-optional
```

### Debian or Ubuntu

```bash
scripts/setup_debian.sh
```

By default, setup scripts do not run the operating-system package manager unless you explicitly use the documented `--install-system` option. `--with-optional` installs `faster-whisper`, PySceneDetect, and OpenTimelineIO.

The scripts prefer `uv`; without it they create `.venv` and install the repository in editable mode.

## One-time Codex configuration

After installation, run the interactive wizard once:

```bash
video-editing-th configure
```

It asks for the optional B-roll, overlay/graphics, sound-effects, music, transition, and background folders, plus default output/profile/caption settings. Personal paths are saved outside the repository.

Verify the result:

```bash
video-editing-th config path
video-editing-th config show --json
```

When at least one creative folder is configured, build the shared catalog:

```bash
video-editing-th assets index-configured
```

See [One-Time Configuration](configuration.md) for the full wizard, non-interactive Codex setup, path resolution, and reconfiguration rules.

Once configured, the normal Codex request is:

```text
$video-editing-th <footage-folder>
```

The installed skill supplies the complete Thai fast-Reel brief. The user only needs to state per-project overrides.

## What the ASR model does

The Whisper model is used only for **speech recognition**. It turns Thai speech into text plus timing/confidence evidence. Codex combines that evidence with the waveform to decide cuts and retakes, and the corrected transcript can feed captions. Whisper does not perform the actual video edit and does not choose B-roll, zooms, overlays, or sound effects.

```text
raw talking-head video
  -> extracted audio
  -> Thai ASR
  -> transcript + timestamps + quality gate
  -> Codex edit decisions
  -> ChatCut timeline
```

## Model recommendation and cache

Inspect the current machine:

```bash
video-editing-th models recommend
video-editing-th models list
```

Model weights are intentionally excluded from Git and normally live in:

```text
~/.cache/video-editing-th/models
```

The full unquantized `large-v3` model is usable on Apple Silicon, but on an 8 GB M1 Air the project deliberately prefers a quantized model so macOS, Codex, the browser, ChatCut, and FFmpeg retain memory headroom. See [Local Thai ASR Models](asr-models.md).

## Install whisper.cpp separately on macOS

If the Python/project setup already exists:

```bash
bash scripts/setup_whisper_cpp_macos.sh --model auto --install-system
```

The helper pins whisper.cpp `v1.9.2` by default, builds `whisper-cli`, links it under `~/.local/bin`, and downloads the selected model. External model weights are never committed to this repository.

## Transcription

When the hardware-recommended model exists in the configured cache, the CLI can discover it automatically:

```bash
video-editing-th transcribe clip.mov \
  --backend whisper.cpp \
  --language th
```

Or pass any supported local GGML model explicitly:

```bash
video-editing-th transcribe clip.mov \
  --backend whisper.cpp \
  --model ~/.cache/video-editing-th/models/ggml-large-v3-q5_0.bin \
  --language th
```

The pipeline extracts 16-bit, 16 kHz mono WAV audio automatically before invoking whisper.cpp.

For the optional Python backend:

```bash
python -m pip install -e '.[transcription]'
```

Run `video-editing-th doctor` after installing external tools. The doctor is read-only and reports OS/architecture, RAM, the recommended ASR model, available transcription backends, and cached GGML models.

## Application configuration overrides

The one-time wizard writes the application YAML. Advanced users may edit it or point to a different file with `VIDEO_EDITING_TH_CONFIG` or `--config`. The schema includes:

```yaml
assets:
  broll: /local/path/to/broll
  overlays: /local/path/to/overlays
  sfx: /local/path/to/sfx
  catalog_path: /local/path/to/assets.db
  preview_dir: /local/path/to/previews
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
model_root: /local/path/to/models
ffmpeg_binary: ffmpeg
ffprobe_binary: ffprobe
auto_editor_binary: auto-editor
whisper_cpp_binary: whisper-cli
project_edit_dir_name: edit
```

Do not commit personal absolute paths. Keep local configuration outside the repository.

## Install the Codex skill

```bash
video-editing-th skill install
```

This creates directory symlinks in `${CODEX_HOME:-~/.codex}/skills/video-editing-th` and `~/.agents/skills/video-editing-th`. It refuses to replace a real directory.

For a source checkout, this equivalent script is available:

```bash
scripts/install_codex_skill.sh
```

## ChatCut

Connect/install the ChatCut MCP integration in the Codex environment. The repository does not store ChatCut credentials or automate account setup. Verify that Codex can create/read a project, import a small test file, and inspect the timeline before processing real footage.
