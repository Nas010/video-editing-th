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

On macOS:

```bash
scripts/setup_macos.sh
```

On Debian/Ubuntu:

```bash
scripts/setup_debian.sh
```

By default, neither script runs the operating-system package manager. Use `--install-system` to authorize the documented FFmpeg installation step. Use `--with-optional` for `faster-whisper`, PySceneDetect, and OpenTimelineIO.

The scripts prefer `uv`; without it they create `.venv` and install the repository in editable mode.

## Transcription models

Model weights are intentionally excluded from Git. Install a current `whisper-cli` build from the official `ggml-org/whisper.cpp` project and download a multilingual model such as `large-v3`, or install the optional Python backend:

```bash
python -m pip install -e '.[transcription]'
```

Pass the local GGML file explicitly:

```bash
video-editing-th transcribe clip.mov \
  --backend whisper.cpp \
  --model /local/model/cache/ggml-large-v3.bin \
  --language th
```

Run `video-editing-th doctor` after installing external tools. The doctor is read-only and does not download or install anything.

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
