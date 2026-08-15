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

`--with-whisper` builds the pinned whisper.cpp release and downloads a hardware-recommended multilingual model outside Git. On an 8 GB M1 Mac the normal default is `large-v3-turbo-q5_0`; `large-v3-q5_0` is the accuracy-oriented alternative. See [Local Thai ASR Models](asr-models.md) for the rationale and full M1/8GB guidance.

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

## Application configuration

A local YAML file may override executable names and paths:

```yaml
asset_root: /local/path/to/assets
model_root: /local/path/to/models
ffmpeg_binary: ffmpeg
ffprobe_binary: ffprobe
auto_editor_binary: auto-editor
whisper_cpp_binary: whisper-cli
project_edit_dir_name: edit
```

Do not commit personal absolute paths. Keep local configuration outside the repository or in an ignored file.

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
